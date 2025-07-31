import streamlit as st
import pandas as pd
from datetime import datetime

from utils.auth import (
    role_required, get_users, create_user, 
    update_user, delete_user, get_user_by_email
)
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_datetime
)

@role_required(["admin"])
def show_user_management():
    """Show the user management page for administrators."""
    show_header("User Management", "Manage users in the system")
    
    # Create tabs for different user management functions
    tab1, tab2, tab3 = st.tabs(["All Users", "Add User", "Edit/Delete User"])
    
    with tab1:
        show_all_users()
    
    with tab2:
        show_add_user_form()
    
    with tab3:
        show_edit_delete_user_form()

def show_all_users():
    """Show all users in the system."""
    users = get_users()
    
    # Filter options
    st.markdown("### Filter Users")
    col1, col2 = st.columns(2)
    
    with col1:
        role_filter = st.selectbox(
            "Filter by Role",
            options=["All", "Admin", "Teacher", "Student"],
            index=0
        )
    
    with col2:
        search_term = st.text_input("Search by Name or Email")
    
    # Prepare data for table
    user_data = []
    for email, user in users.items():
        # Apply filters
        if role_filter != "All" and user.get("role", "").lower() != role_filter.lower():
            continue
        
        if search_term and search_term.lower() not in email.lower() and search_term.lower() not in user.get("name", "").lower():
            continue
        
        user_data.append({
            "Email": email,
            "Name": user.get("name", ""),
            "Role": user.get("role", "").capitalize(),
            "Department": user.get("department", "N/A"),
            "Created At": format_datetime(user.get("created_at", ""))
        })
    
    # Show table
    st.markdown("### User List")
    if user_data:
        show_data_table(user_data)
    else:
        st.info("No users found matching the filters.")

def show_add_user_form():
    """Show the form to add a new user."""
    st.markdown("### Add New User")
    
    with st.form("add_user_form"):
        email = st.text_input("Email")
        name = st.text_input("Name")
        password = st.text_input("Password", type="password")
        
        role = st.selectbox(
            "Role",
            options=["Admin", "Teacher", "Student"],
            index=2
        )
        
        # Role-specific fields
        if role == "Teacher":
            department = st.text_input("Department")
            additional_data = {"department": department}
        elif role == "Student":
            student_id = st.text_input("Student ID")
            department = st.text_input("Department")
            year = st.number_input("Year", min_value=1, max_value=6, value=1)
            additional_data = {
                "student_id": student_id,
                "department": department,
                "year": year
            }
        else:
            additional_data = {}
        
        submit = st.form_submit_button("Add User")
        
        if submit:
            if not email or not name or not password:
                show_notification("Please fill in all required fields.", "error")
            else:
                # Create user
                success, message = create_user(
                    email=email,
                    password=password,
                    role=role.lower(),
                    name=name,
                    **additional_data
                )
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error")

def show_edit_delete_user_form():
    """Show the form to edit or delete a user."""
    st.markdown("### Edit or Delete User")
    
    # Get all users
    users = get_users()
    
    # Select user to edit
    email = st.selectbox(
        "Select User",
        options=list(users.keys()),
        format_func=lambda x: f"{users[x].get('name', '')} ({x})"
    )
    
    if email:
        user = get_user_by_email(email)
        
        if user:
            with st.form("edit_user_form"):
                name = st.text_input("Name", value=user.get("name", ""))
                password = st.text_input("New Password (leave blank to keep current)", type="password")
                
                role = user.get("role", "")
                st.text_input("Role", value=role.capitalize(), disabled=True)
                
                # Role-specific fields
                if role == "teacher":
                    department = st.text_input("Department", value=user.get("department", ""))
                    additional_data = {"department": department}
                elif role == "student":
                    student_id = st.text_input("Student ID", value=user.get("student_id", ""))
                    department = st.text_input("Department", value=user.get("department", ""))
                    year = st.number_input("Year", min_value=1, max_value=6, value=user.get("year", 1))
                    additional_data = {
                        "student_id": student_id,
                        "department": department,
                        "year": year
                    }
                else:
                    additional_data = {}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    update = st.form_submit_button("Update User")
                
                with col2:
                    delete = st.form_submit_button("Delete User", type="primary", help="This action cannot be undone")
                
                if update:
                    # Prepare update data
                    update_data = {"name": name, **additional_data}
                    
                    if password:
                        update_data["password"] = password
                    
                    # Update user
                    success, message = update_user(email, **update_data)
                    
                    if success:
                        show_notification(message, "success")
                    else:
                        show_notification(message, "error")
                
                elif delete:
                    # Delete user
                    success, message = delete_user(email)
                    
                    if success:
                        show_notification(message, "success")
                    else:
                        show_notification(message, "error") 