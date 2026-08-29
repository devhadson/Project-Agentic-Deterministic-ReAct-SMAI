from pydantic import BaseModel
from typing import Optional, List

class GlucosaResponse(BaseModel):
    glucose_level: float
    doctor_id: Optional[int] = None

class TriajeEmergenciaRequest(BaseModel):
    sintomas: str
    #exercise_frequency: str
    #recent_intake: str
    patient_id: str
    patient_name: str
    glucose_value: float
    doctor_id: int

class SolicitudLabRequest(BaseModel):
    reason: str
    patient_id: str
    patient_name: str
    glucose_value: float

class AgendarCitaRequest(BaseModel):
    patient_id: str
    patient_name: str
    appointment_date: str
    appointment_time: str
    doctor_id: int
    details: str
    glucose_value: float

class AlertaGlucosaRequest(BaseModel):
    patient_id: str
    glucose_value: float
    sintomas: str
    twilio_call_sid: str
    doctor_id: int
    destino_llamada: str = "Médico Tratante"

class RAGSearchRequest(BaseModel):
    query: str
    hc_filter: Optional[str] = None

class MedicoSchema(BaseModel):
    nombre: str
    especialidad: str