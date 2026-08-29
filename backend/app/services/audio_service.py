# backend/app/services/audio_service.py
import os
import tempfile
from openai import OpenAI
from app.core.config import settings

if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]
    
class AudioService:
    def __init__(self):
        # Instanciar el cliente cliente de OpenAI con la API Key configurada
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def transcribe_audio_file(self, file_bytes: bytes, filename: str) -> str:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno (.env).")

        suffix = os.path.splitext(filename)[1] or ".wav"
        
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            with open(temp_path, "rb") as audio_file:
                # Sintaxis para openai >= 1.0.0
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            return transcript.text
        finally:
            # Garantizar la eliminación del archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)