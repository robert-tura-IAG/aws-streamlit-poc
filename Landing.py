import streamlit as st
import plotly as py
import plotly.io as pio
from plotly import graph_objects as go
from datetime import date

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

##############################################
###############Page Navigation################
##############################################
pages = [st.Page("Landing.py", title="🏠 Home"), 
         st.Page("pages/1_Timeline_Analysis.py", title="📈 Timeline Analysis"), 
         st.Page("pages/2_Volume_Analysis.py", title="📊 Volume Analysis"), 
         st.Page("pages/3_MRO_Analysis.py", title="🛠️ MRO Analysis"), 
         st.Page("pages/4_Chatbot.py", title="🤖 Chatbot")]

pg = st.navigation(pages, position="top")
pg.run()




with st.sidebar:
    #Date Input
    time_range = st.date_input(
        "Time Window",
        [date.today(), date.today()],
        min_value=None,
        max_value=None
    )

    if pg.title == "📈 Timeline Analysis":
        ac_model = st.multiselect("Select Aircraft Model", 
                                  options = ["A333", "A320", "A21N", "A332", "A20N", "A321", "A319"])
        ac_description = st.multiselect("Select Aircraft Description", 
                                        options = ["AIRBUS A320-214", "AIRBUS A320-251N", "AIRBUS A330-302", "AIRBUS A330-200"])
        reg_number = st.multiselect("Select Registration Number", 
                                        options = ["EI-DEE", "EI-DVM", "EI-NSD", "EI-DEH", "EI-DVM"])
        finding_source = st.multiselect("Select Finding Source", 
                                        options = ["CHECK 1000 FH", "TASKCARD", "NRC DOCUMENT"])
        ata = st.multiselect("Select ATA Code Chapter", 
                                        options = ["25-21", "05-20", "25-00", "20-00", "20-00"])
        taskcard = st.multiselect("Select Taskcard", 
                                        options = ["ALT-25-0002", "ALT-28-0001", "323000-01-1", "ZL-500-03-1", "ALT-74-0001-RH"])
        amm_code = st.multiselect("Select AMM Code", 
                                        options = ["74-00-00-710-802", "21-28-00-710-802-A", "11-00-00", "53-00-14-283-002", "51-72-11"])
        
    elif pg.title == "📊 Volume Analysis":
        aggreagtion_fields = ["Aircraft Type", "Location", "ATA Code", "Aircraft Model"]
        main_groupby_feature = st.selectbox("Main Aggregation", options = aggreagtion_fields)
        second_groupby_feature = st.selectbox("Secondary Aggregation", options = aggreagtion_fields)
        
    elif pg.title == "🛠️ MRO Analysis":
        aggreagtion_fields = ["Aircraft Type", "Location", "ATA Code", "Aircraft Model"]
        main_groupby_feature = st.selectbox("Main Aggregation", options = aggreagtion_fields)
        
    elif pg.title == "🤖 Chatbot":
        agent = st.selectbox("Select Agent", options=["Agent 1", "Agent 2", "Agent 3"])
    

# labels = ["People who like streamlit", "People who don't know about streamlit"]
# values = [80, 20]


# # pull is given as a fraction of the pie radius
# fig = go.Figure(data=[go.Pie(
#     labels=labels,
#     values=values,
#     textinfo='label+percent',
#     insidetextorientation='radial',
#     pull=[0, 0]  # Adjusted to match the number of labels
# )])


# fig.update_layout(
#     title_text="Demo streamlit app")


# st.plotly_chart(fig, sharing='streamlit')