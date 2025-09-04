import streamlit as st
from plotly import graph_objects as go
from src.data_load import get_data_va_1, get_data_va_2, get_local_csv_data
import pandas as pd
from src.utils import set_base_session_sates,change_verbose_to_code

set_base_session_sates()

# Data Loading
df = get_local_csv_data().copy()
df['Date'] = pd.to_datetime(df['Date'])


# Input Section
aggreagtion_fields = ["Aircraft Type", "Location", "ATA Code", "Aircraft Registration"]
input1, input2, input3, input4 = st.columns(4)
with input1:
    date_interval = st.date_input(
        "Time Window",
        [st.session_state.end_date, st.session_state.ini_date],
        min_value=None,
        max_value=None
    )
    st.session_state.end_date = date_interval[0]
    st.session_state.ini_date = date_interval[1]
    st.session_state.group = st.checkbox("Group data?", value = True)
with input2:
    main_agg = st.selectbox("Main Aggregation", options = aggreagtion_fields)
with input3:
    secondary_agg = st.selectbox("Secondary Aggregation", options = aggreagtion_fields)

main_groupby_feature = change_verbose_to_code(main_agg)
second_groupby_feature = change_verbose_to_code(secondary_agg)


# Data Grouping
if main_groupby_feature == second_groupby_feature:
    grouped_df_ = df.groupby([main_groupby_feature]).size().reset_index(name="Findings")
else:
    grouped_df_ = df.groupby([second_groupby_feature, main_groupby_feature]).size().reset_index(name="Findings")

grouped_df_ = grouped_df_.sort_values("Findings", ascending=False).head(10)


# Visualization
col1, col2 = st.columns(2)

with col1:
    fig = go.Figure(go.Bar(
        x=grouped_df_["Findings"],
        y=grouped_df_[main_groupby_feature],
        orientation="h"))

    fig.update_layout(
        title=f"Top 10 {main_agg} with Most Findings",
        xaxis_title="Total of Findings",
        yaxis_title=main_agg,
        yaxis=dict(categoryorder="total descending", type='category'))

    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Data Pivoting for heatmap (limit to top 10 for both axes)
    top_rows = grouped_df_[main_groupby_feature].unique()[:10]
    top_cols = grouped_df_[second_groupby_feature].unique()[:10]

    # Data Pivoting
    heatmap_data = grouped_df_.pivot_table(
        index=main_groupby_feature,
        columns=second_groupby_feature,
        values="Findings",
        aggfunc="sum",
        fill_value=0
    ).loc[top_rows, top_cols]

    # Build heatmap
    fig = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=heatmap_data.columns,
    y=heatmap_data.index,
    colorscale="Reds",
    colorbar=dict(title="Findings")))

    fig.update_layout(
        title=f"Findings Severity by {main_agg} and {secondary_agg}",
        xaxis_title=secondary_agg,
        yaxis_title=main_agg,
        xaxis={'tickangle': 15, 'type': 'category'}, 
        yaxis=dict(categoryorder="total descending", type='category'))
    
    st.plotly_chart(fig, use_container_width=True)

