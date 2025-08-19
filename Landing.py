import streamlit as st
import plotly as py
import plotly.io as pio
from plotly import graph_objects as go
from datetime import date


with st.sidebar:
    st.header("Settings")
    # st.write("Time Window")
    time_range = st.date_input(
        "Time Window",
        [date.today(), date.today()],
        min_value=None,
        max_value=None
    )
    ac_model = st.multiselect("Select Aircraft Model", 
                              options = ["A333", "A320", "A21N", "A332", "A20N", "A321", "A319"])
    # ac_description = 
    # reg_number = 
    # ata = 
    # taskcard = 
    # amm_code = 
    # finding_source = 
    

labels = ["People who like streamlit", "People who don't know about streamlit"]
values = [80, 20]


# pull is given as a fraction of the pie radius
fig = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    textinfo='label+percent',
    insidetextorientation='radial',
    pull=[0, 0]  # Adjusted to match the number of labels
)])


fig.update_layout(
    title_text="Demo streamlit app")


st.plotly_chart(fig, sharing='streamlit')