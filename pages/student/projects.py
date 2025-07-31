import streamlit as st
from datetime import datetime
import os

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_projects, get_submissions,
    submit_project, get_student_submissions
)

@role_required(["student"])
def show_student_projects():
    """Show the projects page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Projects", "View and submit projects")
    
    # Create tabs for different project views
    tab1, tab2 = st.tabs(["Pending Projects", "Submitted Projects"])
    
    with tab1:
        show_pending_projects(email)
    
    with tab2:
        show_submitted_projects(email)

def show_pending_projects(email):
    """Show pending projects for the student."""
    st.markdown("### Pending Projects")
    
    # Get all courses
    courses = get_courses()
    
    # Get all projects
    all_projects = get_projects()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    # Find pending projects (not submitted yet)
    pending_projects = []
    
    for course_id, course_projects in all_projects.items():
        course_name = courses.get(course_id, {}).get("course_name", "Unknown Course")
        
        for project in course_projects:
            project_id = project.get("project_id")
            
            # Check if the project is already submitted
            is_submitted = False
            for submission in student_submissions:
                if submission.get("assignment_id") == project_id:
                    is_submitted = True
                    break
            
            if not is_submitted:
                # Add to pending projects
                pending_projects.append({
                    "course_id": course_id,
                    "course_name": course_name,
                    "project_id": project_id,
                    "title": project.get("title", "No Title"),
                    "description": project.get("description", "No Description"),
                    "due_date": project.get("due_date", ""),
                    "max_points": project.get("max_points", 100),
                    "group_project": project.get("group_project", False)
                })
    
    if not pending_projects:
        st.info("You have no pending projects.")
        return
    
    # Sort by due date (earliest first)
    pending_projects.sort(key=lambda x: x["due_date"])
    
    # Display pending projects
    for i, project in enumerate(pending_projects):
        with st.expander(f"{project['course_name']} - {project['title']} (Due: {format_date(project['due_date'])})"):
            st.markdown(f"**Course:** {project['course_name']} ({project['course_id']})")
            st.markdown(f"**Title:** {project['title']}")
            st.markdown(f"**Description:** {project['description']}")
            st.markdown(f"**Due Date:** {format_date(project['due_date'])}")
            st.markdown(f"**Maximum Points:** {project['max_points']}")
            st.markdown(f"**Group Project:** {'Yes' if project['group_project'] else 'No'}")
            
            # Submission form
            with st.form(f"submit_project_form_{i}"):
                st.markdown("### Submit Project")
                
                submission_text = st.text_area("Your Answer", height=200)
                
                uploaded_file = st.file_uploader("Upload File (Optional)", key=f"file_upload_{i}")
                
                # Group members (if group project)
                group_members = []
                if project['group_project']:
                    st.markdown("### Group Members")
                    st.markdown("Enter the email addresses of your group members (one per line):")
                    
                    group_members_text = st.text_area("Group Members", height=100)
                    
                    if group_members_text:
                        # Split by newline and remove empty lines
                        group_members = [
                            member.strip() 
                            for member in group_members_text.split("\n") 
                            if member.strip()
                        ]
                
                submit = st.form_submit_button("Submit Project")
                
                if submit:
                    if not submission_text and not uploaded_file:
                        show_notification("Please provide either text or a file for your submission.", "error")
                    else:
                        # Handle file upload
                        file_path = None
                        if uploaded_file:
                            # Create directory for uploads if it doesn't exist
                            upload_dir = os.path.join("data", "uploads")
                            os.makedirs(upload_dir, exist_ok=True)
                            
                            # Save file
                            file_path = os.path.join(upload_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                        
                        # Submit project
                        success, message = submit_project(
                            project_id=project["project_id"],
                            student_email=email,
                            submission_text=submission_text,
                            file_path=file_path,
                            group_members=group_members if project['group_project'] else None
                        )
                        
                        if success:
                            show_notification(message, "success")
                            st.rerun()
                        else:
                            show_notification(message, "error")

def show_submitted_projects(email):
    """Show submitted projects for the student."""
    st.markdown("### Submitted Projects")
    
    # Get all courses
    courses = get_courses()
    
    # Get all projects
    all_projects = get_projects()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    if not student_submissions:
        st.info("You have not submitted any projects yet.")
        return
    
    # Prepare data for display
    submission_data = []
    
    for submission in student_submissions:
        assignment_id = submission.get("assignment_id")
        
        # Check if this is a project (not an assignment)
        is_project = False
        project_details = None
        course_id = None
        course_name = "Unknown Course"
        
        for c_id, c_projects in all_projects.items():
            for project in c_projects:
                if project.get("project_id") == assignment_id:
                    is_project = True
                    project_details = project
                    course_id = c_id
                    course_name = courses.get(c_id, {}).get("course_name", "Unknown Course")
                    break
            if is_project:
                break
        
        if is_project and project_details:
            submission_data.append({
                "course_id": course_id,
                "course_name": course_name,
                "project_id": assignment_id,
                "title": project_details.get("title", "No Title"),
                "due_date": project_details.get("due_date", ""),
                "max_points": project_details.get("max_points", 100),
                "group_project": project_details.get("group_project", False),
                "submitted_at": submission.get("submitted_at", ""),
                "grade": submission.get("grade", "Not graded yet"),
                "feedback": submission.get("feedback", "No feedback yet"),
                "submission_text": submission.get("submission_text", ""),
                "file_path": submission.get("file_path", None),
                "group_members": submission.get("group_members", [])
            })
    
    if not submission_data:
        st.info("You have not submitted any projects yet.")
        return
    
    # Sort by submission date (newest first)
    submission_data.sort(key=lambda x: x["submitted_at"], reverse=True)
    
    # Display submitted projects
    for submission in submission_data:
        with st.expander(f"{submission['course_name']} - {submission['title']} (Submitted: {format_datetime(submission['submitted_at'])})"):
            st.markdown(f"**Course:** {submission['course_name']} ({submission['course_id']})")
            st.markdown(f"**Title:** {submission['title']}")
            st.markdown(f"**Due Date:** {format_date(submission['due_date'])}")
            st.markdown(f"**Submitted At:** {format_datetime(submission['submitted_at'])}")
            
            # Show group members if any
            if submission['group_project'] and submission['group_members']:
                st.markdown(f"**Group Members:** {', '.join(submission['group_members'])}")
            
            # Show grade if available
            if submission['grade'] != "Not graded yet" and submission['grade'] is not None:
                grade = submission['grade']
                max_points = submission['max_points']
                percentage = (grade / max_points) * 100 if max_points > 0 else 0
                st.markdown(f"**Grade:** {grade} / {max_points} ({percentage:.2f}%)")
                st.markdown(f"**Feedback:** {submission['feedback']}")
            else:
                st.info("This submission has not been graded yet.")
            
            # Show submission details
            st.markdown("### Your Submission")
            st.text_area(
                "Submission Text",
                value=submission["submission_text"],
                height=200,
                disabled=True
            )
            
            if submission["file_path"]:
                st.markdown(f"**Uploaded File:** {os.path.basename(submission['file_path'])}") 