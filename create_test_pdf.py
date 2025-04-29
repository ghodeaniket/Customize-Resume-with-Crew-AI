#!/usr/bin/env python3
"""
Create Test PDF Resume

This script generates a sample PDF resume for testing the Resume Customizer application.
"""
import os
import sys
from pathlib import Path

try:
    # Try to import reportlab
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
except ImportError:
    print("ERROR: The 'reportlab' package is required to create PDF files.")
    print("Please install it using: pip install reportlab")
    sys.exit(1)

# Create test_data directory if it doesn't exist
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

# Path for the output PDF file
pdf_path = test_data_dir / "test_resume.pdf"

print(f"Creating test PDF resume at: {pdf_path}")

# Create a new PDF
c = canvas.Canvas(str(pdf_path), pagesize=letter)

# Set font styles
title_font = "Helvetica-Bold"
heading_font = "Helvetica-Bold"
normal_font = "Helvetica"

# Add content to the PDF
def add_text(text, x, y, font=normal_font, size=12):
    c.setFont(font, size)
    c.drawString(x, y, text)

# Title and contact information
add_text("John Doe", 1*inch, 10*inch, title_font, 18)
add_text("Software Engineer", 1*inch, 9.7*inch, heading_font, 14)
add_text("john.doe@example.com | (555) 123-4567 | linkedin.com/in/johndoe", 1*inch, 9.4*inch)

# Summary
add_text("Summary", 1*inch, 8.9*inch, heading_font, 14)
add_text("Experienced software engineer with 5+ years in backend development", 1*inch, 8.6*inch)
add_text("specializing in Python, FastAPI, and cloud technologies.", 1*inch, 8.4*inch)

# Skills
add_text("Skills", 1*inch, 7.9*inch, heading_font, 14)
add_text("• Languages: Python, JavaScript, SQL, TypeScript", 1*inch, 7.6*inch)
add_text("• Frameworks: FastAPI, Django, Flask, React", 1*inch, 7.4*inch)
add_text("• Cloud: AWS, Docker, Kubernetes", 1*inch, 7.2*inch)
add_text("• Databases: PostgreSQL, MongoDB", 1*inch, 7.0*inch)
add_text("• AI/ML: CrewAI, LangChain, TensorFlow", 1*inch, 6.8*inch)

# Experience
add_text("Experience", 1*inch, 6.3*inch, heading_font, 14)
add_text("Senior Software Engineer | TechCorp Inc. | 2022-Present", 1*inch, 6.0*inch, heading_font, 12)
add_text("• Developed and maintained microservices using FastAPI and Python", 1*inch, 5.8*inch)
add_text("• Implemented CI/CD pipelines reducing deployment time by 40%", 1*inch, 5.6*inch)
add_text("• Led a team of 3 developers in building a document processing system", 1*inch, 5.4*inch)

add_text("Software Engineer | Innovate Solutions | 2020-2022", 1*inch, 5.0*inch, heading_font, 12)
add_text("• Built RESTful APIs using Flask and PostgreSQL", 1*inch, 4.8*inch)
add_text("• Migrated monolithic application to microservices architecture", 1*inch, 4.6*inch)
add_text("• Optimized database queries resulting in 30% performance improvement", 1*inch, 4.4*inch)

# Education
add_text("Education", 1*inch, 3.9*inch, heading_font, 14)
add_text("Bachelor of Science in Computer Science", 1*inch, 3.6*inch, heading_font, 12)
add_text("University of Technology, 2020", 1*inch, 3.4*inch)

# Save the PDF
c.save()

print(f"Successfully created test PDF resume at: {pdf_path}")
print("You can now use this file to test the Resume Customizer application.")
print("\nExample command:")
print(f"curl -X POST -F \"resume=@{pdf_path}\" http://127.0.0.1:8000/api/resumes/upload")
