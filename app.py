"""
Databricks Workflows Launcher
Main application entry point with navigation
"""
import streamlit as st
from databricks.sdk import WorkspaceClient
from components.trigger_job import show_trigger_job_page
from components.run_status import show_run_status_page

st.set_page_config(
    page_title="Workflows Launcher", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default Streamlit navigation
hide_default_nav = """
    <style>
    .css-1d391kg {display: none}
    .css-1lsmgbg {display: none}
    [data-testid="stSidebarNav"] {display: none}
    </style>
"""
st.markdown(hide_default_nav, unsafe_allow_html=True)

# Initialize WorkspaceClient
w = WorkspaceClient()

st.header("Workflows", divider=True)

# Clear and customize sidebar navigation
st.sidebar.empty()
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page", ["TRIGGER JOB", "RUN STATUS"], index=0)
    
    st.divider()
    
    if page == "TRIGGER JOB":
        st.caption("🚀 Trigger Databricks jobs with custom parameters")
    else:
        st.caption("📊 Monitor job run history and status")

# Route to appropriate page
if page == "TRIGGER JOB":
    show_trigger_job_page(w)
elif page == "RUN STATUS":
    show_run_status_page(w)