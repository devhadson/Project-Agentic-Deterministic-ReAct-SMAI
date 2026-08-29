import os
from pathlib import Path
from PIL import Image
import streamlit as st
from src.services.api_client import APIClient


def render_login():

    # CSS personalizado
    st.markdown("""
    <style>
        .welcome-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.8rem;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            z-index: 999;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="welcome-card">                        
        <h2>Atención médica inteligente Aplicando IA</h2>
        <p>Disponible 24/7</p>
    </div>""", unsafe_allow_html=True)
    
    #col1, col2, col3 = st.columns([1, 2, 1])
    col1, col2 = st.columns([1, 2])

    with col1:
        # Carga dinámica y segura de la imagen con PIL
        COMPONENTS_DIR = Path(__file__).resolve().parent
        IMAGE_PATH = COMPONENTS_DIR.parent / "assets" / "ai-medicine-robot-600.webp"

        if IMAGE_PATH.exists():
            try:
                img = Image.open(IMAGE_PATH)
                st.image(
                    img,
                    use_container_width=True,
                    caption="Bienvenido al Sistema Médico de Asistencia Inteligente (SMAI). Inicie sesión para acceder a su panel de control y gestionar sus datos clínicos de manera segura."
                )
            except Exception as e:
                st.error(f"Error al cargar imagen: {e}")
        else:
            st.warning(f"⚠️ Imagen no encontrada en: `{IMAGE_PATH}`")

    with col2:
        st.subheader("🔑 Iniciar Sesión")

        tab_local, tab_oauth = st.tabs(["Credenciales Locales", "Google OAuth"])        
        with tab_local:
            with st.form("form_login"):
                u = st.text_input("Usuario / DNI")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar", use_container_width=True):
                    res = APIClient.login_local(u, p)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.update({
                            "logged_in": True,
                            "token": data["access_token"],
                            "username": data["username"],
                            "display_name": data["display_name"],
                            "rol": data["rol_nombre"]
                        })
                        st.rerun()
                    else:
                        st.error("❌ Credenciales inválidas.")

        with tab_oauth:

            st.markdown("<p style='text-align:center; color:gray;'><strong>" \
                                        "Acceso: Administrador de Sistema</strong><br>" \
                                        "Al hacer clic, será redirigido a la autenticación de Google.</p><br>", unsafe_allow_html=True)
            
            url = APIClient.get_google_url()
            if url:
                st.markdown(f'''
                    <a href="{url}" target="_self" style="text-decoration:none;">
                        <div style="background-color:#4285F4;color:white;text-align:center;padding:10px;border-radius:5px;font-weight:bold;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/2/2d/Logo_Google_blanco.png" style="width:20px; margin-right:10px;">
                            Continuar con Google
                        </div>
                    </a>
                ''', unsafe_allow_html=True)

    st.markdown("""
        <div class="footer">
            <p>© 2026 SMAI - Powered by Hadson Paredes</p>        
            <p>Horarios: Lun-Sáb 7:00-19:00 • Dom 9:00-18:00</p>
        </div>
        """, unsafe_allow_html=True)