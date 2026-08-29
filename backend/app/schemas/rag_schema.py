from pydantic import BaseModel, Field

class UploadHCResponse(BaseModel):
    index_id: str
    filename: str
    hc_id: str
    message: str
    
class ValidateHCResponse(BaseModel):
    hc_id: str
    exists: bool
    count: int
    message: str

class QueryHCRequest(BaseModel):
    hc_id: str = Field(..., description="ID de la Historia Clínica a consultar (ej. HC-52384)")
    pregunta: str = Field(..., description="Pregunta del usuario sobre el historial")
    model: str = Field(default="gpt-4o-mini", description="Modelo de lenguaje a utilizar")
    temperature: float = Field(default=0.0, description="Temperatura de generación")

class QueryHCResponse(BaseModel):
    hc_id: str
    pregunta: str
    respuesta: str
    contexto_utilizado: bool