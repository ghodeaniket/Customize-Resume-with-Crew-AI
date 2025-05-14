#!/bin/bash

# Run the Resume Customizer Streamlit application
echo "Starting Resume Customizer Streamlit application..."

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Error: Streamlit is not installed. Please install it using pip:"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Run the application
streamlit run app.py
