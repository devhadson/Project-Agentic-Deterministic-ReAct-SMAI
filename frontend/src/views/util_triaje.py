import re
import locale
from datetime import datetime, timedelta

# --- DICCIONARIO DE FERIADOS EN PERÚ (MM-DD) ---
FERIADOS_PERU = {
    "01-01": "Año Nuevo",
    "05-01": "Día del Trabajo",
    "06-29": "San Pedro y San Pablo",
    "07-23": "Día de la Fuerza Aérea del Perú",
    "07-28": "Fiestas Patrias",
    "07-29": "Fiestas Patrias",
    "08-06": "Batalla de Junín",
    "08-30": "Santa Rosa de Lima",
    "10-08": "Combate de Angamos",
    "11-01": "Día de todos los Santos",
    "12-08": "Inmaculada Concepción",
    "12-09": "Batalla de Ayacucho",
    "12-25": "Navidad"
}

# --- LISTAS DE DÍAS Y MESES EN ESPAÑOL ---
DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", 
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def formatear_fecha_espanol(fecha: datetime) -> str:
    """Formatea la fecha al estilo 'miércoles, 19 de agosto de 2026'."""
    dia_nombre = DIAS_ES[fecha.weekday()]
    mes_nombre = MESES_ES[fecha.month - 1]
    return f"{dia_nombre}, {fecha.day} de {mes_nombre} de {fecha.year}"


def generar_fechas_disponibles_rango(dias_inicio: int = 7, total_dias: int = 30) -> list[dict]:
    """
    Genera fechas disponibles entre +7 y +37 días a partir de hoy.
    Retorna una lista de diccionarios con metadatos de la fecha y si es feriado.
    """
    fechas_info = []
    fecha_base = datetime.now() + timedelta(days=dias_inicio)
    
    for i in range(total_dias):
        fecha = fecha_base + timedelta(days=i)
        
        # Omitir domingos (día 6)
        if fecha.weekday() == 6:
            continue
            
        key_feriado = fecha.strftime("%m-%d")
        es_feriado = key_feriado in FERIADOS_PERU
        nombre_feriado = FERIADOS_PERU.get(key_feriado, "")
        
        iso_date = fecha.strftime("%Y-%m-%d")
        texto_formateado = formatear_fecha_espanol(fecha)
        
        fechas_info.append({
            "iso_date": iso_date,
            "texto_formateado": texto_formateado,
            "es_feriado": es_feriado,
            "nombre_feriado": nombre_feriado
        })
            
    return fechas_info


def obtener_horarios_disponibles() -> list[str]:
    """Retorna la lista de horarios de atención numerados."""
    return [
        "08:00 AM - 09:00 AM",
        "09:00 AM - 10:00 AM",
        "10:00 AM - 11:00 AM",
        "11:00 AM - 12:00 PM",
        "03:00 PM - 04:00 PM",
        "04:00 PM - 05:00 PM",
        "05:00 PM - 06:00 PM",
        "06:00 PM - 07:00 PM"        
    ]


def extraer_fecha_hora_de_texto(texto: str, fechas_sugeridas: list[dict]) -> tuple[str, str]:
    """Extrae la fecha ISO (YYYY-MM-DD) y la hora desde el texto del chat."""
    match_fecha = re.search(r'(\d{4}-\d{2}-\d{2})', texto)
    if match_fecha:
        fecha_str = match_fecha.group(1)
    else:
        # Asignar la primera fecha disponible de la lista como fallback
        fecha_str = (
            fechas_sugeridas[0]["iso_date"] 
            if fechas_sugeridas else (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        )

    match_hora = re.search(r'(\d{1,2}:\d{2})', texto)
    hora_str = match_hora.group(1) if match_hora else "09:00"

    return fecha_str, hora_str

def extraer_doctor_id_de_texto(texto: str, medicos_list: list[dict]) -> int:
    """
    Compara el texto devuelto por el LLM con la lista de médicos devuelta por el backend 
    para extraer su ID original.
    """
    if not medicos_list:
        return 1

    texto_lower = texto.lower()
    for med in medicos_list:
        nombre_partes = str(med.get("nombre", "")).lower().split()
        if any(parte in texto_lower for parte in nombre_partes if len(parte) > 3):
            return med.get("id") or med.get("doctor_id") or 1

    # Retornar el ID del primer médico de la lista como respaldo
    return medicos_list[0].get("id") or medicos_list[0].get("doctor_id") or 1