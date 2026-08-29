from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DBService
from app.services.rag_service import RAGService
from app.schemas.agent_schema import (
    GlucosaResponse, TriajeEmergenciaRequest, SolicitudLabRequest,
    AgendarCitaRequest, AlertaGlucosaRequest, RAGSearchRequest,
    MedicoSchema
)

router = APIRouter()

@router.get("/glucosa/{patient_id}", response_model=GlucosaResponse)
def get_glucosa(patient_id: str, db: Session = Depends(get_db)):
    return DBService.get_ultimo_nivel_glucosa(db, patient_id)

@router.get("/medico/telefono/{doctor_id}")
def get_telefono_medico(doctor_id: int, db: Session = Depends(get_db)):
    phone = DBService.obtener_telefono_medico(db, doctor_id)
    return {"mobile_phone": phone}

@router.get("/medicos/disponibles/", response_model=list[MedicoSchema])
def get_medicos_disponibles(db: Session = Depends(get_db)):
    contexto = DBService.get_medicos_disponibles(db)
    return contexto

@router.post("/triaje/emergencia")
def post_triaje_emergencia(req: TriajeEmergenciaRequest, db: Session = Depends(get_db)):
    msg = DBService.registrar_triaje_emergencia(db, req)
    return {"message": msg}

@router.post("/solicitud/laboratorio")
def post_solicitud_lab(req: SolicitudLabRequest, db: Session = Depends(get_db)):
    msg = DBService.registrar_solicitud_urgente_lab(db, req)
    return {"message": msg}

@router.post("/citas/agendar")
def post_agendar_cita(req: AgendarCitaRequest, db: Session = Depends(get_db)):
    msg = DBService.agendar_cita_rutinario(db, req)
    return {"message": msg}

@router.post("/alertas/glucosa")
def post_alerta_glucosa(req: AlertaGlucosaRequest, db: Session = Depends(get_db)):
    msg = DBService.registrar_alerta_glucosa(db, req)
    return {"message": msg}

@router.post("/rag/buscar")
def post_rag_buscar(req: RAGSearchRequest, db: Session = Depends(get_db)):
    contexto = RAGService.buscar_contexto(db, req.query, req.hc_filter)
    return {"context": contexto}
