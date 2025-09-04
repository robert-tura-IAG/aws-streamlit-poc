import streamlit as st
from datetime import date, timedelta
import pandas as pd

def set_base_session_sates():
    # Fechas por defecto (últimos 365 días)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = date.today()
    if 'ini_date' not in st.session_state:
        st.session_state.ini_date = date.today() - timedelta(days=365)
    if 'group' not in st.session_state:
        st.session_state.group = True

    # Inicializar TODAS las claves de filtros que usa filter_data
    for k in ["ac_model", "ac_description", "reg_number",
              "finding_source", "ata", "taskcard", "amm_code", "location"]:
        st.session_state.setdefault(k, [])
    return


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Asegurar tipo datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # Normalizar rango (independiente del orden seleccionado)
        start = pd.to_datetime(min(st.session_state.end_date, st.session_state.ini_date))
        end   = pd.to_datetime(max(st.session_state.end_date, st.session_state.ini_date))

        df = df[(df["Date"] >= start) & (df["Date"] <= end)]

    # Helper para aplicar filtros de forma segura
    def _safe_filter(_df, col_name, state_key):
        vals = st.session_state.get(state_key, [])
        if vals and col_name in _df.columns:
            return _df[_df[col_name].isin(vals)]
        return _df

    df = _safe_filter(df, "ac_model", "ac_model")
    df = _safe_filter(df, "aircraft_description", "ac_description")
    df = _safe_filter(df, "ac_registration_id", "reg_number")
    df = _safe_filter(df, "finding_source", "finding_source")
    df = _safe_filter(df, "ata_chapter_code", "ata")
    df = _safe_filter(df, "task_id", "taskcard")
    df = _safe_filter(df, "amm_reference", "amm_code")
    loc_vals = st.session_state.get("location", [])
    if loc_vals:
        if "location" in df.columns:
            df = df[df["location"].isin(loc_vals)]
        elif "defect_location" in df.columns:
            df = df[df["defect_location"].isin(loc_vals)]

    return df


def change_verbose_to_code(value: str) -> str:
    if value == "Aircraft Type":
        return "ac_model"
    elif value == "Location":
        return "location"
    elif value == "ATA Code":
        return "ata_chapter_code"
    elif value == "Aircraft Registration":
        return "ac_registration_id"  # corregido
    return value
