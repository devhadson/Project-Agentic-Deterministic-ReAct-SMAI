from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.rag_schema import (
    UploadHCResponse,
    ValidateHCResponse,
    QueryHCRequest,
    QueryHCResponse
)
from app.services.rag_service import RAGService

router = APIRouter()

@router.post(
    "/upload-hc",
    response_model=UploadHCResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cargar y vectorizar una Historia Clínica"
)
def upload_historias_clinicas(
    file: UploadFile = File(..., description="Archivo PDF o TXT de la Historia Clínica"),
    db: Session = Depends(get_db)
):
    """Procesa un archivo PDF/TXT, genera los vectores con OpenAI/FAISS y guarda los registros en BD."""
    return RAGService.process_and_ingest_document(db=db, file=file)

@router.get(
    "/validate-hc",
    response_model=ValidateHCResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar existencia de una Historia Clínica"
)
def validate_hc(
    hc_id: str = Query(..., description="ID de Historia Clínica a validar (ej. HC-52384)"),
    db: Session = Depends(get_db)
):
    """Verifica si la Historia Clínica ingresada está cargada e indexada en la BD."""
    try:
        return RAGService.validate_hc(db=db, hc_id=hc_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al validar Historia Clínica: {str(e)}"
        )

@router.post(
    "/query-hc",
    response_model=QueryHCResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta RAG a la Historia Clínica"
)
def query_hc(
    req: QueryHCRequest,
    db: Session = Depends(get_db)
):
    """Efectúa una búsqueda vectorial y consulta generativa mediante RAG sobre los PDF de la Historia Clínica."""
    try:
        return RAGService.query_hc_rag(db=db, req=req)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando la consulta RAG: {str(e)}"
        )