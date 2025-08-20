import streamlit as st
from plotly import graph_objects as go
import pandas as pd
from datetime import datetime
import numpy as np

st.header("Timeline Analysis")

#Data loading
x_values = pd.date_range(start='01/01/2023', end='01/01/2024', periods=12).tolist()
y_values = [150, 138, 64, 123, 98, 72, 103, 83, 103, 135, 150, 122]
df = pd.DataFrame({
    'Date': x_values,
    'Value': y_values
})

col1, col2, col3 = st.columns([3, 1, 1], vertical_alignment = "center")

with col1:
    fig_1 = go.Figure()
    fig_1.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['Value']
        )
    )
    fig_1.update_layout(
    autosize=False,
    height=600,
    )

    st.plotly_chart(fig_1, config = {'scrollZoom': False})

with col2:
    st.dataframe(df)

with col3:
    st.markdown("###### 💡 **Insights Detectados**")

    st.success("🏆 Aeronave Más Eficiente:\n\nEC-MNK con un score de 383.6\n\nPromedio de 26.2h por finding")

    st.warning("⚠️ Ubicación Más Costosa:\n\nfwd cargo con €11142 promedio\n\nRequiere 89.6h promedio")

    st.error("🚨 Patrón Crítico:\n\n55 findings críticos en AFT CARGO\n\nRevisar procedimientos de mantenimiento preventivo")

df['ac_model'] = np.random.choice(["A333", "A320", "A21N", "A332", "A20N", "A321", "A319"], 12)
df['ac_description'] = np.random.choice(["AIRBUS A320-214", "AIRBUS A320-251N", "AIRBUS A330-302", "AIRBUS A330-200"], 12)
df['reg_number'] = np.random.choice(["EI-DEE", "EI-DVM", "EI-NSD", "EI-DEH", "EI-DVM"], 12)
df['finding_source'] = np.random.choice(["CHECK 1000 FH", "TASKCARD", "NRC DOCUMENT"], 12)
df['ata'] = np.random.choice(["25-21", "05-20", "25-00", "20-00", "20-00"], 12)
df['taskcard'] = np.random.choice(["ALT-25-0002", "ALT-28-0001", "323000-01-1", "ZL-500-03-1", "ALT-74-0001-RH"], 12)
df['amm_code'] = np.random.choice(["74-00-00-710-802", "21-28-00-710-802-A", "11-00-00", "53-00-14-283-002", "51-72-11"], 12)

st.dataframe(df)
