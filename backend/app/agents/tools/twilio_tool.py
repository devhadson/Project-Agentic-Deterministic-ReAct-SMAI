# backend/app/agents/tools/twilio_tool.py
from langchain.tools import tool
from app.services.twilio_service import TwilioService
from app.schemas.notification_schema import CallRequest

twilio_service = TwilioService()

@tool
def ejecutar_llamada_emergencia_tool(to_phone: str, nombre_paciente: str, dni_paciente: str) -> str:
    """Útil para realizar una llamada telefónica de emergencia automatizada vía Twilio cuando el paciente presenta hipoglucemia o emergencia médica."""
    try:
        req = CallRequest(
            to_phone=to_phone,
            patient_name=nombre_paciente,
            patient_dni=dni_paciente,
            message_type="EMERGENCIA_CRITICA"
        )
        res = twilio_service.make_emergency_call(req)
        return f"Llamada iniciada con éxito. SID: {res.get('call_sid')}"
    except Exception as e:
        return f"Error ejecutando llamada: {str(e)}"