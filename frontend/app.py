import os
from dotenv import load_dotenv
import streamlit as st
from src.services.api_client import APIClient
from src.components.auth_ui import render_login
from src.components.sidebar import render_sidebar
from src.views import dashboard_view, triaje_view, historia_view, cargar_view

st.set_page_config(page_title="Sistema Médico AI", page_icon="🤖", layout="wide")

def load_configurations() -> None:
    """Inicializa variables de entorno seguras."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ CRÍTICO: La variable 'OPENAI_API_KEY' no está configurada en el entorno.")
        st.stop()
    #else:
    #    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    load_configurations()
except Exception as e:
    st.error(f"Error de inicialización: {e}")
    st.stop()

# Google Identity MVP3
GOOGLE_CLIENT_ID        = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET    = os.getenv("GOOGLE_CLIENT_SECRET")

def main():
    # Callback Google OAuth
    if "code" in st.query_params and not st.session_state.get("logged_in"):
        code = st.query_params["code"]
        res = APIClient.process_google_callback(code)
        if res.status_code == 200:
            data = res.json()
            st.session_state.update({
                "logged_in": True,
                "token": data["access_token"],
                "username": data["username"],
                "display_name": data["display_name"],
                "rol": data["rol_nombre"]
            })
            st.query_params.clear()
            st.rerun()

    if not st.session_state.get("logged_in"):
        render_login()
    else:
        modulo = render_sidebar()
        if modulo == "Dashboard":
            dashboard_view.render_dashboard_view()
        elif modulo == "Triaje / Agendamiento":
            #triaje_view.render()
            triaje_view.render_triaje_view()
        elif modulo == "Historia Clínica":
            historia_view.render_historia_view()
        elif modulo == "Cargar Historia":
            cargar_view.render_cargar_view()

if __name__ == "__main__":
    main()