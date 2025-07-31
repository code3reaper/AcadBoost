import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from utils.auth import role_required, get_users
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_datetime
)
from utils.database import (
    get_courses, DATA_DIR
)

# File path for departments
DEPARTMENTS_FILE = os.path.join(DATA_DIR, "departments.json")

@role_required(["admin"])
def show_department_management():
    """Show the department management page for administrators."""
    show_header("Department Management", "Manage departments in the system")
    
    # Create tabs for different department management functions
    tab1, tab2, tab3 = st.tabs(["All Departments", "Add Department", "Edit/Delete Department"])
    
    with tab1:
        show_all_departments()
    
    with tab2:
        show_add_department_form()
    
    with tab3:
        show_edit_delete_department_form()

def get_departments():
    """Get all departments."""
    if not os.path.exists(DEPARTMENTS_FILE):
        # Create default departments
        departments = {
            "CS": {
                "name": "Computer Science",
                "hod_email": "teacher@college.edu",
                "description": "Department of Computer Science",
                "created_at": datetime.now().isoformat()
            },
            "MATH": {
                "name": "Mathematics",
                "hod_email": "teacher@college.edu",
                "description": "Department of Mathematics",
                "created_at": datetime.now().isoformat()
            },
            "PHY": {
                "name": "Physics",
                "hod_email": "teacher@college.edu",
                "description": "Department of Physics",
                "created_at": datetime.now().isoformat()
            }
        }
        
        with open(DEPARTMENTS_FILE, 'w') as f:
            json.dump(departments, f, indent=4)
    
    with open(DEPARTMENTS_FILE, 'r') as f:
        return json.load(f)

def save_departments(departments):
    """Save departments to file."""
    with open(DEPARTMENTS_FILE, 'w') as f:
        json.dump(departments, f, indent=4)

def add_department(dept_id, name, hod_email, description=""):
    """Add a new department."""
    departments = get_departments()
    
    if dept_id in departments:
        return False, "Department ID already exists"
    
    departments[dept_id] = {
        "name": name,
        "hod_email": hod_email,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    
    save_departments(departments)
    return True, "Department added successfully"

def update_department(dept_id, name, hod_email, description):
    """Update a department."""
    departments = get_departments()
    
    if dept_id not in departments:
        return False, "Department not found"
    
    departments[dept_id].update({
        "name": name,
        "hod_email": hod_email,
        "description": description
    })
    
    save_departments(departments)
    return True, "Department updated successfully"

def delete_department(dept_id):
    """Delete a department."""
    departments = get_departments()
    
    if dept_id not in departments:
        return False, "Department not found"
    
    # Check if department is in use
    courses = get_courses()
    for course_id, course in courses.items():
        if course.get("department") == departments[dept_id]["name"]:
            return False, "Cannot delete department that is in use by courses"
    
    del departments[dept_id]
    save_departments(departments)
    return True, "Department deleted successfully"

def show_all_departments():
    """Show all departments in the system."""
    departments = get_departments()
    courses = get_courses()
    users = get_users()
    
    # Prepare data for table
    department_data = []
    for dept_id, dept in departments.items():
        # Count courses in this department
        course_count = 0
        for course_id, course in courses.items():
            if course.get("department") == dept["name"]:
                course_count += 1
        
        # Count teachers in this department
        teacher_count = 0
        for email, user in users.items():
            if user.get("role") == "teacher" and user.get("department") == dept["name"]:
                teacher_count += 1
        
        # Count students in this department
        student_count = 0
        for email, user in users.items():
            if user.get("role") == "student" and user.get("department") == dept["name"]:
                student_count += 1
        
        department_data.append({
            "Department ID": dept_id,
            "Name": dept["name"],
            "Head of Department": dept["hod_email"],
            "Courses": course_count,
            "Teachers": teacher_count,
            "Students": student_count,
            "Created At": format_datetime(dept.get("created_at", ""))
        })
    
    # Show table
    st.markdown("### Department List")
    if department_data:
        show_data_table(department_data)
    else:
        st.info("No departments available.")

def show_add_department_form():
    """Show the form to add a new department."""
    st.markdown("### Add New Department")
    
    # Get all teachers
    users = get_users()
    teachers = {email: user for email, user in users.items() if user.get("role") == "teacher"}
    
    with st.form("add_department_form"):
        dept_id = st.text_input("Department ID")
        name = st.text_input("Department Name")
        
        hod_email = st.selectbox(
            "Head of Department",
            options=list(teachers.keys()),
            format_func=lambda x: f"{teachers[x].get('name', '')} ({x})"
        )
        
        description = st.text_area("Description")
        
        submit = st.form_submit_button("Add Department")
        
        if submit:
            if not dept_id or not name or not hod_email:
                show_notification("Please fill in all required fields.", "error")
            else:
                # Add department
                success, message = add_department(
                    dept_id=dept_id,
                    name=name,
                    hod_email=hod_email,
                    description=description
                )
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error")

def show_edit_delete_department_form():
    """Show the form to edit or delete a department."""
    st.markdown("### Edit or Delete Department")
    
    # Get all departments
    departments = get_departments()
    
    if not departments:
        st.info("No departments available to edit.")
        return
    
    # Get all teachers
    users = get_users()
    teachers = {email: user for email, user in users.items() if user.get("role") == "teacher"}
    
    # Select department to edit
    dept_id = st.selectbox(
        "Select Department",
        options=list(departments.keys()),
        format_func=lambda x: f"{departments[x]['name']} ({x})"
    )
    
    if dept_id:
        dept = departments[dept_id]
        
        with st.form("edit_department_form"):
            name = st.text_input("Department Name", value=dept["name"])
            
            hod_email = st.selectbox(
                "Head of Department",
                options=list(teachers.keys()),
                format_func=lambda x: f"{teachers[x].get('name', '')} ({x})",
                index=list(teachers.keys()).index(dept["hod_email"]) if dept["hod_email"] in teachers else 0
            )
            
            description = st.text_area("Description", value=dept.get("description", ""))
            
            col1, col2 = st.columns(2)
            
            with col1:
                update = st.form_submit_button("Update Department")
            
            with col2:
                delete = st.form_submit_button("Delete Department", type="primary", help="This action cannot be undone")
            
            if update:
                # Update department
                success, message = update_department(
                    dept_id=dept_id,
                    name=name,
                    hod_email=hod_email,
                    description=description
                )
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error")
            
            elif delete:
                # Delete department
                success, message = delete_department(dept_id)
                
                if success:
                    show_notification(message, "success")
                else:
                    show_notification(message, "error") 