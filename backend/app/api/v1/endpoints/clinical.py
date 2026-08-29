from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.clinical_schema import HistoriaClinicaResponse, CargaHistoriaResponse, DashboardMetricsResponse
from app.services.clinical_service import ClinicalService

router = APIRouter()

@router.get("/historia-clinica/{dni}", response_model=List[HistoriaClinicaResponse])
def get_historia(dni: str, db: Session = Depends(get_db)):
    return ClinicalService.fetch_historia_clinica(db, dni)

@router.post(
        "/cargar-historia", 
        response_model=CargaHistoriaResponse)
async def upload_historia(
    dni_paciente: str = Form(...),
    observaciones: str = Form(""),
    file: UploadFile = File(...)
):
    if not file:
        raise HTTPException(status_code=400, detail="Debe adjuntar un archivo válido.")
    
    # Lógica de guardado o procesamiento RAG del documento
    return {
        "status": "success",
        "mensaje": "Archivo guardado correctamente en la historia clínica del paciente.",
        "paciente_dni": dni_paciente,
        "filename": file.filename
    }

@router.get(
    "/dashboard-metrics", 
    response_model=DashboardMetricsResponse, 
    status_code=status.HTTP_200_OK,
    summary="Obtener métricas y listado detallado para el Dashboard Analítico"
)
def get_dashboard_metrics(
    rol: str = Query(..., description="Rol del usuario (paciente, enfermería, médico, administrador)"),
    username: str = Query(..., description="Nombre de usuario o DNI del usuario autenticado"),
    patient_id: Optional[str] = Query(None, description="Filtrar por DNI Paciente específico"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    try:
        return ClinicalService.get_dashboard_metrics(
            db=db,
            rol=rol,
            username=username,
            patient_id=patient_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener métricas clínicas: {str(e)}"
        )