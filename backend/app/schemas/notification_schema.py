from pydantic import BaseModel, Field

class CallRequest(BaseModel):
    to_phone: str = Field(..., example="+51999999999")
    patient_name: str = Field(..., example="Juan Pérez")
    patient_dni: str = Field(..., example="12345678")
    message_type: str = Field(default="EMERGENCIA_HIPOGLUCEMIA")

class CallResponse(BaseModel):
    call_sid: str
    status: str

class SMSRequest(BaseModel):
    to_phone: str = Field(..., example="+51999999999")
    message: str = Field(..., example="Alerta médica para su cita.")

class SMSResponse(BaseModel):
    sms_sid: str
    status: str