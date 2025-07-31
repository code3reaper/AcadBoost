import streamlit as st
import os
from datetime import datetime

from utils.auth import is_authenticated, role_required, update_user, get_user_by_email
from utils.ui import show_header, show_notification, format_datetime
from utils.database import get_student_submissions, get_teacher_courses

@role_required(["admin", "teacher", "student"])
def show_profile():
    """Show the profile page."""
    user = st.session_state.user
    email = st.session_state.email
    role = user["role"]
    
    show_header("My Profile", "View and update your profile information")
    
    # Create columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Profile picture placeholder
        st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=200)
        
        st.markdown(f"**Role:** {role.capitalize()}")
        st.markdown(f"**Email:** {email}")
        
        if "created_at" in user:
            st.markdown(f"**Joined:** {format_datetime(user['created_at'])}")
    
    with col2:
        # Profile information form
        with st.form("profile_form"):
            st.markdown("### Update Profile Information")
            
            name = st.text_input("Name", value=user.get("name", ""))
            
            # Role-specific fields
            if role == "teacher":
                department = st.text_input("Department", value=user.get("department", ""))
            elif role == "student":
                student_id = st.text_input("Student ID", value=user.get("student_id", ""))
                department = st.text_input("Department", value=user.get("department", ""))
                year = st.number_input("Year", min_value=1, max_value=6, value=user.get("year", 1))
                
                # Add semester field
                semester = st.selectbox(
                    "Semester", 
                    options=[1, 2, 3, 4, 5, 6, 7, 8],
                    index=user.get("semester", 1) - 1 if user.get("semester") else 0
                )
                
                # Add section field
                section = st.text_input("Section", value=user.get("section", ""))
            
            # Password change fields
            st.markdown("### Change Password")
            password = st.text_input("New Password (leave blank to keep current)", type="password")
            
            # Submit button
            submit = st.form_submit_button("Update Profile")
            
            if submit:
                # Create a new dictionary for the updated user instead of modifying the original
                updated_user = {}
                # Copy all existing user data
                for key, value in user.items():
                    # Ensure we're not copying any dictionary values that might cause issues
                    if not isinstance(value, dict):
                        updated_user[key] = value
                
                # Update with new values
                updated_user["name"] = name
                
                if role == "teacher":
                    updated_user["department"] = department
                elif role == "student":
                    updated_user["student_id"] = student_id
                    updated_user["department"] = department
                    updated_user["year"] = year
                    updated_user["semester"] = semester
                    updated_user["section"] = section
                
                # Update password if provided
                if password:
                    updated_user["password"] = password
                
                # Save changes
                success = update_user(email, updated_user)
                
                if success:
                    show_notification("Profile updated successfully!", "success")
                    # Update the session state with the new user data
                    for key, value in updated_user.items():
                        st.session_state.user[key] = value
                else:
                    show_notification("Failed to update profile. Please try again.", "error")
    
    # Show role-specific information
    st.markdown("---")
    
    if role == "teacher":
        show_teacher_profile_info(user, email)
    elif role == "student":
        show_student_profile_info(user, email)

def show_teacher_profile_info(user, email):
    """Show additional profile information for teachers."""
    st.markdown("---")
    st.markdown("### Teaching Information")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if courses:
        st.markdown("#### Courses Teaching")
        
        for course_id, course in courses.items():
            with st.expander(f"{course.get('course_name', 'No Name')} ({course_id})"):
                st.markdown(f"**Department:** {course.get('department', 'N/A')}")
                st.markdown(f"**Credits:** {course.get('credits', 3)}")
                if course.get("description"):
                    st.markdown(f"**Description:** {course.get('description')}")
    else:
        st.info("You are not assigned to any courses yet.")

def show_student_profile_info(user, email):
    """Show additional information for student profiles."""
    st.markdown("### Academic Information")
    
    # Get student's submissions
    submissions = get_student_submissions(email)
    
    # Calculate statistics
    total_submissions = len(submissions) if submissions else 0
    graded_submissions = [s for s in submissions if s.get("grade") is not None] if submissions else []
    total_graded = len(graded_submissions)
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Submissions", total_submissions)
    
    with col2:
        st.metric("Graded Submissions", total_graded)
    
    with col3:
        # Fix the potential division by zero error
        completion_rate = (total_graded / max(1, total_submissions)) * 100 if total_submissions > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%") 