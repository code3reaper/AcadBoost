import streamlit as st
from datetime import datetime
import os

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_assignments, get_submissions,
    submit_assignment, get_student_submissions
)

@role_required(["student"])
def show_student_assignments():
    """Show the assignments page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Assignments", "View and submit assignments")
    
    # Create tabs for different assignment views
    tab1, tab2 = st.tabs(["Pending Assignments", "Submitted Assignments"])
    
    with tab1:
        show_pending_assignments(email)
    
    with tab2:
        show_submitted_assignments(email)

def show_pending_assignments(email):
    """Show pending assignments for the student."""
    st.markdown("### Pending Assignments")
    
    # Get all courses
    courses = get_courses()
    
    # Get all assignments
    all_assignments = get_assignments()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    # Find pending assignments (not submitted yet)
    pending_assignments = []
    
    for course_id, course_assignments in all_assignments.items():
        course_name = courses.get(course_id, {}).get("course_name", "Unknown Course")
        
        for assignment in course_assignments:
            assignment_id = assignment.get("assignment_id")
            
            # Check if the assignment is already submitted
            is_submitted = False
            for submission in student_submissions:
                if submission.get("assignment_id") == assignment_id:
                    is_submitted = True
                    break
            
            if not is_submitted:
                # Add to pending assignments
                pending_assignments.append({
                    "course_id": course_id,
                    "course_name": course_name,
                    "assignment_id": assignment_id,
                    "title": assignment.get("title", "No Title"),
                    "description": assignment.get("description", "No Description"),
                    "due_date": assignment.get("due_date", ""),
                    "max_points": assignment.get("max_points", 100)
                })
    
    if not pending_assignments:
        st.info("You have no pending assignments.")
        return
    
    # Sort by due date (earliest first)
    pending_assignments.sort(key=lambda x: x["due_date"])
    
    # Display pending assignments
    for i, assignment in enumerate(pending_assignments):
        with st.expander(f"{assignment['course_name']} - {assignment['title']} (Due: {format_date(assignment['due_date'])})"):
            st.markdown(f"**Course:** {assignment['course_name']} ({assignment['course_id']})")
            st.markdown(f"**Title:** {assignment['title']}")
            st.markdown(f"**Description:** {assignment['description']}")
            st.markdown(f"**Due Date:** {format_date(assignment['due_date'])}")
            st.markdown(f"**Maximum Points:** {assignment['max_points']}")
            
            # Submission form
            with st.form(f"submit_assignment_form_{i}"):
                st.markdown("### Submit Assignment")
                
                submission_text = st.text_area("Your Answer", height=200)
                
                uploaded_file = st.file_uploader("Upload File (Optional)", key=f"file_upload_{i}")
                
                submit = st.form_submit_button("Submit Assignment")
                
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
                        
                        # Submit assignment
                        success, message = submit_assignment(
                            assignment_id=assignment["assignment_id"],
                            student_email=email,
                            submission_text=submission_text,
                            file_path=file_path
                        )
                        
                        if success:
                            show_notification(message, "success")
                            st.rerun()
                        else:
                            show_notification(message, "error")

def show_submitted_assignments(email):
    """Show submitted assignments for the student."""
    st.markdown("### Submitted Assignments")
    
    # Get all courses
    courses = get_courses()
    
    # Get all assignments
    all_assignments = get_assignments()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    if not student_submissions:
        st.info("You have not submitted any assignments yet.")
        return
    
    # Prepare data for display
    submission_data = []
    
    for submission in student_submissions:
        assignment_id = submission.get("assignment_id")
        
        # Find the assignment details
        assignment_details = None
        course_id = None
        course_name = "Unknown Course"
        
        for c_id, c_assignments in all_assignments.items():
            for assignment in c_assignments:
                if assignment.get("assignment_id") == assignment_id:
                    assignment_details = assignment
                    course_id = c_id
                    course_name = courses.get(c_id, {}).get("course_name", "Unknown Course")
                    break
            if assignment_details:
                break
        
        if assignment_details:
            submission_data.append({
                "course_id": course_id,
                "course_name": course_name,
                "assignment_id": assignment_id,
                "title": assignment_details.get("title", "No Title"),
                "due_date": assignment_details.get("due_date", ""),
                "max_points": assignment_details.get("max_points", 100),
                "submitted_at": submission.get("submitted_at", ""),
                "grade": submission.get("grade", "Not graded yet"),
                "feedback": submission.get("feedback", "No feedback yet"),
                "submission_text": submission.get("submission_text", ""),
                "file_path": submission.get("file_path", None)
            })
    
    # Sort by submission date (newest first)
    submission_data.sort(key=lambda x: x["submitted_at"], reverse=True)
    
    # Display submitted assignments
    for submission in submission_data:
        with st.expander(f"{submission['course_name']} - {submission['title']} (Submitted: {format_datetime(submission['submitted_at'])})"):
            st.markdown(f"**Course:** {submission['course_name']} ({submission['course_id']})")
            st.markdown(f"**Title:** {submission['title']}")
            st.markdown(f"**Due Date:** {format_date(submission['due_date'])}")
            st.markdown(f"**Submitted At:** {format_datetime(submission['submitted_at'])}")
            
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