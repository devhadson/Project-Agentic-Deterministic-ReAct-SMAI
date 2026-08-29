import streamlit as st
from src.services.api_client import APIClient

def render_cargar_view():
    st.title("📥 Carga de Historias Clínicas")
    
    uploaded_file = st.file_uploader("Subir archivo (PDF/TXT)", type=["pdf", "txt"])
    
    if uploaded_file and st.button("Procesar y Vectorizar"):
        with st.spinner("Ingestando archivo y generando embeddings en el servidor..."):
            file_bytes = uploaded_file.getbuffer().tobytes()
            
            response = APIClient.upload_historia_clinica(
                file_bytes=file_bytes,
                filename=uploaded_file.name
            )
            
            if response:
                index_id = response.get("index_id")
                hc_id = response.get("hc_id")
                
                st.success(f"✅ Archivo indexado correctamente.")
                st.write(f"**ID del Registro Indexado:** `{index_id}`")
                st.write(f"**Identificador Clínico Extraído:** `{hc_id}`")
                st.info("Guarde el ID de la Historia Clínica para realizar consultas futuras en el módulo correspondiente.")
            else:
                st.error("❌ Ocurrió un error al intentar procesar e indexar el archivo en el servidor.")