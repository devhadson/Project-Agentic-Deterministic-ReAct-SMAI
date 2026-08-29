# backend/app/api/v1/endpoints/audio.py
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.audio_schema import TranscriptionResponse
from app.services.audio_service import AudioService

logger = logging.getLogger(__name__)
router = APIRouter()
audio_service = AudioService()

@router.post("/transcribe", response_model=TranscriptionResponse, status_code=status.HTTP_200_OK)
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="El archivo de audio subido está vacío."
            )

        text = await audio_service.transcribe_audio_file(file_bytes, file.filename)
        return {"text": text}

    except Exception as e:
        # Imprime la traza de error real en la terminal del backend
        logger.error(f"Error procesando transcripción de audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en transcripción: {str(e)}"
        )