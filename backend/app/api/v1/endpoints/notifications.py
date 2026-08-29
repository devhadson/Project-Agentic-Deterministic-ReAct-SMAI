from fastapi import APIRouter, HTTPException, status
from app.schemas.notification_schema import CallRequest, CallResponse, SMSRequest, SMSResponse
from app.services.twilio_service import TwilioService

router = APIRouter()
twilio_service = TwilioService()

@router.post("/make-call", response_model=CallResponse, status_code=status.HTTP_200_OK)
def make_call(data: CallRequest):
    try:
        res = twilio_service.make_emergency_call(data)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error realizando llamada Twilio: {str(e)}"
        )

@router.post("/send-sms", response_model=SMSResponse, status_code=status.HTTP_200_OK)
def send_sms(data: SMSRequest):
    try:
        res = twilio_service.send_sms(data)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando SMS Twilio: {str(e)}"
        )