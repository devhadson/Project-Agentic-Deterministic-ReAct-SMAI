from twilio.rest import Client
from app.core.config import settings
from app.schemas.notification_schema import CallRequest, SMSRequest

class TwilioService:
    def __init__(self):
        self.client = (
            Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN
            else None
        )
        self.from_phone = settings.TWILIO_PHONE_NUMBER

    def make_emergency_call(self, data: CallRequest) -> dict:
        if not self.client:
            raise RuntimeError("Cliente de Twilio no configurado.")

        twiml_instruction = (
            f"<Response><Say language='es-MX' voice='Polly.Lupe'>"
            f"Alerta de emergencia médica. El paciente {data.patient_name} "
            f"con DNI {data.patient_dni} presenta una alerta crítica de {data.message_type}. "
            f"Por favor atienda el caso de inmediato."
            f"</Say></Response>"
        )

        call = self.client.calls.create(
            twiml=twiml_instruction,
            to=data.to_phone,
            from_=self.from_phone
        )
        return {"call_sid": call.sid, "status": call.status}

    def send_sms(self, data: SMSRequest) -> dict:
        if not self.client:
            raise RuntimeError("Cliente de Twilio no configurado.")

        message = self.client.messages.create(
            body=data.message,
            from_=self.from_phone,
            to=data.to_phone
        )
        return {"sms_sid": message.sid, "status": message.status}