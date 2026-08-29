import os
import requests
import streamlit as st
from PIL import Image
from pathlib import Path

if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

# ==========================================
# CONSTANTES Y CONFIGURACIÓN DE APIs BACKEND
# ==========================================
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

@st.cache_data(ttl=300)  # Guarda la respuesta en caché durante 5 minutos
def fetch_user_permissions(rol: str) -> list[str]:
    """
    Obtiene dinámicamente desde el Backend la lista de módulos habilitados en BD según el rol.
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/auth/permissions",
            params={"rol": str(rol).strip()},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            modulos = data.get("modulos", [])
            if modulos:
                return modulos
    except Exception as e:
        st.sidebar.warning(f"⚠️ No se pudo conectar con Auth API: {e}")

    # Lista por defecto o fallback en caso de error de conexión
    return ["Dashboard", "Triaje / Agendamiento"]

def render_sidebar() -> str:
    """
    Renders the sidebar component for model selection, module navigation, 
    and session management.
    
    Returns:
        str: El módulo seleccionado por el usuario para renderizar en app.py
    """
    with st.sidebar:

        COMPONENTS_DIR = Path(__file__).resolve().parent
        IMAGE_PATH = COMPONENTS_DIR.parent / "assets" / "robot-smai.png"

        if IMAGE_PATH.exists():
            try:
                img = Image.open(IMAGE_PATH)
                st.image(
                    img,
                    use_container_width=True,
                    caption="SMAI"
                )
            except Exception as e:
                st.error(f"Error al cargar imagen: {e}")
        else:
            st.title("🤖 SMAI")

        # 2. Encabezado e Información de Usuario y Rol
        st.header("⚙️ Panel de Control")
        
        display_name = st.session_state.get("display_name", st.session_state.get("username", "Usuario"))
        rol_actual = str(st.session_state.get("rol", "paciente")).lower()
        
        st.markdown(f"**Usuario:** `{display_name}`")
        st.markdown(f"**Rol Asignado:** `{rol_actual.upper()}`")                
        
        # 3. Configuración de Parámetros de LLM
        st.subheader("Configuración LLM")
        
        model_options = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        current_model = st.session_state.get("selected_model", "gpt-4o")
        model_index = model_options.index(current_model) if current_model in model_options else 0
        
        st.session_state["selected_model"] = st.selectbox(
            "Modelo", 
            options=model_options, 
            index=model_index,
            help="Selecciona el modelo LLM para el procesamiento de triaje y agentes."
        )
        
        current_temp = float(st.session_state.get("selected_temp", 0.0))
        st.session_state["selected_temp"] = st.slider(
            "Temperatura", 
            min_value=0.0, 
            max_value=1.0, 
            value=current_temp, 
            step=0.1,
            help="Define la creatividad de las respuestas (0.0 = Determinista/Preciso)."
        )

        # 4. Navegación por Módulos (Cargados dinámicamente desde la BD vía API Auth)
        modulos_validos = fetch_user_permissions(rol_actual)
        
        # Preservar o reiniciar la selección de módulo si no es válida para el rol
        current_modulo = st.session_state.get("modulo_activo")
        default_index = modulos_validos.index(current_modulo) if current_modulo in modulos_validos else 0
        
        selected_module = st.selectbox(
            "Módulo Activo", 
            options=modulos_validos,
            index=default_index
        )
        st.session_state["modulo_activo"] = selected_module
        
        st.markdown("---")

        # 5. Cierre de Sesión
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        return selected_module