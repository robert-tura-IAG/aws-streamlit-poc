import streamlit as st
import plotly as py
import plotly.io as pio
from plotly import graph_objects as go
from datetime import date, timedelta
from src.utils import set_base_session_sates

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed"
)

##############################################
###############Page Navigation################
##############################################
pages = [st.Page("pages/0_Home.py", title="🏠 Home"), 
         st.Page("pages/1_Timeline_Analysis.py", title="📈 Timeline Analysis"), 
         st.Page("pages/2_Volume_Analysis.py", title="📊 Volume Analysis"), 
         st.Page("pages/3_MRO_Analysis.py", title="🛠️ MRO Analysis"), 
         st.Page("pages/4_Chatbot.py", title="🤖 Chatbot")]

pg = st.navigation(pages, position="top")
pg.run()

set_base_session_sates()
