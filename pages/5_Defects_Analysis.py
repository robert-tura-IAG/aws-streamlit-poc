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
input5, input6, input7, input8 = st.columns(4)

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

# Apply filters
filtered_df = filter_data(df)

# Main Analysis Section
tab1, tab2, tab3, tab4 = st.tabs(["Distribution", "By Location", "Timeline", "Task Performance"])

with tab1:
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

with tab2:
    st.subheader("Defects by Location")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Locations by Defects
        location_counts = filtered_df["location"].value_counts().head(10)
        
        fig_loc = go.Figure(go.Bar(
            x=location_counts.index,
            y=location_counts.values,
            marker_color='#4ecdc4',
            text=location_counts.values,
            textposition='outside'
        ))
        
        fig_loc.update_layout(
            title="Top 10 Locations with Most Defects",
            xaxis_title="Location",
            yaxis_title="Number of Defects",
            height=600,
            xaxis={'tickangle': 45}
        )
        
        st.plotly_chart(fig_loc, use_container_width=True)
    
    with col2:
        # Heatmap: Defect Category vs Location
        # Get top 8 categories and top 10 locations for clarity
        top_categories = filtered_df['defect_category'].value_counts().head(8).index
        top_locations = filtered_df['location'].value_counts().head(10).index
        
        heatmap_data = filtered_df[
            (filtered_df['defect_category'].isin(top_categories)) & 
            (filtered_df['location'].isin(top_locations))
        ]
        
        category_location_crosstab = pd.crosstab(
            heatmap_data["defect_category"], 
            heatmap_data["location"]
        )
        
        fig_heat = go.Figure(go.Heatmap(
            z=category_location_crosstab.values,
            x=category_location_crosstab.columns,
            y=category_location_crosstab.index,
            colorscale="Reds",
            colorbar=dict(title="Count")
        ))
        
        fig_heat.update_layout(
            title="Defect Category vs Location",
            xaxis_title="Location",
            yaxis_title="Defect Category",
            height=600,
            xaxis={'tickangle': 45}
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)

with tab3:
    st.subheader("Defects Timeline")
    
    # Controls for timeline analysis
    col_control1, col_control2 = st.columns(2)
    
    with col_control1:
        analysis_type = st.selectbox(
            "Analysis Type",
            options=["defect_category", "defect_specific_code"],
            format_func=lambda x: "Defect Category" if x == "defect_category" else "Specific Defect Code"
        )
    
    with col_control2:
        top_n = st.selectbox(
            "Show Top N",
            options=[3, 5, 8, 10],
            index=1  # Default to 5
        )
    
    # Timeline analysis
    if 'Date' in filtered_df.columns:
        # Group by month and selected analysis type
        filtered_df['month'] = filtered_df['Date'].dt.to_period('M').dt.to_timestamp()
        timeline_data = filtered_df.groupby(['month', analysis_type]).size().reset_index(name='count')
        
        # Get top N categories for clarity
        top_categories = filtered_df[analysis_type].value_counts().head(top_n).index
        timeline_filtered = timeline_data[timeline_data[analysis_type].isin(top_categories)]
        
        title_text = f"Defects Timeline by {'Category' if analysis_type == 'defect_category' else 'Specific Code'} (Top {top_n})"
        
        fig_timeline = px.line(
            timeline_filtered, 
            x='month', 
            y='count', 
            color=analysis_type,
            title=title_text,
            labels={'month': 'Month', 'count': 'Number of Defects'}
        )
        
        fig_timeline.update_layout(height=600)
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.warning("Date information not available for timeline analysis")

with tab4:
    st.subheader("Task Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Task IDs with most defects
        task_counts = filtered_df["task_id"].value_counts().head(15)
        
        fig_task = go.Figure(go.Bar(
            x=task_counts.values,
            y=task_counts.index,
            orientation='h',
            marker_color='#9b59b6',
            text=task_counts.values,
            textposition='outside'
        ))
        
        fig_task.update_layout(
            title=dict(text="Top 15 Task IDs with Most Defects", font=dict(size=16)),
            xaxis_title=dict(text="Number of Defects", font=dict(size=12)),
            yaxis_title=dict(text="Task ID", font=dict(size=12)),
            height=600,
            margin=dict(l=20, r=20, t=60, b=60),
            yaxis=dict(categoryorder="total ascending", tickfont=dict(size=8)),
            xaxis=dict(tickfont=dict(size=10))
        )
        
        st.plotly_chart(fig_task, use_container_width=True)
    
    with col2:
        # Task ID vs Defect Category heatmap
        st.markdown("**Task ID vs Defect Category**")
        
        # Get top 10 task IDs and top 8 defect categories for clarity
        top_tasks = filtered_df['task_id'].value_counts().head(10).index
        top_defect_cats = filtered_df['defect_category'].value_counts().head(8).index
        
        task_defect_data = filtered_df[
            (filtered_df['task_id'].isin(top_tasks)) & 
            (filtered_df['defect_category'].isin(top_defect_cats))
        ]
        
        task_heatmap = pd.crosstab(
            task_defect_data['task_id'], 
            task_defect_data['defect_category']
        )
        
        fig_task_heat = go.Figure(go.Heatmap(
            z=task_heatmap.values,
            x=task_heatmap.columns,
            y=task_heatmap.index,
            colorscale="Purples",
            colorbar=dict(title="Count")
        ))
        
        fig_task_heat.update_layout(
            title=dict(text="Task ID vs Defect Category (Top 10 Tasks)", font=dict(size=16)),
            xaxis_title=dict(text="Defect Category", font=dict(size=12)),
            yaxis_title=dict(text="Task ID", font=dict(size=12)),
            height=600,
            margin=dict(l=20, r=20, t=60, b=60),
            xaxis=dict(tickangle=45, tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=8))
        )
        
        st.plotly_chart(fig_task_heat, use_container_width=True)

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
    'Date': 'Date'
}

# Select relevant columns for display (excluding ground time, risk level, and maintenance type)
display_columns = ['work_order_id', 'ac_registration_id', 'ac_model', 'defect_category', 
                  'defect_specific_code', 'location', 'ata_chapter_code', 'Date']

show_df = filtered_df[display_columns].copy()
# Format Date column to yyyy-mm-dd
show_df['Date'] = show_df['Date'].dt.strftime('%Y-%m-%d')
show_df = show_df.rename(columns=column_rename_map)
st.dataframe(show_df, use_container_width=True, hide_index=True)