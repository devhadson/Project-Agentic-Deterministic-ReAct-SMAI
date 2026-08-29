import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Cargar variables de entorno desde el archivo .env
load_dotenv()

#engine = create_engine(os.getenv("DATABASE_URL"))

# Inicialización segura del engine
db_url = os.getenv("DATABASE_URL")
if not db_url:
    logging.error("DATABASE_URL no está definida en las variables de entorno.")

try:
    engine = create_engine(db_url) if db_url else None
except Exception as e:
    logging.error(f"Error al crear el engine de la base de datos: {str(e)}")
    engine = None

# Crear servidor MCP
mcp = FastMCP("HistoriaClinicaServer")

@mcp.tool()
def verificar_existencia_hc(hc_id: str) -> bool:
    """Verifica si existen registros o PDFs asociados a un ID de Historia Clínica."""
    if not engine:
        logging.error("No se pudo ejecutar la consulta: Engine de BD no inicializado.")
        return False

    query = text("""
        SELECT COUNT(*) 
        FROM index_rag_pdf 
        WHERE nombre_pdf LIKE :pattern OR hc_id = :hc
    """)
    
    try:
        with engine.connect() as conn:
            count = conn.execute(query, {
                "pattern": f"%{hc_id}%",
                "hc": hc_id.strip()
            }).scalar()
        
        return (count or 0) > 0

    except SQLAlchemyError as e:
        logging.error(f"Error de base de datos en verificar_existencia_hc ({hc_id}): {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error inesperado en verificar_existencia_hc ({hc_id}): {str(e)}")
        return False

@mcp.tool()
def obtener_registros_hc(hc_id: str) -> list[dict]:
    """Obtiene la lista de indices RAG asociados a una Historia Clínica."""
    if not engine:
        logging.error("No se pudo ejecutar la consulta: Engine de BD no inicializado.")
        return []

    query = text("""
        SELECT idex_rag, hc_id 
        FROM index_rag_pdf 
        WHERE hc_id = :hc OR nombre_pdf LIKE :pattern
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {
                "hc": hc_id.strip(),
                "pattern": f"%{hc_id}%"
            }).fetchall()
            
        return [{"idex_rag": row[0], "hc_id": row[1]} for row in result]

    except SQLAlchemyError as e:
        logging.error(f"Error de base de datos en obtener_registros_hc ({hc_id}): {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Error inesperado en obtener_registros_hc ({hc_id}): {str(e)}")
        return []

if __name__ == "__main__":
    mcp.run()