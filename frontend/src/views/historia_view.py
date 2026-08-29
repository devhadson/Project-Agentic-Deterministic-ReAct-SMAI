import streamlit as st
from src.services.api_client import APIClient
from mcp_server.serverhc import verificar_existencia_hc#, obtener_registros_hc

def render_historia_view():
    st.title("📋 Buscar en Historia Clínica")

    # 1. Asegurar que la lista de historial existe en la sesión
    if "mensajes_rag" not in st.session_state:
        st.session_state["mensajes_rag"] = []

    # Mostrar el historial de la conversación actual
    for msg in st.session_state["mensajes_rag"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- LÓGICA DE BÚSQUEDA RAG (SOLO MÉDICOS / ENFERMERÍA) ---
    rol_usuario = st.session_state.get('rol', '').lower()
    
    if rol_usuario in ['enfermería', 'médico']:
        hc_busqueda = st.text_input("Filtrar por ID de Historia Clínica (ej. HC-52384):")

        # Validar existencia de la H.C. llamando al API Client Backend
        hc_valida = False
        if hc_busqueda:
            res_validation = APIClient.validate_hc(hc_busqueda)
            #res_validation = verificar_existencia_hc(hc_busqueda)  # Llamada a la función MCP para obtener registros asociados
            
            if res_validation and res_validation.get("exists"):
                hc_valida = True
                st.success(res_validation.get("message"))
            else:
                mensaje_error = res_validation.get("message") if res_validation else f"❌ La Historia Clínica '{hc_busqueda}' no se encuentra cargada o indexada."
                st.error(mensaje_error)

        # Habilitar el chat solo si se ha validado la H.C.
        if hc_valida:
            model_selected = st.session_state.get("selected_model", "gpt-4o-mini")
            temp_selected = st.session_state.get("selected_temp", 0.0)

            if pregunta := st.chat_input(f"¿Qué deseas consultar en la H.C. '{hc_busqueda}'?"):
                # Agregar y pintar pregunta del usuario
                st.session_state["mensajes_rag"].append({"role": "user", "content": pregunta})
                with st.chat_message("user"):
                    st.write(pregunta)

                # Solicitar respuesta al Backend mediante RAG
                with st.chat_message("assistant"):
                    with st.spinner("Analizando H.C. con IA..."):
                        # Llamada al API Client para procesar la pregunta con RAG desde el backend,
                        # no se está llamando a la función verificar_existencia_hc en serverhc.py (MCP)
                        response_data = APIClient.query_hc(
                            hc_id=hc_busqueda,
                            pregunta=pregunta,
                            model=model_selected,
                            temperature=temp_selected
                        )

                        if response_data and "respuesta" in response_data:
                            respuesta_final = response_data["respuesta"]
                            st.write(respuesta_final)
                            st.session_state["mensajes_rag"].append({
                                "role": "assistant", 
                                "content": respuesta_final
                            })
                        else:
                            st.error("Ocurrió un error al procesar la respuesta con el servidor.")

        else:
            if not hc_busqueda:
                st.info("ℹ️ Por favor, ingrese un ID de Historia Clínica válido para habilitar el asistente.")
    else:
        st.warning("🔒 Su rol actual no dispone de permisos para consultar Historias Clínicas.")