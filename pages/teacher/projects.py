import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_teacher_courses, get_projects, get_submissions,
    create_project, grade_submission
)

@role_required(["teacher"])
def show_teacher_projects():
    """Show the projects page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("Project Management", "Create and manage projects for your courses")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Create tabs for different project functions
    tab1, tab2, tab3 = st.tabs([
        "Create Project", 
        "Manage Projects", 
        "Grade Submissions"
    ])
    
    with tab1:
        show_create_project(courses)
    
    with tab2:
        show_manage_projects(courses)
    
    with tab3:
        show_grade_project_submissions(courses)

def show_create_project(courses):
    """Show interface for creating projects."""
    st.markdown("### Create New Project")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="create_course"
    )
    
    if course_id:
        with st.form("create_project_form"):
            title = st.text_input("Project Title")
            description = st.text_area("Description")
            
            col1, col2 = st.columns(2)
            
            with col1:
                due_date = st.date_input(
                    "Due Date",
                    value=datetime.now().date() + timedelta(days=14)
                )
            
            with col2:
                max_points = st.number_input(
                    "Maximum Points",
                    min_value=1,
                    max_value=100,
                    value=100
                )
            
            group_project = st.checkbox("Group Project")
            
            submit = st.form_submit_button("Create Project")
            
            if submit:
                if not title:
                    show_notification("Please enter a title for the project.", "error")
                else:
                    # Format due date
                    due_date_str = due_date.isoformat()
                    
                    # Create project
                    success, message, project_id = create_project(
                        course_id=course_id,
                        title=title,
                        description=description,
                        due_date=due_date_str,
                        max_points=max_points,
                        group_project=group_project
                    )
                    
                    if success:
                        show_notification(message, "success")
                    else:
                        show_notification(message, "error")

def show_manage_projects(courses):
    """Show interface for managing projects."""
    st.markdown("### Manage Projects")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="manage_course"
    )
    
    if course_id:
        # Get projects for this course
        projects = get_projects().get(course_id, [])
        
        if not projects:
            st.info("No projects found for this course. Create a project first.")
            return
        
        # Show projects
        for i, project in enumerate(projects):
            project_id = project.get("project_id")
            
            with st.expander(f"{project.get('title', 'No Title')} - Due: {project.get('due_date', 'No Date')}"):
                # Project details
                st.markdown(f"**Description:** {project.get('description', 'No description')}")
                st.markdown(f"**Maximum Points:** {project.get('max_points', 100)}")
                st.markdown(f"**Group Project:** {'Yes' if project.get('group_project', False) else 'No'}")
                st.markdown(f"**Created At:** {format_datetime(project.get('created_at', ''))}")
                
                # Edit project form
                with st.form(f"edit_project_form_{i}"):
                    st.markdown("### Edit Project")
                    
                    title = st.text_input("Title", value=project.get("title", ""))
                    description = st.text_area("Description", value=project.get("description", ""))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        try:
                            current_due_date = datetime.fromisoformat(project.get("due_date", "")).date()
                        except:
                            current_due_date = datetime.now().date() + timedelta(days=14)
                        
                        due_date = st.date_input("Due Date", value=current_due_date)
                    
                    with col2:
                        max_points = st.number_input(
                            "Maximum Points",
                            min_value=1,
                            max_value=100,
                            value=project.get("max_points", 100)
                        )
                    
                    group_project = st.checkbox("Group Project", value=project.get("group_project", False))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        update = st.form_submit_button("Update Project")
                    
                    with col2:
                        delete = st.form_submit_button("Delete Project")
                    
                    if update:
                        if not title:
                            show_notification("Please enter a title for the project.", "error")
                        else:
                            # Format due date
                            due_date_str = due_date.isoformat()
                            
                            # Update project
                            from utils.database import update_assignment
                            success, message = update_assignment(
                                course_id=course_id,
                                assignment_id=project_id,
                                title=title,
                                description=description,
                                due_date=due_date_str,
                                max_points=max_points,
                                group_project=group_project
                            )
                            
                            if success:
                                show_notification(message, "success")
                                st.rerun()
                            else:
                                show_notification(message, "error")
                    
                    elif delete:
                        # Delete project
                        from utils.database import delete_assignment
                        success, message = delete_assignment(
                            course_id=course_id,
                            assignment_id=project_id
                        )
                        
                        if success:
                            show_notification(message, "success")
                            st.rerun()
                        else:
                            show_notification(message, "error")
                
                # Show submissions
                submissions = get_submissions().get(project_id, [])
                
                st.markdown(f"### Submissions ({len(submissions)})")
                
                if submissions:
                    # Prepare submission data
                    submission_data = []
                    
                    for submission in submissions:
                        # Get group members if any
                        group_members = submission.get("group_members", [])
                        group_members_str = ", ".join(group_members) if group_members else "Individual Project"
                        
                        submission_data.append({
                            "Student": submission.get("student_email", "Unknown"),
                            "Group Members": group_members_str,
                            "Submitted At": format_datetime(submission.get("submitted_at", "")),
                            "Grade": submission.get("grade", "Not graded"),
                            "Feedback": submission.get("feedback", "No feedback")
                        })
                    
                    # Show submission table
                    show_data_table(submission_data)
                else:
                    st.info("No submissions for this project yet.")

def show_grade_project_submissions(courses):
    """Show interface for grading project submissions."""
    st.markdown("### Grade Project Submissions")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="grade_course"
    )
    
    if course_id:
        # Get projects for this course
        projects = get_projects().get(course_id, [])
        
        if not projects:
            st.info("No projects found for this course. Create a project first.")
            return
        
        # Select project
        project_options = [(p.get("project_id"), f"{p.get('title', 'No Title')} - Due: {p.get('due_date', 'No Date')}") for p in projects]
        
        selected_project_id = st.selectbox(
            "Select Project",
            options=[option[0] for option in project_options],
            format_func=lambda x: next((option[1] for option in project_options if option[0] == x), x)
        )
        
        if selected_project_id:
            # Get project details
            project = next((p for p in projects if p.get("project_id") == selected_project_id), {})
            
            # Get submissions for this project
            submissions = get_submissions().get(selected_project_id, [])
            
            if not submissions:
                st.info("No submissions for this project yet.")
                return
            
            # Show project details
            st.markdown(f"**Project:** {project.get('title', 'No Title')}")
            st.markdown(f"**Description:** {project.get('description', 'No description')}")
            st.markdown(f"**Due Date:** {project.get('due_date', 'No Date')}")
            st.markdown(f"**Maximum Points:** {project.get('max_points', 100)}")
            st.markdown(f"**Group Project:** {'Yes' if project.get('group_project', False) else 'No'}")
            
            # Create tabs for each submission
            tabs = st.tabs([f"Student: {s.get('student_email', 'Unknown')}" for s in submissions])
            
            for i, (tab, submission) in enumerate(zip(tabs, submissions)):
                with tab:
                    student_email = submission.get("student_email", "Unknown")
                    
                    # Show group members if any
                    group_members = submission.get("group_members", [])
                    if group_members:
                        st.markdown(f"**Group Members:** {', '.join(group_members)}")
                    
                    st.markdown(f"**Submission Text:**")
                    st.text_area(
                        "Submission",
                        value=submission.get("submission_text", "No text"),
                        height=200,
                        key=f"submission_text_{i}",
                        disabled=True
                    )
                    
                    if submission.get("file_path"):
                        st.markdown(f"**File:** {submission.get('file_path')}")
                    
                    st.markdown(f"**Submitted At:** {format_datetime(submission.get('submitted_at', ''))}")
                    
                    # Grading form
                    with st.form(f"grade_form_{i}"):
                        current_grade = submission.get("grade")
                        current_feedback = submission.get("feedback", "")
                        
                        grade = st.number_input(
                            "Grade",
                            min_value=0,
                            max_value=project.get("max_points", 100),
                            value=current_grade if current_grade is not None else 0,
                            key=f"grade_input_{i}"
                        )
                        
                        feedback = st.text_area(
                            "Feedback",
                            value=current_feedback,
                            key=f"feedback_input_{i}"
                        )
                        
                        submit = st.form_submit_button("Submit Grade")
                        
                        if submit:
                            # Grade submission
                            success, message = grade_submission(
                                assignment_id=selected_project_id,
                                student_email=student_email,
                                grade=grade,
                                feedback=feedback
                            )
                            
                            if success:
                                show_notification(message, "success")
                            else:
                                show_notification(message, "error") 