"""Header component for the Resume Customizer application."""
import streamlit as st

def render_header():
    """Render the application header."""
    
    # Title and description
    st.title("Resume Customizer")
    
    st.markdown(
        """
        <div class="info-box">
        📄 Upload your resume and our AI will help you customize it for job applications.
        <br>This tool analyzes job descriptions and tailors your resume to increase your chances of success.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add a divider
    st.divider()
