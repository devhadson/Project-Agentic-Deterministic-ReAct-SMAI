import streamlit as st
import pandas as pd
from src.services.api_client import APIClient

def render_dashboard_view():
    st.subheader("📊 Panel de Control Analítico")
    
    # --- UI DE FILTROS ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    # Filtro de Fechas
    fecha_inicio = col_f1.date_input("Fecha Inicio", value=None)
    fecha_fin = col_f2.date_input("Fecha Fin", value=None)
    
    # Filtro de Paciente (solo si no es rol paciente)
    selected_patient = None
    if st.session_state.get("rol") in ["enfermería", "médico", "administrador"]:
        selected_patient = col_f3.text_input("Filtrar por DNI Paciente (opcional)")

    # Formateo de fechas para pasar como parámetro YYYY-MM-DD
    str_fecha_inicio = str(fecha_inicio) if fecha_inicio else None
    str_fecha_fin = str(fecha_fin) if fecha_fin else None
    
    # Invocación al cliente API del Backend
    data = APIClient.get_dashboard_metrics(
        rol=st.session_state.get("rol", "paciente"),
        username=st.session_state.get("username", ""),
        patient_id=selected_patient,
        fecha_inicio=str_fecha_inicio,
        fecha_fin=str_fecha_fin
    )

    if not data:
        st.error("No se pudieron cargar los datos desde el servidor.")
        return

    stats = data.get("stats", {})
    detalle = data.get("detalle", [])

    # --- VISUALIZACIÓN DE MÉTRICAS ---
    if not stats and not detalle:
        st.info("No se encontraron datos con los filtros seleccionados.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", data.get("total", 0))
        c2.metric("Emergencias 🚨", data.get("emergencias", 0))
        c3.metric("Citas 📅", data.get("citas", 0))
        c4.metric("Urgencia ⚠️", data.get("urgencias", 0))
        
        if stats:
            st.bar_chart(stats)

        # --- SECCIÓN: LISTADO DETALLADO ---
        st.markdown("---")
        st.subheader("📋 Detalle de Registros")
        
        if detalle:
            df_detalle = pd.DataFrame(detalle)
            # Formatear nombres de columnas
            df_detalle.columns = [col.replace("_", " ") for col in df_detalle.columns]
            st.dataframe(df_detalle, use_container_width=True)
        else:
            st.write("No hay detalles disponibles para estos filtros.")