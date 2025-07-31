import streamlit as st
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table, show_card,
    format_datetime
)
from utils.database import (
    get_announcements, create_announcement, delete_announcement
)
from pages.admin.department_management import get_departments

@role_required(["admin"])
def show_announcements():
    """Show the announcements page for administrators."""
    show_header("Announcements", "Create and manage announcements")
    
    # Create tabs for different announcement functions
    tab1, tab2 = st.tabs(["All Announcements", "Create Announcement"])
    
    with tab1:
        show_all_announcements()
    
    with tab2:
        show_create_announcement_form()

def show_all_announcements():
    """Show all announcements in the system."""
    announcements = get_announcements()
    
    # Filter options
    st.markdown("### Filter Announcements")
    col1, col2 = st.columns(2)
    
    with col1:
        role_filter = st.selectbox(
            "Filter by Target Role",
            options=["All", "Admin", "Teacher", "Student"],
            index=0
        )
    
    with col2:
        search_term = st.text_input("Search by Title or Content")
    
    # Prepare filtered announcements
    filtered_announcements = []
    for announcement in announcements:
        # Apply role filter
        if role_filter != "All":
            target_roles = announcement.get("target_roles", [])
            if target_roles and role_filter.lower() not in [r.lower() for r in target_roles]:
                continue
        
        # Apply search filter
        if search_term:
            title = announcement.get("title", "").lower()
            content = announcement.get("content", "").lower()
            if search_term.lower() not in title and search_term.lower() not in content:
                continue
        
        filtered_announcements.append(announcement)
    
    # Sort announcements by date (newest first)
    filtered_announcements.sort(
        key=lambda x: x.get("created_at", ""), 
        reverse=True
    )
    
    # Show announcements
    st.markdown("### Announcement List")
    
    if filtered_announcements:
        for announcement in filtered_announcements:
            with st.expander(f"{announcement.get('title', 'No Title')} - {format_datetime(announcement.get('created_at', ''))}"):
                st.markdown(f"**Author:** {announcement.get('author_email', 'Unknown')}")
                
                # Show target roles
                target_roles = announcement.get("target_roles", [])
                if target_roles:
                    st.markdown(f"**Target Roles:** {', '.join(target_roles)}")
                else:
                    st.markdown("**Target Roles:** All")
                
                # Show target departments
                target_departments = announcement.get("target_departments", [])
                if target_departments:
                    st.markdown(f"**Target Departments:** {', '.join(target_departments)}")
                else:
                    st.markdown("**Target Departments:** All")
                
                st.markdown("**Content:**")
                st.markdown(announcement.get("content", "No content"))
                
                # Delete button
                if st.button(f"Delete Announcement #{announcement.get('announcement_id')}", key=f"delete_{announcement.get('announcement_id')}_{id(announcement)}"):
                    success, message = delete_announcement(announcement.get("announcement_id"))
                    
                    if success:
                        show_notification(message, "success")
                        st.rerun()
                    else:
                        show_notification(message, "error")
    else:
        st.info("No announcements found matching the filters.")

def show_create_announcement_form():
    """Show the form to create a new announcement."""
    st.markdown("### Create New Announcement")
    
    # Get departments
    departments = get_departments()
    department_names = [dept["name"] for dept in departments.values()]
    
    with st.form("create_announcement_form"):
        title = st.text_input("Title")
        content = st.text_area("Content")
        
        st.markdown("### Target Audience")
        
        # Target roles
        st.markdown("**Target Roles** (leave unchecked for all)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_admin = st.checkbox("Admin")
        
        with col2:
            target_teacher = st.checkbox("Teacher")
        
        with col3:
            target_student = st.checkbox("Student")
        
        # Target departments
        st.markdown("**Target Departments** (leave unchecked for all)")
        
        target_departments = []
        for dept_name in department_names:
            if st.checkbox(dept_name, key=f"dept_{dept_name}"):
                target_departments.append(dept_name)
        
        submit = st.form_submit_button("Create Announcement")
        
        if submit:
            if not title or not content:
                show_notification("Please fill in all required fields.", "error")
            else:
                # Prepare target roles
                target_roles = []
                if target_admin:
                    target_roles.append("admin")
                if target_teacher:
                    target_roles.append("teacher")
                if target_student:
                    target_roles.append("student")
                
                # Create announcement
                success, message = create_announcement(
                    title=title,
                    content=content,
                    author_email=st.session_state.email,
                    target_roles=target_roles if target_roles else None,
                    target_departments=target_departments if target_departments else None
                )
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error") 