"""
Component package for the Resume Customizer application.

This package contains all the UI components used in the application.
"""

# Phase 1 components
from .header import render_header
from .upload_section import render_upload_section
from .status_section import render_status_section

# Phase 2 components
from .job_description_section import render_job_description_section

# Phase 3 components
from .customization_options import render_customization_options

# Phase 4 components
from .customization_request_section import render_customization_request_section
from .customization_status_section import render_customization_status_section
from .results_section import render_results_section
