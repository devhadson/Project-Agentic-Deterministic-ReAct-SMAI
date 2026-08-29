import os
import requests
import logging
import streamlit as st
from typing import Optional, Dict, Any, Tuple, List

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

logger = logging.getLogger(__name__)

class APIClient:
    @staticmethod
    def login_local(username, password):
        response = requests.post(f"{API_BASE_URL}/auth/login", json={"username": username, "password": password})
        return response

    @staticmethod
    def get_google_url():
        response = requests.get(f"{API_BASE_URL}/auth/google/url")
        return response.json().get("url") if response.status_code == 200 else None

    @staticmethod
    def process_google_callback(code):
        response = requests.post(f"{API_BASE_URL}/auth/google/callback", json={"code": code})
        return response

    @staticmethod
    def get_historia_clinica(dni):
        response = requests.get(f"{API_BASE_URL}/clinical/historia-clinica/{dni}")
        return response
    
    @staticmethod
    def get_dashboard_metrics(
        rol: str,
        username: str,
        patient_id: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Invoca la API de métricas del Dashboard analítico."""
        params = {
            "rol": rol,
            "username": username
        }
        if patient_id:
            params["patient_id"] = patient_id
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin

        try:
            response = requests.get(
                f"{API_BASE_URL}/clinical/dashboard-metrics",
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Excepción al conectar con el backend: {e}")
            return None

    @staticmethod
    def upload_historia_clinica(file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Envía el archivo binario al backend para ingestión RAG."""
        files = {
            "file": (filename, file_bytes)
        }
        try:
            response = requests.post(
                f"{API_BASE_URL}/rag/upload-hc",
                files=files,
                timeout=60
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Excepción al subir Historia Clínica: {e}")
            return None
        
    # El método validate_hc que llama al endpoint /rag/validate-hc del backend, 
    # será remplazado por MCP que llama a la función verificar_existencia_hc en serverhc.py
    @staticmethod
    def validate_hc(hc_id: str) -> Optional[Dict[str, Any]]:
        """Invoca al backend para validar si existe el ID de Historia Clínica."""
        try:
            response = requests.get(
                f"{API_BASE_URL}/rag/validate-hc",
                params={"hc_id": hc_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Excepción al validar HC: {e}")
            return None

    @staticmethod
    def query_hc(
        hc_id: str,
        pregunta: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """Invoca al endpoint RAG de Historia Clínica en el backend."""
        payload = {
            "hc_id": hc_id,
            "pregunta": pregunta,
            "model": model,
            "temperature": temperature
        }
        try:
            response = requests.post(
                f"{API_BASE_URL}/rag/query-hc",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Excepción al consultar HC RAG: {e}")
            return None

    @staticmethod
    def _get_headers(extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Obtiene headers predeterminados con autenticación JWT desde st.session_state."""
        headers = {}
        token = st.session_state.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @classmethod
    def get_ultimo_nivel_glucosa(cls, patient_id: str) -> Dict[str, Any]:
        """Obtiene el último nivel de glucosa del paciente."""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agent/glucosa/{patient_id}",
                headers=cls._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.warning("⚠️ No se encontró historial clínico previo para este usuario.")
        except Exception as e:
            st.error(f"Error conectando con el servicio de historial clínico: {e}")
        return {"glucose_level": 0.0, "doctor_id": None}

    @classmethod
    def obtener_telefono_medico(cls, doctor_id: str) -> str:
        """Obtiene el número telefónico del médico tratante."""
        if not doctor_id:
            return ""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agent/medico/telefono/{doctor_id}",
                headers=cls._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("mobile_phone", "")
        except Exception as e:
            st.error(f"Error recuperando teléfono del médico: {e}")
        return ""

    @classmethod
    def obtener_medicos_disponibles(cls) -> Tuple[str, List[Dict[str, Any]]]:
        """Obtiene el catálogo de médicos disponibles del sistema."""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agent/medicos/disponibles",
                headers=cls._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                medicos = response.json()
                if medicos:
                    medicos_lines = [
                        f"  {idx + 1}. {m.get('nombre', 'Dr.')} (Especialidad: {m.get('especialidad', 'General')})"
                        for idx, m in enumerate(medicos)
                    ]
                    return "\n".join(medicos_lines), medicos
                return "- Ningún médico registrado actualmente.", []
            else:
                st.warning(f"⚠️ No se pudo obtener la lista de médicos (Status {response.status_code})")
                return "- Ningún médico registrado actualmente.", []
        except Exception as e:
            st.error(f"Error conectando con la API de médicos: {e}")
            return "Error al cargar médicos del sistema.", []

    @classmethod
    def gestionar_solicitud_urgente_lab(cls, payload: Dict[str, Any]) -> str:
        """Registra la orden de laboratorio urgente."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/agent/solicitud/laboratorio",
                json=payload,
                headers=cls._get_headers({"Content-Type": "application/json"}),
                timeout=10
            )
            if response.status_code in (200, 201):
                return response.json().get("message", "Orden de laboratorio generada con éxito.")
        except Exception as e:
            return f"Error en registro de laboratorio: {e}"
        return "No se pudo generar la orden de laboratorio."

    @classmethod
    def gestionar_alertas_glucosa(cls, payload: Dict[str, Any]) -> str:
        """Notifica una alerta de glucosa crítica al backend."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/agent/alertas/glucosa",
                json=payload,
                headers=cls._get_headers({"Content-Type": "application/json"}),
                timeout=10
            )
            if response.status_code in (200, 201):
                return "Alerta registrada correctamente."
        except Exception as e:
            return f"Error enviando alerta: {e}"
        return "Fallo en registro de alerta."

    @classmethod
    def agendar_cita_rutinario(cls, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Agenda una cita médica de seguimiento."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/agent/citas/agendar",
                json=payload,
                headers=cls._get_headers({"Content-Type": "application/json"}),
                timeout=10
            )
            if response.status_code in (200, 201):
                msg = response.json().get("detail", "Cita agendada correctamente.")
                return True, msg
            else:
                error_detail = response.json().get("detail", response.text)
                return False, f"Error API ({response.status_code}): {error_detail}"
        except Exception as e:
            return False, f"Error de conexión al agendar cita: {e}"

    @classmethod
    def transcribir_audio(cls, audio_bytes: bytes) -> str:
        """Envía un archivo de audio WAV para su transcripción."""
        if not audio_bytes:
            st.warning("No se ha grabado ningún audio.")
            return ""
        try:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            response = requests.post(
                f"{API_BASE_URL}/audio/transcribe",
                files=files,
                headers=cls._get_headers(),
                timeout=20
            )
            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Error de conexión al transcribir audio: {e}")
        return ""

    @classmethod
    def ejecutar_llamada_twilio(cls, to_phone: str, nombre_paciente: str, dni_paciente: str) -> str:
        """Solicita la ejecución de una llamada automatizada de voz."""
        try:
            payload = {
                "to_phone": to_phone,
                "patient_name": nombre_paciente,
                "patient_dni": dni_paciente,
                "message_type": "EMERGENCIA_HIPOGLUCEMIA"
            }
            response = requests.post(
                f"{API_BASE_URL}/twilio/make-call",
                json=payload,
                headers=cls._get_headers({"Content-Type": "application/json"}),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("call_sid", "SID_DESCONOCIDO")
            else:
                st.error(f"Error en respuesta de servidor al realizar llamada: {response.status_code}")
        except Exception as e:
            st.error(f"Error al conectar con backend para llamada de emergencia: {e}")
        return "NO_INICIADA"

    @classmethod
    def enviar_sms_twilio(cls, to_phone: str, mensaje: str) -> str:
        """Solicita el envío de un mensaje de texto SMS."""
        try:
            payload = {"to_phone": to_phone, "message": mensaje}
            response = requests.post(
                f"{API_BASE_URL}/twilio/send-sms",
                json=payload,
                headers=cls._get_headers({"Content-Type": "application/json"}),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("sms_sid", "SMS_ENVIADO")
            else:
                st.error(f"Error en respuesta de servidor al enviar SMS: {response.status_code}")
        except Exception as e:
            st.error(f"Error conectando con backend para SMS: {e}")
        return "SMS_FALLIDO"
    
    @classmethod
    def registrar_triaje_emergencia(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Envía los datos de triaje de emergencia al backend para registrar la cita.
        
        :param payload: Diccionario con patient_id, patient_name, glucose_value, 
                        symptoms, exercise_frequency, recent_intake y doctor_id.
        :return: JSON de respuesta del servidor o None en caso de error.
        """
        # Ajusta la URL según el prefijo de tus endpoints                   
        endpoint = f"{API_BASE_URL}/agent/triaje/emergencia" 
        headers = cls._get_headers({"Content-Type": "application/json"})  # Incluye Authorization Header si aplica

        try:
            #logger.info(f"Enviando registro de triaje de emergencia para paciente {payload.get('patient_id')}")
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=10  # Timeout de 10 segundos para prevenir cuelgues
            )

            # Lanza una excepción si el status HTTP es 4xx o 5xx
            response.raise_for_status()

            data = response.json()
            #logger.info("Triaje de emergencia registrado exitosamente en el backend.")
            return data

        except requests.exceptions.HTTPError as http_err:
            error_msg = f"Error HTTP al registrar triaje de emergencia: {http_err.response.status_code} - {http_err.response.text}"
            logger.error(error_msg)
            # Retorna un diccionario formateado o re-lanza según prefieras manejarlo en Streamlit
            return {"error": True, "detail": error_msg}

        except requests.exceptions.ConnectionError as conn_err:
            error_msg = f"Error de conexión con el servidor backend: {str(conn_err)}"
            #logger.error(error_msg)
            return {"error": True, "detail": "No se pudo conectar con el servidor backend."}

        except requests.exceptions.Timeout:
            error_msg = "Tiempo de espera agotado al intentar registrar la emergencia."
            #logger.error(error_msg)
            return {"error": True, "detail": error_msg}

        except Exception as ex:
            error_msg = f"Error inesperado en registrar_triaje_emergencia: {str(ex)}"
            logger.error(error_msg)
            return {"error": True, "detail": error_msg}