import os
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from streamlit_mic_recorder import mic_recorder

from src.services.api_client import APIClient

# Importar constantes y funciones utilitarias de triaje
from src.views.util_triaje import (
    generar_fechas_disponibles_rango,
    obtener_horarios_disponibles,
    extraer_fecha_hora_de_texto,
    extraer_doctor_id_de_texto
)

if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

# ==========================================
# CONSTANTES Y CONFIGURACIÓN DE APIs BACKEND
# ==========================================
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

HORARIOS_REGLAS = """
Horarios de atención estándar: Lunes a Viernes de 07:00 a 19:00 hrs.
Sábados de 07:00 a 16:00 hrs. Domingos de 09:00 a 13:00 hrs.
"""

REGLAS_LABORATORIO_MD = """
### 🧪 Indicaciones para Orden de Laboratorio Urgente
1. Acuda al laboratorio clínico central dentro de las **próximas 12 a 24 horas**.
2. Guarde un ayuno de **8 horas** antes de la toma de muestra.
3. Presente su documento de identidad (DNI) en la ventanilla de atención.
"""
# ==========================================
# VISTA PRINCIPAL STREAMLIT
# ==========================================

def render_triaje_view():
    st.title("🩺 Módulo de Triaje")

    # 1. Control de Acceso por Rol
    if st.session_state.get("rol") != "paciente":
        st.info("El módulo de Triaje y Agendamiento está diseñado exclusivamente para interacción de pacientes en su portal.")
        return

    # 2. Lógica Inicial de Triaje (Determinista)
    if "triage_category" not in st.session_state:

        try:
            username = st.session_state.get("username", "")

            # Obtener datos del backend con fallback seguro
            datos_triaje = APIClient.get_ultimo_nivel_glucosa(username)

            # Extraer y asignar al session_state
            if isinstance(datos_triaje, dict):
                st.session_state["glucose_level"] = float(datos_triaje.get("glucose_level", 0.0))
                st.session_state["doctor_id"] = datos_triaje.get("doctor_id")
            else:
                st.session_state["glucose_level"] = 0.0
                st.session_state["doctor_id"] = None

            #st.session_state["glucose_level"] = datos_triaje.get("glucose_level", 0.0)
            #st.session_state["doctor_id"] = datos_triaje.get("doctor_id")

            if st.session_state["doctor_id"]:
                telefono = APIClient.obtener_telefono_medico(st.session_state["doctor_id"])
                st.session_state["telefono_medico_tratante"] = telefono

            # Continuar con la lógica según el nivel de glucosa
            glucose = st.session_state["glucose_level"]

            # Clasificación de Triaje
            if glucose > 0:
                if glucose < 70.0:
                    st.session_state["triage_category"] = "EMERGENCIA"
                    st.session_state["action_message"] = "Llamar a Emergencias"
                    st.session_state["chat_history"] = [
                        AIMessage(content=f"Hola {st.session_state['display_name']}, detectamos un nivel de glucosa crítico ({glucose} mg/dL). Por favor, indícame qué síntomas tienes ahora mismo.")
                    ]
                elif glucose > 250.0:
                    st.session_state["triage_category"] = "URGENCIAS"
                    st.session_state["action_message"] = "Solicitar Orden Laboratorio"
                else:
                    st.session_state["triage_category"] = "AGENDAR CITA"
                    st.session_state["action_message"] = "Felicidades: Agendar tu cita de seguimiento"
                    st.session_state["chat_history"] = [
                        AIMessage(content=f"¡Hola **{st.session_state['display_name']}!** Tu nivel de glucosa está en metas de control diario ({glucose} mg/dL). Vamos a agendar tu cita de seguimiento. **¿Qué día te convendría asistir?**")
                    ]
            else:
                # Manejo de Primera Consulta o sin registros previos
                st.session_state["triage_category"] = "AGENDAR CITA"
                st.session_state["action_message"] = "Evaluación Inicial / Agendar Cita"
                st.session_state["chat_history"] = [
                    AIMessage(content=f"¡Hola **{st.session_state['display_name']}!** No registra una toma de glucosa reciente en el sistema. Vamos a agendar tu cita de evaluación. **¿Qué día prefieres asistir?**")
                ]

        except Exception as e:
            st.error(f"Error en motor de triaje: {e}")
            st.stop()

    # 3. Interfaz del Portal Clínico
    st.subheader(f"Portal Clínico de: {st.session_state.get('display_name', 'Paciente')}")
    st.info(f"**Nivel de Glucosa Analizado:** {st.session_state.get('glucose_level')} mg/dL")

    # 4. Manejo de Estado de Cierre de Sesión
    if st.session_state.get("sesion_cerrada", False):
        st.warning("⚠️ Esta sesión de triaje ha finalizado. Por favor, reinicia el módulo para una nueva consulta.")
        if st.button("🔄 Reiniciar Triaje"):
            for key in ["sesion_cerrada", "triage_category", "chat_history", "glucose_level", "registro_urgencia_realizado", "fechas_sugeridas"]:
                st.session_state.pop(key, None)
            st.rerun()
        return

    # 5. Ruteo por Categoría de Triaje
    category = st.session_state.get("triage_category")

    # CASO A: URGENCIAS (Procesamiento Automático)
    if category == "URGENCIAS":
        if "registro_urgencia_realizado" not in st.session_state:
            with st.spinner("Registrando orden de laboratorio en sistema..."):
                payload = {
                    "reason": "Triaje automático: Glucosa > 250 mg/dL",
                    "patient_id": st.session_state.get("username", "DESCONOCIDO"),
                    "patient_name": st.session_state.get("display_name"),
                    "glucose_value": st.session_state.get("glucose_level")
                }
                mensaje_resultado = APIClient.gestionar_solicitud_urgente_lab(payload)
                st.success(mensaje_resultado)
                st.session_state["registro_urgencia_realizado"] = True
                st.session_state["sesion_cerrada"] = True

        st.markdown(REGLAS_LABORATORIO_MD)
        st.warning("Su sesión ha finalizado. Por favor diríjase al laboratorio con las indicaciones descritas.")

    # CASO B & C: CHAT DE EMERGENCIA Y AGENDAMIENTO RUTINARIO
    else:
        llm = ChatOpenAI(
            model=st.session_state.get("selected_model", "gpt-4o"),
            temperature=st.session_state.get("selected_temp", 0.2)
        )

        # SUB-CASO: EMERGENCIA (Hipoglucemia Critical)
        if category == "EMERGENCIA":
            nombre_paciente = st.session_state.get('display_name', 'Paciente Desconocido')
            dni_paciente = st.session_state.get('username', 'N/A')

            st.error(f"🚨 **ALERTA, resultado del triaje determinista: {st.session_state.get('action_message')}**")

            col1, col2 = st.columns(2)
            call_sid = "NO_INICIADA"

            with col1:
                if st.button("📞 Llamar a Emergencia"):
                    with st.spinner("Iniciando llamada automatizada de emergencia..."):
                        call_sid = APIClient.ejecutar_llamada_twilio(
                            to_phone=st.session_state.get("telefono_medico_tratante", ""),
                            nombre_paciente=nombre_paciente,
                            dni_paciente=dni_paciente
                        )
                        if call_sid != "NO_INICIADA":
                            st.success("✅ La llamada de alerta ha sido enviada al médico.")

                        tool_args = {
                            "patient_id": st.session_state.get("username"),
                            "glucose_value": st.session_state.get("glucose_level"),
                            "sintomas": "Llamada a emergencia, el paciente presenta hipoglucemia grave",
                            "twilio_call_sid": call_sid,
                            "doctor_id": str(st.session_state.get("doctor_id")),
                            "destino_llamada": "Emergencia"
                        }
                        APIClient.gestionar_alertas_glucosa(tool_args)

            with col2:
                if st.button("👨‍⚕️ Contactar al Médico"):
                    with st.spinner("Iniciando llamada automatizada al médico tratante..."):
                        call_sid = APIClient.ejecutar_llamada_twilio(
                            to_phone=st.session_state.get("telefono_medico_tratante", ""),
                            nombre_paciente=nombre_paciente,
                            dni_paciente=dni_paciente
                        )
                        if call_sid != "NO_INICIADA":
                            st.success("✅ La llamada de alerta ha sido enviada al médico.")

                        tool_args = {
                            "patient_id": st.session_state.get("username"),
                            "glucose_value": st.session_state.get("glucose_level"),
                            "sintomas": "Llamada al Médico Tratante, el paciente presenta hipoglucemia grave",
                            "twilio_call_sid": call_sid,
                            "doctor_id": str(st.session_state.get("doctor_id")),
                            "destino_llamada": "Médico Tratante"
                        }
                        APIClient.gestionar_alertas_glucosa(tool_args)

            # Selector Multimodal (Texto / Voz)
            modo = st.radio("Seleccione modo de interacción:", ["Texto", "Voz (Micrófono)"], horizontal=True)
            texto_procesar = None

            if modo == "Texto":
                texto_procesar = st.chat_input("Responda síntomas, ejercicio y consumo...")
            else:
                audio = mic_recorder(key='audio_emergencia', start_prompt="🎙️ Grabar síntomas", stop_prompt="⏹️ Detener")
                if audio:
                    texto_procesar = APIClient.transcribir_audio(audio.get('bytes'))
                    st.write(f"Transcripción: {texto_procesar}")

            # Procesamiento con Agente Conversacional Multimodal
            if texto_procesar:
                st.session_state["chat_history"].append(HumanMessage(content=texto_procesar))

                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", (
                        "Eres un asistente de endocrinología. El paciente tiene HIPOGLUCEMIA GRAVE.\n"
                        "PROTOCOLO: Debes recopilar obligatoriamente:\n"
                        "1. Síntomas exactos actuales. 2. Frecuencia de ejercicio semanal. 3. Consumo reciente carbohidratos o alcohol.\n"
                        "Sé conciso, profesional y empático."
                    )),
                    MessagesPlaceholder(variable_name="chat_history"),
                ])

                agent_chain = prompt_template | llm

                with st.spinner("Procesando emergencia..."):
                    response = agent_chain.invoke({"chat_history": st.session_state["chat_history"]})

                    # Registrar información y notificar vía SMS
                    msg_sms = f"ALERTA URGENTE: {st.session_state['display_name']} - Síntomas: {texto_procesar}"
                    sms_sid = APIClient.enviar_sms_twilio(st.session_state.get("telefono_medico_tratante", ""), msg_sms)

                    payload_alerta = {
                        "patient_id": st.session_state.get("username"),
                        "patient_name": st.session_state.get("display_name"),
                        "glucose_value": st.session_state.get("glucose_level"),
                        "sintomas": texto_procesar,
                        "twilio_call_sid": sms_sid,
                        "doctor_id": str(st.session_state.get("doctor_id"))
                    }
                    APIClient.gestionar_alertas_glucosa(payload_alerta)

                    
                    payload_triaje_emergencia = {
                        "patient_id": st.session_state.get("username"),
                        "patient_name": st.session_state.get("display_name"),
                        "glucose_value": st.session_state.get("glucose_level"),
                        "sintomas": texto_procesar,
                        #"exercise_frequency": "No especificado / Reportado en chat",
                        #"recent_intake": "No especificado / Reportado en chat",
                        "doctor_id": str(st.session_state.get("doctor_id"))
                    }
                    

                    #res_emergencia = APIClient.registrar_triaje_emergencia(payload_triaje_emergencia)
                    APIClient.registrar_triaje_emergencia(payload_triaje_emergencia)
                    
                    st.success("✅ Cita de emergencia registrada en BD y SMS enviado al médico.")
                    st.session_state["chat_history"].append(AIMessage(content=response.content))
                    st.session_state["sesion_cerrada"] = True
                    st.rerun()

        # SUB-CASO: AGENDAR CITA RUTINARIA
        else:
            st.success(f"**Resultado del Triaje Determinista:** {st.session_state.get('action_message')}")            
            # 1. PANTALLA DE CITA CONFIRMADA / CERRADA
            if st.session_state.get("sesion_cerrada"):
                st.success("✅ **¡CITA REGISTRADA EXITOSAMENTE EN EL SISTEMA!**")
                
                mensaje_confirmacion = st.session_state.get(
                    "mensaje_confirmacion_cita", 
                    "Su cita ha sido registrada con éxito."
                )
                st.info(f"📋 **Detalles del Registro:**\n\n{mensaje_confirmacion}")

                with st.expander("💬 Ver conversación de agendamiento", expanded=False):
                    for msg in st.session_state.get("chat_history", []):
                        role = "assistant" if isinstance(msg, AIMessage) else "user"
                        with st.chat_message(role):
                            st.write(msg.content)

                st.markdown("---")
                st.markdown("##### ¿Qué deseas hacer a continuación?")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🔄 Reiniciar Triaje", type="primary", use_container_width=True):
                        for key in ["triage_category", "chat_history", "sesion_cerrada", "fechas_sugeridas", "mensaje_confirmacion_cita", "appointment_id"]:
                            st.session_state.pop(key, None)
                        st.rerun()

                with col2:
                    if st.button("❌ Cancelar Cita / Cambiar Horario", type="secondary", use_container_width=True):
                        st.session_state["sesion_cerrada"] = False
                        st.warning("⚠️ La cita previa se ha descartado. Puedes seleccionar una nueva fecha u horario en el chat.")
                        st.rerun()

            else:                
                # 2. PROCESO DE CHAT Y SELECCIÓN CON DATOS REALES DE LA API BACKEND
                # Obtener la lista y el texto directamente desde tu función backend
                medicos_str_prompt, medicos_list = APIClient.obtener_medicos_disponibles()

                # Generar las fechas sugeridas (+7 a +37 días)
                if "fechas_sugeridas" not in st.session_state:
                    st.session_state["fechas_sugeridas"] = generar_fechas_disponibles_rango(dias_inicio=7, total_dias=30)

                fechas_list = st.session_state["fechas_sugeridas"]

                # Formatear la lista de fechas con Feriados en Rojo
                fechas_numeradas_prompt = []
                for idx, item in enumerate(fechas_list):
                    if item["es_feriado"]:
                        linea = f"  {idx + 1}. <span style='color:red;'>{item['texto_formateado']} - Feriado ({item['nombre_feriado']})</span> [NO DISPONIBLE]"
                    else:
                        linea = f"  {idx + 1}. {item['texto_formateado']} ({item['iso_date']})"
                    fechas_numeradas_prompt.append(linea)

                fechas_str_prompt = "\n".join(fechas_numeradas_prompt)

                horarios_list = obtener_horarios_disponibles()
                horarios_numerados = "\n".join([f"  {idx + 1}. {horario}" for idx, horario in enumerate(horarios_list)])

                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", (
                        "Eres el asistente virtual encargado de agendar citas de seguimiento preventivo en Diabetes.\n\n"
                        f"MÉDICOS DISPONIBLES (Obtenidos del sistema):\n{medicos_str_prompt}\n\n"
                        f"FECHAS DISPONIBLES EN EL SISTEMA:\n{fechas_str_prompt}\n\n"
                        f"HORARIOS DISPONIBLES:\n{horarios_numerados}\n\n"
                        "REGLAS CRÍTICAS DE INTERACCIÓN:\n"
                        "1. Presenta explícitamente al usuario los Médicos Disponibles listados arriba, las Fechas y los Horarios.\n"
                        "2. Solicita al usuario elegir indicando el número correspondiente a: (A) Médico, (B) Fecha y (C) Horario.\n"
                        "3. Las fechas marcadas con '- Feriado' NO SE PUEDEN SELECCIONAR. Si el usuario intenta elegir una, pídele amablemente seleccionar otra opción.\n"
                        "4. Al confirmar la cita, menciona claramente el Médico seleccionado, la fecha formateada en español, la fecha ISO (YYYY-MM-DD) y la hora.\n"
                        "5. En tu mensaje final de confirmación incluye explícitamente palabras clave como 'agendada' o 'confirmada'."
                    )),
                    MessagesPlaceholder(variable_name="chat_history"),
                ])

                agent_chain = prompt_template | llm

                # Renderizar historial
                for msg in st.session_state.get("chat_history", []):
                    role = "assistant" if isinstance(msg, AIMessage) else "user"
                    with st.chat_message(role):
                        st.markdown(msg.content, unsafe_allow_html=True)

                # Chat Input
                if user_input := st.chat_input("Escribe tu selección (ej: Médico 1, Fecha 2, Hora 1)..."):
                    with st.chat_message("user"):
                        st.write(user_input)

                    st.session_state["chat_history"].append(HumanMessage(content=user_input))

                    with st.chat_message("assistant"):
                        with st.spinner("Procesando selección..."):
                            response = agent_chain.invoke({"chat_history": st.session_state["chat_history"]})
                            output_text = response.content

                            if "confirmad" in output_text.lower() or "agendad" in output_text.lower():
                                
                                app_date, app_time = extraer_fecha_hora_de_texto(output_text, fechas_list)
                                doctor_id = extraer_doctor_id_de_texto(output_text, medicos_list)

                                payload_appointment = {
                                    "patient_id": str(st.session_state.get("username", "")),
                                    "patient_name": str(st.session_state.get("display_name", "")),
                                    "glucose_value": float(st.session_state.get("glucose_level", 0.0)),
                                    "doctor_id": doctor_id,
                                    "appointment_date": app_date,
                                    "appointment_time": app_time,
                                    "details": output_text
                                }

                                exito, result_tool = APIClient.agendar_cita_rutinario(payload_appointment)

                                if exito:
                                    st.session_state["mensaje_confirmacion_cita"] = (
                                        f"**Doctor ID:** {doctor_id}\n"
                                        f"**Fecha programada:** {app_date}\n"
                                        f"**Hora programada:** {app_time}\n\n"
                                        f"**Respuesta del Backend:** {result_tool}"
                                    )
                                    st.session_state["sesion_cerrada"] = True
                                    st.rerun()
                                else:
                                    output_text = f"❌ **NO SE PUDO GUARDAR LA CITA.**\n\n*Detalle:* {result_tool}\n\nPor favor, intenta seleccionar nuevamente."

                            st.markdown(output_text, unsafe_allow_html=True)
                            st.session_state["chat_history"].append(AIMessage(content=output_text))