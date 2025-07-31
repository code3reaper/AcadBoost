import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_teacher_courses, get_assignments, get_submissions,
    create_assignment, update_assignment, delete_assignment, grade_submission
)

@role_required(["teacher"])
def show_teacher_assignments():
    """Show the assignments page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("Assignment Management", "Create and manage assignments for your courses")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Create tabs for different assignment functions
    tab1, tab2, tab3 = st.tabs([
        "Create Assignment", 
        "Manage Assignments", 
        "Grade Submissions"
    ])
    
    with tab1:
        show_create_assignment(courses)
    
    with tab2:
        show_manage_assignments(courses)
    
    with tab3:
        show_grade_submissions(courses)

def show_create_assignment(courses):
    """Show interface for creating assignments."""
    st.markdown("### Create New Assignment")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="create_course"
    )
    
    if course_id:
        with st.form("create_assignment_form"):
            title = st.text_input("Assignment Title")
            description = st.text_area("Description")
            
            col1, col2 = st.columns(2)
            
            with col1:
                due_date = st.date_input(
                    "Due Date",
                    value=datetime.now().date() + timedelta(days=7)
                )
            
            with col2:
                max_points = st.number_input(
                    "Maximum Points",
                    min_value=1,
                    max_value=100,
                    value=100
                )
            
            submit = st.form_submit_button("Create Assignment")
            
            if submit:
                if not title:
                    show_notification("Please enter a title for the assignment.", "error")
                else:
                    # Format due date
                    due_date_str = due_date.isoformat()
                    
                    # Create assignment
                    success, message, assignment_id = create_assignment(
                        course_id=course_id,
                        title=title,
                        description=description,
                        due_date=due_date_str,
                        max_points=max_points
                    )
                    
                    if success:
                        show_notification(message, "success")
                    else:
                        show_notification(message, "error")

def show_manage_assignments(courses):
    """Show interface for managing assignments."""
    st.markdown("### Manage Assignments")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="manage_course"
    )
    
    if course_id:
        # Get assignments for this course
        assignments = get_assignments().get(course_id, [])
        
        if not assignments:
            st.info("No assignments found for this course. Create an assignment first.")
            return
        
        # Show assignments
        for i, assignment in enumerate(assignments):
            assignment_id = assignment.get("assignment_id")
            
            with st.expander(f"{assignment.get('title', 'No Title')} - Due: {assignment.get('due_date', 'No Date')}"):
                # Assignment details
                st.markdown(f"**Description:** {assignment.get('description', 'No description')}")
                st.markdown(f"**Maximum Points:** {assignment.get('max_points', 100)}")
                st.markdown(f"**Created At:** {format_datetime(assignment.get('created_at', ''))}")
                
                # Edit assignment form
                with st.form(f"edit_assignment_form_{i}"):
                    st.markdown("### Edit Assignment")
                    
                    title = st.text_input("Title", value=assignment.get("title", ""))
                    description = st.text_area("Description", value=assignment.get("description", ""))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        try:
                            current_due_date = datetime.fromisoformat(assignment.get("due_date", "")).date()
                        except:
                            current_due_date = datetime.now().date() + timedelta(days=7)
                        
                        due_date = st.date_input("Due Date", value=current_due_date)
                    
                    with col2:
                        max_points = st.number_input(
                            "Maximum Points",
                            min_value=1,
                            max_value=100,
                            value=assignment.get("max_points", 100)
                        )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        update = st.form_submit_button("Update Assignment")
                    
                    with col2:
                        delete = st.form_submit_button("Delete Assignment")
                    
                    if update:
                        if not title:
                            show_notification("Please enter a title for the assignment.", "error")
                        else:
                            # Format due date
                            due_date_str = due_date.isoformat()
                            
                            # Update assignment
                            success, message = update_assignment(
                                course_id=course_id,
                                assignment_id=assignment_id,
                                title=title,
                                description=description,
                                due_date=due_date_str,
                                max_points=max_points
                            )
                            
                            if success:
                                show_notification(message, "success")
                                st.rerun()
                            else:
                                show_notification(message, "error")
                    
                    elif delete:
                        # Delete assignment
                        success, message = delete_assignment(
                            course_id=course_id,
                            assignment_id=assignment_id
                        )
                        
                        if success:
                            show_notification(message, "success")
                            st.rerun()
                        else:
                            show_notification(message, "error")
                
                # Show submissions
                submissions = get_submissions().get(assignment_id, [])
                
                st.markdown(f"### Submissions ({len(submissions)})")
                
                if submissions:
                    # Prepare submission data
                    submission_data = []
                    
                    for submission in submissions:
                        submission_data.append({
                            "Student": submission.get("student_email", "Unknown"),
                            "Submitted At": format_datetime(submission.get("submitted_at", "")),
                            "Grade": submission.get("grade", "Not graded"),
                            "Feedback": submission.get("feedback", "No feedback")
                        })
                    
                    # Show submission table
                    show_data_table(submission_data)
                else:
                    st.info("No submissions for this assignment yet.")

def show_grade_submissions(courses):
    """Show interface for grading submissions."""
    st.markdown("### Grade Submissions")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="grade_course"
    )
    
    if course_id:
        # Get assignments for this course
        assignments = get_assignments().get(course_id, [])
        
        if not assignments:
            st.info("No assignments found for this course. Create an assignment first.")
            return
        
        # Select assignment
        assignment_options = [(a.get("assignment_id"), f"{a.get('title', 'No Title')} - Due: {a.get('due_date', 'No Date')}") for a in assignments]
        
        selected_assignment_id = st.selectbox(
            "Select Assignment",
            options=[option[0] for option in assignment_options],
            format_func=lambda x: next((option[1] for option in assignment_options if option[0] == x), x)
        )
        
        if selected_assignment_id:
            # Get assignment details
            assignment = next((a for a in assignments if a.get("assignment_id") == selected_assignment_id), {})
            
            # Get submissions for this assignment
            submissions = get_submissions().get(selected_assignment_id, [])
            
            if not submissions:
                st.info("No submissions for this assignment yet.")
                return
            
            # Show assignment details
            st.markdown(f"**Assignment:** {assignment.get('title', 'No Title')}")
            st.markdown(f"**Description:** {assignment.get('description', 'No description')}")
            st.markdown(f"**Due Date:** {assignment.get('due_date', 'No Date')}")
            st.markdown(f"**Maximum Points:** {assignment.get('max_points', 100)}")
            
            # Create tabs for each submission
            tabs = st.tabs([f"Student: {s.get('student_email', 'Unknown')}" for s in submissions])
            
            for i, (tab, submission) in enumerate(zip(tabs, submissions)):
                with tab:
                    student_email = submission.get("student_email", "Unknown")
                    
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
                            max_value=assignment.get("max_points", 100),
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
                                assignment_id=selected_assignment_id,
                                student_email=student_email,
                                grade=grade,
                                feedback=feedback
                            )
                            
                            if success:
                                show_notification(message, "success")
                            else:
                                show_notification(message, "error") 