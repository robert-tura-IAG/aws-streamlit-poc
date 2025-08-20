import streamlit as st
from plotly import graph_objects as go
from src.data_load import get_data_ta_1, enhance_dataframe

st.markdown("# Timeline Analysis")

df = get_data_ta_1()

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

df = enhance_dataframe(df)

st.dataframe(df)
