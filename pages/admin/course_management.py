import streamlit as st
import pandas as pd
from datetime import datetime

from utils.auth import role_required, get_users
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_datetime
)
from utils.database import (
    get_courses, add_course, update_course, delete_course,
    get_assignments, get_attendance
)

@role_required(["admin"])
def show_course_management():
    """Show the course management page for administrators."""
    show_header("Course Management", "Manage courses in the system")
    
    # Create tabs for different course management functions
    tab1, tab2, tab3 = st.tabs(["All Courses", "Add Course", "Edit/Delete Course"])
    
    with tab1:
        show_all_courses()
    
    with tab2:
        show_add_course_form()
    
    with tab3:
        show_edit_delete_course_form()

def show_all_courses():
    """Show all courses in the system."""
    courses = get_courses()
    assignments = get_assignments()
    attendance = get_attendance()
    
    # Filter options
    st.markdown("### Filter Courses")
    col1, col2 = st.columns(2)
    
    with col1:
        department_filter = st.text_input("Filter by Department")
    
    with col2:
        search_term = st.text_input("Search by Course Name or ID")
    
    # Prepare data for table
    course_data = []
    for course_id, course in courses.items():
        # Apply filters
        if department_filter and department_filter.lower() not in course.get("department", "").lower():
            continue
        
        if search_term and search_term.lower() not in course_id.lower() and search_term.lower() not in course.get("course_name", "").lower():
            continue
        
        # Count assignments
        assignment_count = 0
        if course_id in assignments:
            assignment_count = len(assignments[course_id])
        
        # Count attendance records
        attendance_count = 0
        if course_id in attendance:
            for date, records in attendance[course_id].items():
                attendance_count += len(records)
        
        course_data.append({
            "Course ID": course_id,
            "Course Name": course.get("course_name", ""),
            "Department": course.get("department", ""),
            "Teacher": course.get("teacher_email", ""),
            "Credits": course.get("credits", 3),
            "Assignments": assignment_count,
            "Attendance Records": attendance_count,
            "Created At": format_datetime(course.get("created_at", ""))
        })
    
    # Show table
    st.markdown("### Course List")
    if course_data:
        show_data_table(course_data)
    else:
        st.info("No courses found matching the filters.")

def show_add_course_form():
    """Show the form to add a new course."""
    st.markdown("### Add New Course")
    
    # Get all teachers
    users = get_users()
    teachers = {email: user for email, user in users.items() if user.get("role") == "teacher"}
    
    with st.form("add_course_form"):
        course_id = st.text_input("Course ID")
        course_name = st.text_input("Course Name")
        
        department = st.text_input("Department")
        
        teacher_email = st.selectbox(
            "Teacher",
            options=list(teachers.keys()),
            format_func=lambda x: f"{teachers[x].get('name', '')} ({x})"
        )
        
        description = st.text_area("Description")
        
        credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
        
        submit = st.form_submit_button("Add Course")
        
        if submit:
            if not course_id or not course_name or not department or not teacher_email:
                show_notification("Please fill in all required fields.", "error")
            else:
                # Add course
                success, message = add_course(
                    course_id=course_id,
                    course_name=course_name,
                    department=department,
                    teacher_email=teacher_email,
                    description=description,
                    credits=credits
                )
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error")

def show_edit_delete_course_form():
    """Show the form to edit or delete a course."""
    st.markdown("### Edit or Delete Course")
    
    # Get all courses
    courses = get_courses()
    
    if not courses:
        st.info("No courses available to edit.")
        return
    
    # Get all teachers
    users = get_users()
    teachers = {email: user for email, user in users.items() if user.get("role") == "teacher"}
    
    # Select course to edit
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', '')} ({x})"
    )
    
    if course_id:
        course = courses.get(course_id, {})
        
        with st.form("edit_course_form"):
            course_name = st.text_input("Course Name", value=course.get("course_name", ""))
            
            department = st.text_input("Department", value=course.get("department", ""))
            
            teacher_email = st.selectbox(
                "Teacher",
                options=list(teachers.keys()),
                format_func=lambda x: f"{teachers[x].get('name', '')} ({x})",
                index=list(teachers.keys()).index(course.get("teacher_email", "")) if course.get("teacher_email", "") in teachers else 0
            )
            
            description = st.text_area("Description", value=course.get("description", ""))
            
            credits = st.number_input("Credits", min_value=1, max_value=6, value=course.get("credits", 3))
            
            col1, col2 = st.columns(2)
            
            with col1:
                update = st.form_submit_button("Update Course")
            
            with col2:
                delete = st.form_submit_button("Delete Course", type="primary", help="This action cannot be undone")
            
            if update:
                # Update course
                success, message = update_course(
                    course_id=course_id,
                    course_name=course_name,
                    department=department,
                    teacher_email=teacher_email,
                    description=description,
                    credits=credits
                )
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error")
            
            elif delete:
                # Delete course
                success, message = delete_course(course_id)
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error") 