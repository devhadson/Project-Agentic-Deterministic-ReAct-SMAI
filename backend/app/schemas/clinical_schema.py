from pydantic import BaseModel
from typing import Optional, List, Optional, Dict
from datetime import datetime

class HistoriaClinicaResponse(BaseModel):
    fecha_registro: datetime
    glucosa: Optional[float]
    categoria: Optional[str]
    detalle_reserva: Optional[str]

    class Config:
        from_attributes = True

class CargaHistoriaResponse(BaseModel):
    status: str
    mensaje: str
    paciente_dni: str
    filename: str

class AppointmentDetail(BaseModel):
    DNI: str
    NOMBRE_DEL_PACIENTE: str
    GLUCOSA: str
    CATEGORIA: str
    DETALLE_DE_LA_RESERVA: Optional[str] = ""

class DashboardMetricsResponse(BaseModel):
    stats: Dict[str, int]
    total: int
    emergencias: int
    citas: int
    urgencias: int
    detalle: List[AppointmentDetail]