from pathlib import Path
import sys
import pandas as pd
import streamlit as st
import hashlib

# --- Hacer visible el paquete 'sql_agent' ---
# Si tu repo tiene:  <RAIZ>/sql_agent/app/api/agent.py
ROOT = Path(__file__).resolve().parents[1]   # sube de /pages a la raíz
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Si en tu equipo está dentro de 'src/sql_agent', descomenta estas dos líneas:
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

# --- Importar tu agente (ajusta el import si cambiaste las rutas) ---
from sql_agent.app.api.agent import ask_agent


# ---------------- UI ----------------
st.set_page_config(page_title="Chatbot Findings", layout="wide")
st.title("💬 Chatbot de Findings")

# Selector de visualización (la llamada al agente se hace una sola vez por pregunta)
mode = st.radio("Format:", ["Texto", "SQL"], horizontal=True, index=0)
st.caption("holis")

# Estado
if "messages" not in st.session_state:
    st.session_state.messages = []   # cada item: {"role": "user|assistant", "content", "sql", "columns", "rows"}
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

# Limpieza de chat
with st.sidebar:
    if st.button("🧹 Limpiar conversación"):
        st.session_state.messages.clear()
        st.session_state.last_hash = None
        st.experimental_rerun()

def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def _render_message(m: dict, current_mode: str):
    """Pinta un mensaje del historial según el modo actual."""
    with st.chat_message(m.get("role", "assistant")):
        if m.get("role") == "assistant":
            if current_mode == "Texto":
                st.markdown(m.get("content", "") or "_(sin texto)_")
            else:
                sql = m.get("sql")
                if sql:
                    st.code(sql, language="sql")
                else:
                    st.markdown("_No se generó SQL para esta respuesta._")
        else:
            st.markdown(m.get("content", ""))

        # Pinta tabla si hay datos (en ambos modos)
        cols = m.get("columns") or []
        rows = m.get("rows") or []
        if cols and rows:
            try:
                df = pd.DataFrame(rows, columns=cols)  # rows: list[list], columns: list[str]
            except Exception:
                # fallback si el backend devolviera list[dict]
                df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

# Historial
for msg in st.session_state.messages:
    _render_message(msg, mode)

# Entrada de usuario
user_msg = st.chat_input("Escribe tu pregunta y pulsa Enter…")

if user_msg:
    # Evita doble ejecución por rerender
    h = _md5(user_msg)
    if h != st.session_state.last_hash:
        st.session_state.last_hash = h

        # Añade mensaje de usuario al historial
        user_entry = {"role": "user", "content": user_msg}
        st.session_state.messages.append(user_entry)
        _render_message(user_entry, mode)

        # ÚNICA llamada al agente (no se repite por cambiar de pestaña)

        with st.spinner("Consultando…"):
            try:
                result = ask_agent(user_msg)  # -> {"answer_text","sql","columns","rows"}
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        assistant_entry = {
            "role": "assistant",
            "content": result.get("answer_text", ""),
            "sql": result.get("sql"),
            "columns": result.get("columns", []),
            "rows": result.get("rows", []),
        }
        st.session_state.messages.append(assistant_entry)
        _render_message(assistant_entry, mode)
