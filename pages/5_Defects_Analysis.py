import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.data_load import get_local_csv_data
import pandas as pd
from src.utils import set_base_session_sates, filter_data
import numpy as np

set_base_session_sates()

# Data Loading
df = get_local_csv_data().copy()

# Input Section - Filters
input1, input2, input3, input4 = st.columns(4)

with input1:
    date_interval = st.date_input(
        "Time Window",
        (st.session_state.ini_date, st.session_state.end_date),
        min_value=None,
        max_value=None
    )

    # Update only when range is complete (2 dates)
    if isinstance(date_interval, (list, tuple)) and len(date_interval) == 2:
        start, end = sorted(date_interval)
        st.session_state.ini_date = start
        st.session_state.end_date = end

with input2:
    st.session_state.ac_model = st.multiselect("Select Aircraft Model", 
                                options = df["ac_model"].unique())
with input3:
    st.session_state.reg_number = st.multiselect("Select Registration Number", 
                                    options = df["ac_registration_id"].unique())
with input4:
    st.session_state.taskcard = st.multiselect("Select Taskcard", 
                                options = df["task_id"].unique())

# Apply filters
filtered_df = filter_data(df)

# Main Content - Distribution Analysis
st.subheader("Defect Categories Distribution")

col1, col2 = st.columns(2)

with col1:
    # Defect Categories Bar Chart
    defect_counts = filtered_df["defect_category"].value_counts().head(10)
    
    fig_bar = go.Figure(go.Bar(
        x=defect_counts.values,
        y=defect_counts.index,
        orientation='h',
        marker_color='#ff6b6b',
        text=defect_counts.values,
        textposition='outside'
    ))
    
    fig_bar.update_layout(
        title=dict(text="Top 10 Defect Categories", font=dict(size=16)),
        xaxis_title=dict(text="Number of Defects", font=dict(size=12)),
        yaxis_title=dict(text="Defect Category", font=dict(size=12)),
        height=600,
        margin=dict(l=20, r=20, t=60, b=60),
        yaxis=dict(categoryorder="total ascending", tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=10))
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    # Top 10 Specific Defects
    specific_defect_counts = filtered_df["defect_specific_code"].value_counts().head(10)
    
    fig_specific = go.Figure(go.Bar(
        x=specific_defect_counts.index,
        y=specific_defect_counts.values,
        marker_color='#4ecdc4',
        text=specific_defect_counts.values,
        textposition='outside'
    ))
    
    fig_specific.update_layout(
        title=dict(text="Top 10 Specific Defect Codes", font=dict(size=16)),
        xaxis_title=dict(text="Specific Defect Code", font=dict(size=12)),
        yaxis_title=dict(text="Number of Defects", font=dict(size=12)),
        height=600,
        margin=dict(l=20, r=20, t=60, b=60),
        xaxis=dict(tickangle=45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=10))
    )
    
    st.plotly_chart(fig_specific, use_container_width=True)

# Detailed Data Table
st.subheader("Detailed Defects Data")

# Rename columns for better display
column_rename_map = {
    'work_order_id': "Work Order",
    'ac_registration_id': "Aircraft Registration", 
    'ac_model': "Aircraft Model",
    'defect_category': "Defect Category",
    'defect_specific_code': "Specific Defect",
    'location': "Location",
    'ata_chapter_code': "ATA Chapter",
    'description_failure': "Failure Description",
    'Date': 'Date'
}

# Select relevant columns for display (including failure description)
display_columns = ['work_order_id', 'ac_registration_id', 'ac_model', 'defect_category', 
                  'defect_specific_code', 'location', 'ata_chapter_code', 'description_failure', 'Date']

show_df = filtered_df[display_columns].copy()
# Format Date column to yyyy-mm-dd
show_df['Date'] = show_df['Date'].dt.strftime('%Y-%m-%d')
show_df = show_df.rename(columns=column_rename_map)
st.dataframe(show_df, use_container_width=True, hide_index=True)