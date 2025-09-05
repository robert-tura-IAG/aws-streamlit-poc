import streamlit as st
from plotly import graph_objects as go
from src.data_load import get_local_csv_data
import pandas as pd
from datetime import date, timedelta
from src.utils import set_base_session_sates, filter_data

set_base_session_sates()

# Data Loading
df = get_local_csv_data().copy()

# Input Selection
input1, input2, input3, input4 = st.columns(4)
input5, input6, input7, input8 = st.columns(4)

with input1:
    date_interval = st.date_input(
        "Time Window",
        (st.session_state.ini_date, st.session_state.end_date),
        min_value=None,
        max_value=None
    )

    # Actualiza SOLO cuando el rango está completo (2 fechas)
    if isinstance(date_interval, (list, tuple)) and len(date_interval) == 2:
        start, end = sorted(date_interval)
        st.session_state.ini_date = start
        st.session_state.end_date = end
    # Si hay 1 fecha no hacer nada!!!!!!!!!!!!!!!

    st.session_state.group = st.checkbox("Group data?", value=True)
with input2:
    st.session_state.ac_model = st.multiselect("Select Aircraft Model", 
                                options = df["ac_model"].unique())
with input3:
    st.session_state.ac_description = st.multiselect("Select Aircraft Description", 
                                options = df["aircraft_description"].unique())
with input4:
    st.session_state.reg_number = st.multiselect("Select Registration Number", 
                                    options = df["ac_registration_id"].unique())
with input5:
    st.session_state.finding_source = st.multiselect("Select Finding Source", 
                                options = df["finding_source"].unique())
with input6:
    st.session_state.ata = st.multiselect("Select ATA Code Chapter", 
                                options = df["ata_chapter_code"].unique())
with input7:
    st.session_state.taskcard = st.multiselect("Select Taskcard", 
                                options = df["task_id"].unique())
with input8:
    st.session_state.amm_code = st.multiselect("Select AMM Code", 
                                    options = df["amm_reference"].unique())


filtered_df = filter_data(df)

unique_days = filtered_df['Date'].nunique()

if st.session_state.group:
    if unique_days > 150:
        # Group by month
        filtered_df['period'] = filtered_df['Date'].dt.to_period('M').dt.to_timestamp()
        group_label = 'Month'
    elif unique_days > 30:
        # Group by week
        filtered_df['period'] = filtered_df['Date'].dt.to_period('W').dt.start_time
        group_label = 'Week'
    else:
        # Group by day
        filtered_df['period'] = filtered_df['Date'].dt.normalize()
        group_label = 'Day'
else:
    # Group by day
    filtered_df['period'] = filtered_df['Date'].dt.normalize()
    group_label = 'Day'

# Then when displaying, format the output
filtered_df['period'] = filtered_df['period'].dt.strftime('%Y-%m-%d')

grouped = filtered_df.groupby('period').size().reset_index(name='Count')
grouped.rename(columns={'period': 'Period'}, inplace=True)

col1, col2, col3 = st.columns([3, 1, 1], vertical_alignment = "center")

with col1:
    fig_1 = go.Figure()
    fig_1.add_trace(
        go.Scatter(
            x=grouped['Period'],
            y=grouped['Count'],
            mode='lines+markers'
        )
    )
    fig_1.update_layout(
    autosize=False,
    height=600,
    )

    st.plotly_chart(fig_1, config = {'scrollZoom': False})

with col2:
    st.dataframe(grouped)

with col3:
    st.markdown("###### 💡 **Detected Insights**")

    st.success("🏆 Most Efficient Aircraft:\n\nEC-MNK with a score of 383.6\n\nAverage of 26.2h per finding")

    st.warning("⚠️ Most Expensive Location:\n\nfwd cargo with an average of €11,142\n\nRequires an average of 89.6h")

    st.error("🚨 Critical Pattern:\n\n55 critical findings in AFT CARGO\n\nReview preventive maintenance procedures")
             
# df = enhance_dataframe(df)

st.dataframe(filtered_df)
