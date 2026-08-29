import os
import re
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import HTTPException, status
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.rag_schema import UploadHCResponse, ValidateHCResponse, QueryHCRequest, QueryHCResponse
from dotenv import load_dotenv

if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

load_dotenv()

# 1. Definir la ruta base absoluta
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FAISS_PATH = BASE_DIR / "vectorstore" / "db_faiss"
TEMP_UPLOADS_DIR = BASE_DIR / "uploads_temp"

class RAGService:
    ## 1. Validación de existencia de la historia clínica en la base de datos indexada
    @staticmethod
    def extract_hc_id(filename: str) -> str:
        """Extrae el identificador HC-XXXXX del nombre del archivo."""
        match = re.search(r'HC-\d+', filename, re.IGNORECASE)
        return match.group(0).upper() if match else "HC-UNKNOWN"

    ## 2. Procesamiento e ingestión del documento en el sistema RAG
    @classmethod
    def process_and_ingest_document(cls, db: Session, file: UploadFile) -> UploadHCResponse:
        filename = file.filename
        hc_id = cls.extract_hc_id(filename)
        index_id = str(uuid.uuid4())
        
        # 2. VALIDACIÓN Y CREACIÓN DEL DIRECTORIO
        # parents=True: Crea directorios padre si no existen
        # exist_ok=True: Si el directorio ya existe, no lanza excepción
        TEMP_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        DB_FAISS_PATH.mkdir(parents=True, exist_ok=True)

        # 3. Construir la ruta absoluta completa para el archivo
        temp_file_path = (TEMP_UPLOADS_DIR / f"{index_id}_{filename}").resolve()
        temp_file_str = str(temp_file_path)

        try:
            # 4. Guardar archivo temporalmente
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Validar existencia física del archivo antes de entregarlo a LangChain
            if not temp_file_path.exists():
                raise FileNotFoundError(f"Error al escribir el archivo temporal en: {temp_file_str}")

            # 5. Cargar documento con LangChain pasando la ruta absoluta
            if filename.lower().endswith('.pdf'):
                loader = PyPDFLoader(temp_file_str)
            elif filename.lower().endswith('.txt'):
                loader = TextLoader(temp_file_str, encoding='utf-8')
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de archivo no soportado. Debe ser PDF o TXT."
                )

            documents = loader.load()
            if not documents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo está vacío o no contiene texto extraíble."
                )

            # 6. Fragmentación e inyección de metadatos clínicos
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            texts = text_splitter.split_documents(documents)

            for doc in texts:
                doc.metadata["hc_id"] = hc_id
                doc.metadata["filename"] = filename
                doc.metadata["index_id"] = index_id

            # 7. Indexación e integración en FAISS
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(texts, embeddings)
            
            document_faiss_path = str((DB_FAISS_PATH / index_id).resolve())
            vectorstore.save_local(document_faiss_path)

            global_faiss_path = str((DB_FAISS_PATH / "global_index").resolve())
            if os.path.exists(global_faiss_path):
                global_store = FAISS.load_local(
                    global_faiss_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                global_store.merge_from(vectorstore)
                global_store.save_local(global_faiss_path)
            else:
                vectorstore.save_local(global_faiss_path)

            # 8. Guardar registro en BD PostgreSQL
            query = text("""
                INSERT INTO index_rag_pdf (idex_rag, nombre_pdf, hc_id) 
                VALUES (:id, :nom, :hc)
            """)
            db.execute(query, {"id": index_id, "nom": filename, "hc": hc_id})
            db.commit()

            return UploadHCResponse(
                index_id=index_id,
                filename=filename,
                hc_id=hc_id,
                message=f"Historia clínica {hc_id} procesada e indexada con éxito."
            )

        except HTTPException as he:
            db.rollback()
            raise he
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error durante el proceso de ingestión RAG: {str(e)}"
            )
        finally:
            # 9. Limpieza del archivo temporal
            if temp_file_path.exists():
                temp_file_path.unlink()

    # Leectura de la historia clínica desde la base de datos indexada                
    @staticmethod
    def validate_hc(db: Session, hc_id: str) -> ValidateHCResponse:
        """Verifica si un ID de Historia Clínica existe en la base de datos indexada."""
        hc_clean = hc_id.strip()
        
        # Búsqueda flexible por nombre o coincidencia de ID
        query = text(
            "SELECT COUNT(*) FROM index_rag_pdf WHERE nombre_pdf LIKE :pattern OR hc_id = :hc"
        )
        count = db.execute(query, {"pattern": f"%{hc_clean}%", "hc": hc_clean}).scalar() or 0
        
        exists = count > 0
        message = (
            f"✅ Historia Clínica {hc_clean} encontrada y lista para consultar."
            if exists
            else f"❌ La Historia Clínica '{hc_clean}' no se encuentra cargada o indexada."
        )
        
        return ValidateHCResponse(
            hc_id=hc_clean,
            exists=exists,
            count=count,
            message=message
        )

    @staticmethod
    def query_hc_rag(db: Session, req: QueryHCRequest) -> QueryHCResponse:
        """Procesa una consulta RAG sobre el vectorstore asociado a una Historia Clínica."""
        hc_clean = req.hc_id.strip()
        
        # 1. Obtener los índices RAG asociados a la Historia Clínica
        sql = text("SELECT idex_rag, hc_id FROM index_rag_pdf WHERE hc_id = :hc OR nombre_pdf LIKE :pattern")
        registros = db.execute(sql, {"hc": hc_clean, "pattern": f"%{hc_clean}%"}).fetchall()

        if not registros:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron registros indexados para la Historia Clínica '{hc_clean}'"
            )

        # 2. Recuperar contexto desde los almacenes vectoriales (FAISS)
        resultados_contexto = ""
        embeddings = OpenAIEmbeddings()

        for reg in registros:
            index_id, hc_id_reg = reg[0], reg[1]
            path_faiss = f"vectorstore/db_faiss/{index_id}"

            if os.path.exists(path_faiss):
                try:
                    vector_store = FAISS.load_local(
                        path_faiss,
                        embeddings,
                        allow_dangerous_deserialization=True
                    )
                    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                    docs = retriever.invoke(req.pregunta)

                    for d in docs:
                        resultados_contexto += f"\n--- [Fuente: {hc_id_reg or hc_clean}] ---\n{d.page_content}"
                except Exception as e:
                    print(f"Error cargando vectorstore {path_faiss}: {str(e)}")

        if not resultados_contexto:
            return QueryHCResponse(
                hc_id=hc_clean,
                pregunta=req.pregunta,
                respuesta="No se encontró información relevante en los documentos indexados de esta Historia Clínica.",
                contexto_utilizado=False
            )

        # 3. Generar respuesta estructurada usando LangChain LLM
        try:
            llm = ChatOpenAI(
                model=req.model,
                temperature=req.temperature
            )

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", (
                    "Eres un asistente virtual experto encargado de responder preguntas basándote "
                    "únicamente en el contexto proporcionado. Si no sabes la respuesta o no está "
                    "en los documentos, di explícitamente que no posees esa información.\n\n"
                    "CONTEXTO DE LOS DOCUMENTOS LOCALES:\n{context}"
                )),
                ("human", "{input}"),
            ])

            chain = prompt_template | llm
            respuesta_obj = chain.invoke({"context": resultados_contexto, "input": req.pregunta})
            respuesta_final = respuesta_obj.content

            return QueryHCResponse(
                hc_id=hc_clean,
                pregunta=req.pregunta,
                respuesta=respuesta_final,
                contexto_utilizado=True
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar el modelo de lenguaje: {str(e)}"
            )