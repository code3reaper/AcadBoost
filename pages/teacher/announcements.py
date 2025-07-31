import streamlit as st
from datetime import datetime
import pandas as pd

from utils.auth import role_required, get_users
from utils.ui import show_header, show_notification, show_data_table, format_datetime
from utils.database import (
    get_announcements, create_announcement, delete_announcement,
    get_teacher_courses
)

@role_required(["teacher"])
def show_announcements():
    """Show the announcements page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("Announcements", "Create and manage announcements for your students")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Create Announcement", "Manage Announcements"])
    
    with tab1:
        show_create_announcement(user, email)
    
    with tab2:
        show_manage_announcements(user, email)

def show_create_announcement(user, email):
    """Show the create announcement form."""
    st.markdown("### Create New Announcement")
    
    # Get all users
    users = get_users()
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    # Find students in teacher's courses
    course_students = {}
    
    for course_id, course in courses.items():
        course_name = course.get("course_name", "Unknown Course")
        course_students[course_id] = {
            "course_name": course_name,
            "students": []
        }
    
    # Filter students
    all_students = {email: user for email, user in users.items() if user.get("role") == "student"}
    
    # Create announcement form
    with st.form("create_announcement_form"):
        title = st.text_input("Announcement Title", placeholder="Enter announcement title")
        content = st.text_area("Announcement Content", placeholder="Enter announcement content", height=200)
        
        # Target options
        st.markdown("### Target Audience")
        
        target_type = st.radio(
            "Select Target Audience",
            options=["All Students", "Specific Departments", "Specific Students"],
            horizontal=True
        )
        
        target_roles = ["student"]
        target_departments = None
        target_emails = None
        
        if target_type == "Specific Departments":
            # Get unique departments
            departments = set()
            for student in all_students.values():
                if "department" in student and student["department"]:
                    departments.add(student["department"])
            
            if departments:
                target_departments = st.multiselect(
                    "Select Departments",
                    options=sorted(list(departments))
                )
            else:
                st.info("No departments found.")
        
        elif target_type == "Specific Students":
            # Get students
            student_options = [(email, user.get("name", "Unknown") + f" ({email})") for email, user in all_students.items()]
            
            if student_options:
                selected_students = st.multiselect(
                    "Select Students",
                    options=[email for email, _ in student_options],
                    format_func=lambda x: next((name for e, name in student_options if e == x), x)
                )
                
                target_emails = selected_students
            else:
                st.info("No students found.")
        
        # Submit button
        submit = st.form_submit_button("Create Announcement")
        
        if submit:
            if not title:
                st.error("Please enter a title for the announcement.")
            elif not content:
                st.error("Please enter content for the announcement.")
            else:
                # Create announcement
                success, message = create_announcement(
                    title=title,
                    content=content,
                    author_email=email,
                    target_roles=target_roles,
                    target_departments=target_departments,
                    target_emails=target_emails
                )
                
                if success:
                    st.success("Announcement created successfully!")
                    # Clear form
                    st.rerun()
                else:
                    st.error(f"Failed to create announcement: {message}")

def show_manage_announcements(user, email):
    """Show and manage existing announcements."""
    st.markdown("### Manage Announcements")
    
    # Get all announcements
    announcements = get_announcements()
    
    # Filter announcements created by this teacher
    teacher_announcements = [a for a in announcements if a.get("author_email") == email]
    
    if not teacher_announcements:
        st.info("You haven't created any announcements yet.")
        return
    
    # Prepare data for display
    announcement_data = []
    
    for announcement in teacher_announcements:
        # Determine target audience
        target_audience = "All Students"
        
        if announcement.get("target_emails"):
            target_audience = f"Specific Students ({len(announcement.get('target_emails'))})"
        elif announcement.get("target_departments"):
            target_audience = f"Specific Departments ({', '.join(announcement.get('target_departments'))})"
        
        announcement_data.append({
            "ID": announcement.get("announcement_id"),
            "Title": announcement.get("title"),
            "Created": format_datetime(announcement.get("created_at", "")),
            "Target Audience": target_audience
        })
    
    # Sort by creation date (newest first)
    announcement_data.sort(key=lambda x: x["Created"], reverse=True)
    
    # Show announcement table
    show_data_table(announcement_data)
    
    # Select announcement for detailed view
    selected_id = st.selectbox(
        "Select Announcement for Details",
        options=[a["ID"] for a in announcement_data],
        format_func=lambda x: next((a["Title"] for a in announcement_data if a["ID"] == x), "")
    )
    
    if selected_id:
        # Find the selected announcement
        selected_announcement = next((a for a in teacher_announcements if a.get("announcement_id") == selected_id), None)
        
        if selected_announcement:
            st.markdown("### Announcement Details")
            
            # Display announcement details
            st.markdown(f"**Title:** {selected_announcement.get('title')}")
            st.markdown(f"**Created:** {format_datetime(selected_announcement.get('created_at', ''))}")
            
            # Display target audience
            if selected_announcement.get("target_emails"):
                st.markdown(f"**Target Audience:** {len(selected_announcement.get('target_emails'))} specific students")
                
                # Get user details for emails
                users = get_users()
                target_students = []
                
                for email in selected_announcement.get("target_emails"):
                    if email in users:
                        target_students.append(f"{users[email].get('name', 'Unknown')} ({email})")
                    else:
                        target_students.append(email)
                
                st.markdown("**Target Students:**")
                for student in target_students:
                    st.markdown(f"- {student}")
            
            elif selected_announcement.get("target_departments"):
                st.markdown(f"**Target Audience:** Departments: {', '.join(selected_announcement.get('target_departments'))}")
            
            else:
                st.markdown("**Target Audience:** All Students")
            
            # Display content
            st.markdown("### Content")
            st.markdown(selected_announcement.get("content"))
            
            # Delete button
            if st.button("Delete Announcement"):
                success, message = delete_announcement(selected_id)
                
                if success:
                    st.success("Announcement deleted successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to delete announcement: {message}") 