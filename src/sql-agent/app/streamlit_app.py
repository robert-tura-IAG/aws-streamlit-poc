# app/streamlit_app.py
import os
import hashlib
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="MyFindings", layout="wide")
st.title("✈️ MyFindings")

# --- Selección de vista (NO debe provocar llamadas a la API)
mode = st.radio("Formato de respuesta:", options=["Texto", "SQL"], horizontal=True, index=0)
st.caption("Escribe tu pregunta y pulsa Enter. Cambiar entre pestañas no reenvía la consulta.")

# --- Estado
if "messages" not in st.session_state:
    st.session_state.messages = []   # [{role, content, sql?, columns?, rows?}]
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None  # evita reenvíos accidentales en reruns

def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

# --- Historial (sólo render; NO llama a la API)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "assistant":
            if mode == "Texto":
                # Texto sin SQL (el backend ya lo devuelve limpio)
                st.markdown(m.get("content", "") or "_(sin texto disponible)_")
            else:
                # Vista SQL: muestra la consulta si existe; si no, texto
                if m.get("sql"):
                    st.code(m["sql"], language="sql")
                else:
                    st.markdown("_No se generó SQL para esta respuesta._")
        else:
            st.markdown(m.get("content", ""))

        # Tabla (siempre que venga en la respuesta)
        if m.get("columns") and m.get("rows"):
            try:
                df = pd.DataFrame(m["rows"], columns=m["columns"])
            except Exception:
                # fallback por si rows ya viene como list[dict]
                df = pd.DataFrame(m["rows"])
            st.dataframe(df, use_container_width=True, hide_index=True)

# --- Entrada de chat (sólo aquí se POSTEA)
user_msg = st.chat_input("Escribe tu pregunta (Enter para enviar)...")

if user_msg:
    # Guard-rail para evitar doble envío en reruns
    h = _md5(user_msg)
    if h == st.session_state.last_hash:
        st.stop()
    st.session_state.last_hash = h

    # Pinta el mensaje del usuario y añade al historial
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Llama al backend UNA sola vez (backend ya devuelve texto+sql+tabla)
    try:
        resp = requests.post(f"{API_URL}/query", json={"question": user_msg}, timeout=120)
        data = resp.json()
        if resp.status_code != 200:
            raise RuntimeError(data.get("detail", "Error"))

        answer_text = data.get("answer_text", "")  # texto ya sin bloques SQL
        sql = data.get("sql")
        columns = data.get("columns", [])
        rows = data.get("rows", [])

        # Guarda ambos formatos; cambiar de pestaña sólo re-renderiza
        assistant_msg = {
            "role": "assistant",
            "content": answer_text,
            "sql": sql,
            "columns": columns,
            "rows": rows,
        }
        st.session_state.messages.append(assistant_msg)

        # Render inmediato del turno según pestaña actual
        with st.chat_message("assistant"):
            if mode == "Texto":
                st.markdown(answer_text or "_(sin texto disponible)_")
            else:
                st.code(sql, language="sql") if sql else st.markdown("_No se generó SQL para esta respuesta._")

            if columns and rows:
                try:
                    df = pd.DataFrame(rows, columns=columns)
                except Exception:
                    df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")
