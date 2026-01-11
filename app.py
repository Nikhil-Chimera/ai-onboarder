"""
AI-Onboarder - Streamlit Main Application
Transform GitHub repositories into comprehensive onboarding documentation
"""

import streamlit as st
import sys
from pathlib import Path

from pages import project_view as project_view

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.database import init_db
from pages import home
from lib.ui.styles import get_custom_css

# Page configuration
st.set_page_config(
    page_title="AI-Onboarder",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize database
init_db()

# Session state initialization
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

# Navigation
def navigate_to(page: str, project_id: str = None):
    st.session_state.current_page = page
    st.session_state.current_project_id = project_id
    st.rerun()

# Router
if st.session_state.current_page == 'home':
    home.render(navigate_to)
elif st.session_state.current_page == 'project':
    project_view.render(navigate_to, st.session_state.current_project_id)
