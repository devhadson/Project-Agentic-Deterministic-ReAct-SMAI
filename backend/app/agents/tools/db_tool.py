import requests
from langchain_core.tools import tool

BASE_API_URL = "http://localhost:8000/api/v1/agent"

@tool
def get_ultimo_nivel_glucosa(patient_id: str) -> dict:
    """Obtiene el último nivel de glucosa y el ID del médico llamando al backend API."""
    res = requests.get(f"{BASE_API_URL}/glucosa/{patient_id}")
    return res.json() if res.status_code == 200 else {"glucose_level": 0.0, "doctor_id": None}

@tool
def gestionar_triaje_emergencia(symptoms: str, exercise_frequency: str, recent_intake: str, patient_id: str, patient_name: str, glucose_value: float, doctor_id: int) -> str:
    """Invoca la API del Backend para registrar la emergencia."""
    payload = {
        "symptoms": symptoms, "exercise_frequency": exercise_frequency,
        "recent_intake": recent_intake, "patient_id": patient_id,
        "patient_name": patient_name, "glucose_value": glucose_value,
        "doctor_id": doctor_id
    }
    res = requests.post(f"{BASE_API_URL}/triaje/emergencia", json=payload)
    return res.json().get("message", "Error al procesar emergencia") if res.status_code == 200 else "Error en la llamada API"

@tool
def agendar_cita_rutinario(patient_id: str, patient_name: str, appointment_date: str, appointment_time: str, doctor_id: int, details: str, glucose_value: float) -> str:
    """Invoca el endpoint API para agendar cita."""
    payload = {
        "patient_id": patient_id, "patient_name": patient_name,
        "appointment_date": appointment_date, "appointment_time": appointment_time,
        "doctor_id": doctor_id, "details": details, "glucose_value": glucose_value
    }
    res = requests.post(f"{BASE_API_URL}/citas/agendar", json=payload)
    return res.json().get("message", "Error al agendar cita") if res.status_code == 200 else "Error en la llamada API"
