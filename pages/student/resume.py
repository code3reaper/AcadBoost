import streamlit as st
import os
import base64
import json
import pandas as pd
from datetime import datetime
import sys

# Add parent directory to path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.auth import role_required, get_user_by_email, update_user, get_current_user, get_user_data
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import get_student_submissions
from utils.ai_analysis import show_resume_analysis_section, analyze_resume_with_gemini
from utils.resume_generator import resume_form, generate_latex_resume

@role_required(["student"])
def show_student_resume():
    """Show the resume page for students."""
    # Get current user from session state
    user = st.session_state.user
    email = user.get("email", "")
    
    show_header("My Resume", "Upload, manage, and create professional resumes")
    
    # Create tabs
    tabs = st.tabs(["Upload Resume", "Create Resume", "AI Resume Analysis"])
    
    with tabs[0]:
        show_resume_upload(user)
    
    with tabs[1]:
        show_resume_creation(user)
    
    with tabs[2]:
        show_resume_analysis(user)

def show_resume_upload(user):
    """Show resume upload section."""
    st.markdown("### Upload Your Resume")
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads", "resumes")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Check if user already has a resume
    email = user["email"]
    resume_path = os.path.join(upload_dir, f"{email.replace('@', '_').replace('.', '_')}_resume.pdf")
    resume_exists = os.path.exists(resume_path)
    
    if resume_exists:
        st.success("You have already uploaded a resume.")
        
        # Show preview
        try:
            with open(resume_path, "rb") as file:
                base64_pdf = base64.b64encode(file.read()).decode('utf-8')
            
            # Display PDF
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # Show the resume preview
            if resume_path and os.path.exists(resume_path):
                with open(resume_path, "rb") as file:
                    st.download_button(
                        label="Download Resume",
                        data=file,
                        file_name=os.path.basename(resume_path),
                        mime="application/pdf",
                        key="download_existing_resume"
                    )
        except Exception as e:
            st.error(f"Error displaying resume: {str(e)}")
        
        # Option to replace
        st.markdown("### Replace Resume")
        
        uploaded_file = st.file_uploader("Upload a new resume (PDF)", type=["pdf"], key="replace_resume")
        
        if uploaded_file is not None:
            try:
                # Save file
                with open(resume_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success("Resume replaced successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving resume: {str(e)}")
    else:
        st.info("You haven't uploaded a resume yet.")
        
        uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="new_resume")
        
        if uploaded_file is not None:
            try:
                # Save file
                with open(resume_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success("Resume uploaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving resume: {str(e)}")

def show_resume_creation(user):
    """
    Show the resume creation section.
    """
    st.header("Create Professional Resume")
    st.write("Fill out the form below to generate a professional LaTeX resume.")
    
    # Check if user already has a resume
    email = user["email"]
    resume_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              "data", "generated", "resumes", 
                              f"{email.replace('@', '_').replace('.', '_')}_resume.pdf")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(resume_path), exist_ok=True)
    
    # Initialize session state variables if they don't exist
    if "resume_generated" not in st.session_state:
        st.session_state.resume_generated = False
    if "resume_pdf_path" not in st.session_state:
        st.session_state.resume_pdf_path = None
    if "show_resume_form" not in st.session_state:
        st.session_state.show_resume_form = not os.path.exists(resume_path)
    
    # Display existing resume if available
    if os.path.exists(resume_path) and not st.session_state.show_resume_form:
        st.success("You already have a generated resume.")
        
        # Display the resume
        with open(resume_path, "rb") as file:
            pdf_bytes = file.read()
        
        # Create download button (outside form)
        st.download_button(
            label="Download Your Resume",
            data=pdf_bytes,
            file_name=f"{user['name']}_resume.pdf",
            mime="application/pdf",
            key="download_generated_resume"
        )
        
        # Display PDF preview
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Option to create a new resume
        if st.button("Create New Resume", key="create_new_resume"):
            st.session_state.show_resume_form = True
            st.rerun()
    
    # Display newly generated resume if available
    elif st.session_state.resume_generated and st.session_state.resume_pdf_path:
        st.success("Resume generated successfully!")
        
        # Display the resume
        with open(st.session_state.resume_pdf_path, "rb") as file:
            pdf_bytes = file.read()
        
        # Create download button (outside form)
        st.download_button(
            label="Download Your Resume",
            data=pdf_bytes,
            file_name=f"{user['name']}_resume.pdf",
            mime="application/pdf",
            key="download_new_resume"
        )
        
        # Display PDF preview
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Option to create another resume
        if st.button("Create Another Resume", key="create_another_resume"):
            st.session_state.show_resume_form = True
            st.session_state.resume_generated = False
            st.rerun()
    
    # Show resume form
    if st.session_state.show_resume_form:
        with st.form("resume_form"):
            # Pre-fill some fields with user data
            user_data = user.copy()  # Use the current user data directly
            
            # Create form for resume data
            st.write("### Personal Information")
            resume_data = {
                "name": st.text_input("Full Name", value=user_data.get("name", "")),
                "email": st.text_input("Email", value=user_data.get("email", "")),
                "phone": st.text_input("Phone Number", value=user_data.get("phone", "")),
                "location": st.text_input("Location", value=user_data.get("location", "")),
                "website": st.text_input("Website (optional)"),
                "linkedin": st.text_input("LinkedIn Username (optional)"),
                "github": st.text_input("GitHub Username (optional)"),
                "education": [],
                "experience": [],
                "projects": [],
                "skills": {}
            }
            
            # Education section
            st.write("### Education")
            num_education = st.number_input("Number of Education Entries", min_value=1, max_value=3, value=1)
            
            for i in range(num_education):
                st.write(f"#### Education #{i+1}")
                education = {
                    "period": st.text_input(f"Period (e.g., Sept 2020 - May 2024)", key=f"edu_period_{i}"),
                    "institution": st.text_input(f"Institution", key=f"edu_inst_{i}"),
                    "degree": st.text_input(f"Degree", key=f"edu_degree_{i}"),
                    "gpa": st.text_input(f"GPA (optional)", key=f"edu_gpa_{i}"),
                    "coursework": st.text_input(f"Relevant Coursework (optional)", key=f"edu_course_{i}")
                }
                resume_data["education"].append(education)
            
            # Experience section
            st.write("### Experience")
            num_experience = st.number_input("Number of Experience Entries", min_value=0, max_value=3, value=1)
            
            for i in range(num_experience):
                st.write(f"#### Experience #{i+1}")
                experience = {
                    "period": st.text_input(f"Period (e.g., June 2023 - Aug 2023)", key=f"exp_period_{i}"),
                    "title": st.text_input(f"Job Title", key=f"exp_title_{i}"),
                    "company": st.text_input(f"Company", key=f"exp_company_{i}"),
                    "location": st.text_input(f"Location (optional)", key=f"exp_location_{i}"),
                    "highlights": []
                }
                
                num_highlights = st.number_input(f"Number of Bullet Points", min_value=1, max_value=5, value=2, key=f"exp_num_high_{i}")
                for j in range(num_highlights):
                    highlight = st.text_input(f"Bullet Point #{j+1}", key=f"exp_high_{i}_{j}")
                    if highlight:
                        experience["highlights"].append(highlight)
                
                resume_data["experience"].append(experience)
            
            # Projects section
            st.write("### Projects")
            num_projects = st.number_input("Number of Project Entries", min_value=0, max_value=3, value=1)
            
            for i in range(num_projects):
                st.write(f"#### Project #{i+1}")
                project = {
                    "title": st.text_input(f"Project Title", key=f"proj_title_{i}"),
                    "link": st.text_input(f"Project Link (optional)", key=f"proj_link_{i}"),
                    "highlights": []
                }
                
                num_highlights = st.number_input(f"Number of Bullet Points", min_value=1, max_value=5, value=2, key=f"proj_num_high_{i}")
                for j in range(num_highlights):
                    highlight = st.text_input(f"Bullet Point #{j+1}", key=f"proj_high_{i}_{j}")
                    if highlight:
                        project["highlights"].append(highlight)
                
                resume_data["projects"].append(project)
            
            # Skills section
            st.write("### Skills")
            num_skill_categories = st.number_input("Number of Skill Categories", min_value=1, max_value=3, value=1)
            
            for i in range(num_skill_categories):
                category = st.text_input(f"Skill Category #{i+1} (e.g., Languages, Technologies)", key=f"skill_cat_{i}")
                if category:
                    skills = st.text_input(f"Skills for {category} (comma-separated)", key=f"skill_list_{i}")
                    if skills:
                        resume_data["skills"][category] = [skill.strip() for skill in skills.split(",")]
            
            # Submit button
            submit_button = st.form_submit_button("Generate Resume")
            
            if submit_button:
                # Validate required fields
                if not resume_data["name"] or not resume_data["email"]:
                    st.error("Name and email are required fields.")
                    return
                
                # Generate resume
                with st.spinner("Generating resume..."):
                    try:
                        # Generate resume using our utility function
                        # The function now handles LaTeX detection internally
                        output_file = generate_latex_resume(resume_data)
                        
                        if output_file and os.path.exists(output_file):
                            # Store the path in session state for display outside the form
                            st.session_state.resume_pdf_path = output_file
                            st.session_state.resume_generated = True
                            st.session_state.show_resume_form = False
                            st.rerun()
                        else:
                            st.error("Failed to generate resume. Please check your inputs and try again.")
                    except Exception as e:
                        st.error(f"Error generating resume: {str(e)}")
                        st.error("Please make sure LaTeX is installed correctly on your system.")
                        st.info("You can run the install_dependencies.py script to check your LaTeX installation.")

def show_resume_analysis(user):
    """Show resume analysis section."""
    st.markdown("### Resume Analysis")
    
    # Check if user has a resume
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads", "resumes")
    resume_path = os.path.join(upload_dir, f"{user['email'].replace('@', '_').replace('.', '_')}_resume.pdf")
    
    if not os.path.exists(resume_path):
        st.warning("Please upload a resume first before requesting analysis.")
        return
    
    # Show AI analysis section
    show_resume_analysis_section(resume_path) 