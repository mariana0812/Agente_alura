
Uso:
    streamlit run interfaz_chat.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from datetime import datetime, timezone
from agente_rag import responder
from registro_ejecucion import actualizar_feedback

st.set_page_config(page_title="Agente NextSkill", page_icon="🎓", layout="centered")

st.title("🎓 Agente de Soporte — NextSkill")
st.caption(
    "⚠️ Estás hablando con un **agente de inteligencia artificial**, no con una persona. "
    "Responde con base en la documentación oficial de la plataforma (reglamento, reembolsos, "
    "FAQ, guía de uso y becas)."
)

if "historial" not in st.session_state:
    st.session_state.historial = []

for i, msg in enumerate(st.session_state.historial):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("fuentes"):
            st.caption(f"📎 Fuentes: {', '.join(msg['fuentes'])}")
            col1, col2 = st.columns([1, 1])
            if col1.button("👍", key=f"up_{i}"):
                actualizar_feedback(msg["timestamp"], "positivo")
                st.toast("¡Gracias por tu feedback!")
            if col2.button("👎", key=f"down_{i}"):
                actualizar_feedback(msg["timestamp"], "negativo")
                st.toast("Gracias, lo tendremos en cuenta.")

pregunta = st.chat_input("Escribe tu pregunta sobre la plataforma...")

if pregunta:
    st.session_state.historial.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en la documentación..."):
            respuesta, fuentes = responder(pregunta)
        st.markdown(respuesta)
        st.caption(f"📎 Fuentes: {', '.join(fuentes)}")

    st.session_state.historial.append({
        "role": "assistant",
        "content": respuesta,
        "fuentes": fuentes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
