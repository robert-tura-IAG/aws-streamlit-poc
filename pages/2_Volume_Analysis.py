import streamlit as st
from plotly import graph_objects as go
from src.data_load import get_data_va_1, get_data_va_2

st.markdown("# Volume Analysis")


df = get_data_va_1()
df_ = get_data_va_2()

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure(go.Bar(
        x=df["total_findings"],
        y=df["ata_codes"],
        orientation="h"))

    fig.update_layout(
        title="Top 10 ATA Codes with Most Findings",
        xaxis_title="Total of Findings",
        yaxis_title="ATA Code",
        yaxis=dict(categoryorder="total ascending"))

    st.plotly_chart(fig, use_container_width=True)

with col2:
    heatmap_data = df_.pivot_table(
        index="ATA Code",
        columns="Aircraft Type",
        values="Findings",
        aggfunc="sum",
        fill_value=0)

    # Build heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale="Reds",
        colorbar=dict(title="Findings")))

    fig.update_layout(
        title="Findings Severity by ATA Code and Aircraft Type",
        xaxis_title="Aircraft Type",
        yaxis_title="ATA Code",
        xaxis={'tickangle': 45})
    
    st.plotly_chart(fig, use_container_width=True)

