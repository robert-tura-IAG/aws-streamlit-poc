import streamlit as st
from datetime import date, timedelta
import pandas as pd

def set_base_session_sates():
    if 'ini_date' not in st.session_state:
        st.session_state.ini_date = date.today() - timedelta(days = 365)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = date.today()
    if 'group' not in st.session_state:
        st.session_state.group = True

    return

def filter_data(df):
    df = df[
        (df['Date'] <= pd.to_datetime(st.session_state.ini_date)) &
        (df['Date'] >= pd.to_datetime(st.session_state.end_date))
    ]
    if st.session_state.ac_model != []:
        df = df[df['ac_model'].isin(st.session_state.ac_model)]
    if st.session_state.ac_description != []:
        df = df[df['aircraft_description'].isin(st.session_state.ac_description)]
    if st.session_state.reg_number != []:
        df = df[df['ac_registration_id'].isin(st.session_state.reg_number)]
    if st.session_state.finding_source != []:
        df = df[df['finding_source'].isin(st.session_state.finding_source)]
    if st.session_state.ata != []:
        df = df[df['ata_chapter_code'].isin(st.session_state.ata)]
    if st.session_state.taskcard != []:
        df = df[df['task_id'].isin(st.session_state.taskcard)]
    if st.session_state.amm_code != []:
        df = df[df['amm_reference'].isin(st.session_state.amm_code)]
    return df

def change_verbose_to_code(value):
    if value == "Aircraft Type":
        return "ac_model"
    elif value == "Location":
        return "location"
    elif value == "ATA Code":
        return "ata_chapter_code"
    elif value == "Aircraft Registration":
        return "ac_registration_id"
    return value