import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, text
from app.core.database import Base

from app.schemas.agent_schema import (
    TriajeEmergenciaRequest, SolicitudLabRequest, 
    AgendarCitaRequest, AlertaGlucosaRequest
)

logger = logging.getLogger(__name__)

class DBService:
    @staticmethod
    def get_ultimo_nivel_glucosa(db: Session, patient_id: str):
        query = text("""
            SELECT glucose_level, doctor_id FROM dataset_paciente 
            WHERE patient_id = :pid
            ORDER BY ultima_actualizacion DESC LIMIT 1
        """)
        result = db.execute(query, {"pid": patient_id}).fetchone()
        if result:
            return {"glucose_level": float(result[0]), "doctor_id": int(result[1]) if result[1] else None}
        return {"glucose_level": 0.0, "doctor_id": None}

    @staticmethod
    def obtener_telefono_medico(db: Session, id_medico: int) -> str:
        try:
            query = text("SELECT mobile_phone FROM medico WHERE id = :doctor_id")
            resultado = db.execute(query, {"doctor_id": id_medico}).fetchone()
            if resultado and resultado[0]:
                return str(resultado[0]).strip()
            return "+51934111744"
        except Exception:
            return "+51934111744"

    @staticmethod
    def get_medicos_disponibles(db: Session):
        """
        Obtiene la lista de médicos disponibles con staff_type = 'MED' 
        para ser utilizados como contexto en el agente LLM de triaje.
        """        
        query = text("SELECT nombre, especialidad FROM medico WHERE staff_type = 'MED'")
        result = db.execute(query).fetchall()
        
        medicos = [
            {"nombre": row[0], "especialidad": row[1]} 
            for row in result
        ]
        return medicos
    
    @staticmethod
    def registrar_triaje_emergencia(db: Session, req: TriajeEmergenciaRequest) -> str:
        """
        Registra una cita médica de categoría EMERGENCIA en la base de datos.
        Maneja excepciones y reversión de transacciones en caso de falla.
        """        
        insert_query = text("""
            INSERT INTO citas (patient_id, categoria, detalle_reserva, glucosa, paciente, fecha_cita, hora_cita, doctor_id)
            VALUES (:pid, 'EMERGENCIA', :detalle, :glucosa, :pac, CURRENT_DATE, CURRENT_TIME, :doctor_id)
        """)
        #detalle = f"Síntomas: {req.symptoms}. Ejercicio: {req.exercise_frequency}. Consumo: {req.recent_intake}"
        detalle = f"Síntomas: {req.sintomas}"

        try:
            db.execute(insert_query, {
                "pid": req.patient_id,
                "pac": req.patient_name, 
                "detalle": detalle,
                "glucosa": req.glucose_value,
                "doctor_id": req.doctor_id
            })
            db.commit()
            return f"ALERTA MÉDICA REGISTRADA: Se ha notificado al equipo de emergencias. Detalles: {detalle}"
        except Exception as e:
            db.rollback()
            logger.error(f"Error al registrar triaje de emergencia para paciente {req.patient_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar la cita de emergencia en base de datos: {str(e)}"
            )

    @staticmethod
    def registrar_solicitud_urgente_lab(db: Session, req: SolicitudLabRequest) -> str:
        insert = text("""
            INSERT INTO citas (patient_id, categoria, detalle_reserva, glucosa, paciente, fecha_cita, hora_cita, doctor_id)
            VALUES (:pid, 'URGENCIAS', :detalle, :glucosa, :pac, CURRENT_DATE, CURRENT_TIME, 0)
        """)
        db.execute(insert, {
            "pid": req.patient_id, "pac": req.patient_name,
            "detalle": f"{req.reason} | Valor glucosa: {req.glucose_value} mg/dL",
            "glucosa": req.glucose_value
        })
        db.commit()
        return f"Orden de laboratorio generada para el paciente {req.patient_id}. Motivo: {req.reason}."

    @staticmethod
    def agendar_cita_rutinario(db: Session, req: AgendarCitaRequest) -> str:
        query = text("""
            INSERT INTO citas (patient_id, paciente, fecha_cita, hora_cita, doctor_id, categoria, detalle_reserva, glucosa)
            VALUES (:pid, :nom, :fec, :hor, :med, 'AGENDAR CITA', :det, :glu)
        """)
        db.execute(query, {
            "pid": req.patient_id, "nom": req.patient_name, "fec": req.appointment_date,
            "hor": req.appointment_time, "med": req.doctor_id, "det": req.details, "glu": req.glucose_value
        })
        db.commit()
        return f"✅ Cita confirmada exitosamente para el {req.appointment_date} a las {req.appointment_time}."

    @staticmethod
    def registrar_alerta_glucosa(db: Session, req: AlertaGlucosaRequest) -> str:
        query = text("""
            INSERT INTO alertas_glucosa (
                fecha_hora, nivel_glucosa, sintomas, llamada_activada, 
                destino_llamada, twilio_call_sid, patient_id, doctor_id
            ) VALUES (CURRENT_TIMESTAMP, :glucosa, :sintomas, :llamada, :destino, :call_sid, :pid, :doctor_id)
        """)
        db.execute(query, {
            "glucosa": int(req.glucose_value), "sintomas": req.sintomas, "llamada": True,
            "destino": req.destino_llamada, "call_sid": req.twilio_call_sid,
            "pid": req.patient_id, "doctor_id": req.doctor_id
        })
        db.commit()
        return "Alerta de glucosa registrada exitosamente en el sistema."

class UsuarioBD(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=True)
    auth_provider = Column(String(20), default="local")
    rol_nombre = Column(String(30), default="paciente")
    # fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

def get_user_by_username(db: Session, username: str):
    return db.query(UsuarioBD).filter(UsuarioBD.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(UsuarioBD).filter(UsuarioBD.email == email).first()

def create_google_user(db: Session, username: str, email: str, display_name: str):
    user = UsuarioBD(
        username=username,
        email=email,
        display_name=display_name,
        password_hash=None,
        auth_provider="google",
        rol_nombre="paciente"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user