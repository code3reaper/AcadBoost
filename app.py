import streamlit as st
import os
import sys
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utility modules
from utils.auth import authenticate, is_authenticated, logout
from utils.ui import (
    set_page_config, show_header, show_sidebar_header, 
    show_login_form, show_user_info, show_navigation,
    show_notification
)

# Import pages
from pages.login import show_login_page
from pages.dashboard import show_dashboard
from pages.profile import show_profile
from pages.admin.user_management import show_user_management
from pages.admin.course_management import show_course_management
from pages.admin.department_management import show_department_management
from pages.admin.announcements import show_announcements as show_admin_announcements
from pages.admin.reports import show_reports
from pages.teacher.my_courses import show_teacher_courses
from pages.teacher.attendance import show_teacher_attendance
from pages.teacher.assignments import show_teacher_assignments
from pages.teacher.projects import show_teacher_projects
from pages.teacher.student_performance import show_student_performance
from pages.teacher.student_reports import show_student_reports
from pages.teacher.exams import show_teacher_exams
from pages.student.my_courses import show_student_courses
from pages.student.attendance import show_student_attendance
from pages.student.assignments import show_student_assignments
from pages.student.projects import show_student_projects
from pages.student.certificates import show_certificates
from pages.student.my_performance import show_my_performance
from pages.student.exams import show_student_exams
from pages.student.resume import show_student_resume
from pages.student.certificates import get_certificates
def main():
    # Set page configuration
    set_page_config()
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    # Show sidebar header
    show_sidebar_header()
    
    # Check authentication
    if not is_authenticated() and st.session_state.page != "login":
        st.session_state.page = "login"
    
    # Show user info and navigation if authenticated
    if is_authenticated():
        user = st.session_state.user
        user["email"] = st.session_state.email  # Add email to user object
        show_user_info(user)
        show_navigation(user["role"])
    
    # Route to the appropriate page
    if st.session_state.page == "login":
        show_login_page()
    
    elif st.session_state.page == "dashboard":
        show_dashboard()
    
    elif st.session_state.page == "profile":
        show_profile()
    
    # Admin pages
    elif st.session_state.page == "user_management" and st.session_state.user["role"] == "admin":
        show_user_management()
    
    elif st.session_state.page == "course_management" and st.session_state.user["role"] == "admin":
        show_course_management()
    
    elif st.session_state.page == "department_management" and st.session_state.user["role"] == "admin":
        show_department_management()
    
    elif st.session_state.page == "announcements" and st.session_state.user["role"] == "admin":
        show_admin_announcements()
    
    elif st.session_state.page == "reports" and st.session_state.user["role"] == "admin":
        show_reports()
    
    # Teacher pages
    elif st.session_state.page == "my_courses" and st.session_state.user["role"] == "teacher":
        show_teacher_courses()
    
    elif st.session_state.page == "attendance" and st.session_state.user["role"] == "teacher":
        show_teacher_attendance()
    
    elif st.session_state.page == "assignments" and st.session_state.user["role"] == "teacher":
        show_teacher_assignments()
    
    elif st.session_state.page == "projects" and st.session_state.user["role"] == "teacher":
        show_teacher_projects()
    
    elif st.session_state.page == "student_reports" and st.session_state.user["role"] == "teacher":
        show_student_reports()
    
    elif st.session_state.page == "student_performance" and st.session_state.user["role"] == "teacher":
        show_student_performance()
    
    elif st.session_state.page == "exams" and st.session_state.user["role"] == "teacher":
        from pages.teacher.exams import show_teacher_exams
        show_teacher_exams()
    elif st.session_state.page == "announcements" and st.session_state.user["role"] == "teacher":
        from pages.teacher.announcements import show_announcements as show_teacher_announcements
        show_teacher_announcements()
    
    # Student pages
    elif st.session_state.page == "my_courses" and st.session_state.user["role"] == "student":
        show_student_courses()
    
    elif st.session_state.page == "attendance" and st.session_state.user["role"] == "student":
        show_student_attendance()
    
    elif st.session_state.page == "assignments" and st.session_state.user["role"] == "student":
        show_student_assignments()
    
    elif st.session_state.page == "projects" and st.session_state.user["role"] == "student":
        show_student_projects()
    
    elif st.session_state.page == "certificates" and st.session_state.user["role"] == "student":
        show_certificates()
    
    elif st.session_state.page == "my_performance" and st.session_state.user["role"] == "student":
        show_my_performance()
    
    elif st.session_state.page == "exams" and st.session_state.user["role"] == "student":
        show_student_exams()
    
    elif st.session_state.page == "resume" and st.session_state.user["role"] == "student":
        show_student_resume()
    
    # Teacher navigation
    elif st.session_state.page == "teacher_navigation" and st.session_state.user["role"] == "teacher":
        show_teacher_navigation()
    
    # Invalid page
    else:
        st.error("Page not found or you don't have permission to access it.")
        st.session_state.page = "dashboard" if is_authenticated() else "login"

# Teacher navigation
def show_teacher_navigation():
    """Show the navigation menu for teachers."""
    st.sidebar.markdown("## Teacher Menu")
    
    options = {
        "My Courses": show_teacher_courses,
        "Attendance": show_teacher_attendance,
        "Assignments": show_teacher_assignments,
        "Projects": show_teacher_projects,
        "Exams": show_teacher_exams,
        "Student Reports": show_student_reports,
        "Profile": show_profile,
        "Logout": logout
    }
    
    selected = st.sidebar.radio("Navigate", list(options.keys()))
    
    if selected == "Logout":
        logout()
    else:
        options[selected]()

if __name__ == "__main__":
    main() 