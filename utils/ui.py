import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt

# Color scheme
PRIMARY_COLOR = "#4F8BF9"
SECONDARY_COLOR = "#FF4B4B"
SUCCESS_COLOR = "#00C851"
WARNING_COLOR = "#FFBB33"
DANGER_COLOR = "#FF4444"
INFO_COLOR = "#33B5E5"

# Set page configuration
def set_page_config(title="AcadBoost", layout="wide"):
    """Set page configuration."""
    st.set_page_config(
        page_title=title,
        page_icon="🎓",
        layout=layout,
        initial_sidebar_state="expanded"
    )

def show_header(title, subtitle=None):
    """Show a header with title and optional subtitle."""
    st.markdown(f"<h1 style='color: {PRIMARY_COLOR};'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<h3>{subtitle}</h3>", unsafe_allow_html=True)
    st.markdown("---")

def show_sidebar_header():
    """Show the sidebar header with logo and navigation."""
    with st.sidebar:
        st.markdown(
            f"<h1 style='text-align: center; color: {PRIMARY_COLOR};'>🎓 AcadBoost</h1>", 
            unsafe_allow_html=True
        )
        st.markdown("---")

def show_login_form():
    """Show the login form."""
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            return email, password
    return None, None

def show_user_info(user):
    """Show user information in the sidebar."""
    with st.sidebar:
        st.markdown(
            f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>"
            f"<p><b>Name:</b> {user.get('name', 'N/A')}</p>"
            f"<p><b>Role:</b> {user.get('role', 'N/A').capitalize()}</p>"
            f"<p><b>Email:</b> {user.get('email', 'N/A')}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.markdown("---")

def show_navigation(role):
    """Show navigation based on user role."""
    with st.sidebar:
        st.markdown("### Navigation")
        
        # Common navigation
        if st.button("Dashboard", use_container_width=True, key="common_dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("Profile", use_container_width=True, key="common_profile"):
            st.session_state.page = "profile"
            st.rerun()
        
        st.markdown("---")
        
        # Role-specific navigation
        if role == "admin":
            st.markdown("### Admin")
            if st.button("User Management", use_container_width=True, key="admin_user_management"):
                st.session_state.page = "user_management"
                st.rerun()
            if st.button("Course Management", use_container_width=True, key="admin_course_management"):
                st.session_state.page = "course_management"
                st.rerun()
            if st.button("Department Management", use_container_width=True, key="admin_department_management"):
                st.session_state.page = "department_management"
                st.rerun()
            if st.button("Announcements", use_container_width=True, key="admin_announcements"):
                st.session_state.page = "announcements"
                st.rerun()
            if st.button("Reports", use_container_width=True, key="admin_reports"):
                st.session_state.page = "reports"
                st.rerun()
        
        elif role == "teacher":
            st.markdown("### Teacher")
            if st.button("Courses", key="teacher_courses", use_container_width=True):
                st.session_state.page = "my_courses"
                st.rerun()
            if st.button("Assignments", key="teacher_assignments", use_container_width=True):
                st.session_state.page = "assignments"
                st.rerun()
            if st.button("Projects", key="teacher_projects", use_container_width=True):
                st.session_state.page = "projects"
                st.rerun()
            if st.button("Attendance", key="teacher_attendance", use_container_width=True):
                st.session_state.page = "attendance"
                st.rerun()
            if st.button("Student Reports", key="teacher_student_reports", use_container_width=True):
                st.session_state.page = "student_reports"
                st.rerun()
            if st.button("Exams", key="teacher_exams", use_container_width=True):
                st.session_state.page = "exams"
                st.rerun()
            if st.button("Announcements", key="teacher_announcements", use_container_width=True):
                st.session_state.page = "announcements"
                st.rerun()
        
        elif role == "student":
            st.markdown("### Student")
            if st.button("My Courses", use_container_width=True, key="student_my_courses"):
                st.session_state.page = "my_courses"
                st.rerun()
            if st.button("Attendance", use_container_width=True, key="student_attendance"):
                st.session_state.page = "attendance"
                st.rerun()
            if st.button("Assignments", use_container_width=True, key="student_assignments"):
                st.session_state.page = "assignments"
                st.rerun()
            if st.button("Projects", use_container_width=True, key="student_projects"):
                st.session_state.page = "projects"
                st.rerun()
            if st.button("Exams", use_container_width=True, key="student_exams"):
                st.session_state.page = "exams"
                st.rerun()
            if st.button("Certificates", use_container_width=True, key="student_certificates"):
                st.session_state.page = "certificates"
                st.rerun()
            if st.button("My Performance", use_container_width=True, key="student_my_performance"):
                st.session_state.page = "my_performance"
                st.rerun()
            if st.button("Resume", use_container_width=True, key="student_resume"):
                st.session_state.page = "resume"
                st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("Logout", use_container_width=True):
            st.session_state.page = "login"
            if "user" in st.session_state:
                del st.session_state.user

def show_card(title, content, icon=None, color=PRIMARY_COLOR):
    """Show a card with title, content, and optional icon."""
    icon_html = f"<i class='material-icons'>{icon}</i> " if icon else ""
    st.markdown(
        f"""
        <div style='background-color: white; padding: 15px; border-radius: 5px; border-left: 5px solid {color}; margin-bottom: 10px;'>
            <h3 style='color: {color};'>{icon_html}{title}</h3>
            <p>{content}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def show_metric_card(title, value, delta=None, delta_color="normal"):
    """Show a metric card with title, value, and optional delta."""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def show_data_table(data, use_container_width=True):
    """Show a data table."""
    if isinstance(data, list) and data:
        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Convert dict to DataFrame
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)
    
    st.dataframe(df, use_container_width=use_container_width)

def show_attendance_chart(attendance_data):
    """Show an attendance chart."""
    if not attendance_data:
        st.info("No attendance data available.")
        return
    
    # Prepare data for chart
    statuses = {"Present": 0, "Absent": 0, "Late": 0, "Excused": 0}
    
    for course_id, dates in attendance_data.items():
        for date, records in dates.items():
            for student, record in records.items():
                status = record.get("status")
                if status in statuses:
                    statuses[status] += 1
    
    # Create chart
    fig = px.pie(
        names=list(statuses.keys()),
        values=list(statuses.values()),
        title="Attendance Summary",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_performance_chart(grades_data):
    """Show a performance chart."""
    if not grades_data:
        st.info("No performance data available.")
        return
    
    # Prepare data for chart
    courses = []
    grades = []
    
    # Check if grades_data is a list or dictionary
    if isinstance(grades_data, list):
        # Handle list of dictionaries (from profile analysis)
        for course_data in grades_data:
            courses.append(course_data.get("course_name", "Unknown"))
            grades.append(course_data.get("grade", 0))
    else:
        # Handle dictionary (from original implementation)
        for assignment_id, submission in grades_data.items():
            if submission.get("grade") is not None:
                courses.append(assignment_id.split("_")[0])  # Extract course ID from assignment ID
                grades.append(submission.get("grade"))
    
    if not courses:
        st.info("No graded assignments available.")
        return
    
    # Create chart
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(courses, grades)
    
    # Add labels and title
    ax.set_xlabel("Course")
    ax.set_ylabel("Grade (%)")
    ax.set_title("Performance by Course")
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom')
    
    st.pyplot(fig)

def show_calendar(events):
    """Show a calendar with events."""
    if not events:
        st.info("No events available.")
        return
    
    # Group events by date
    events_by_date = {}
    for event in events:
        date = event.get("date")
        if date not in events_by_date:
            events_by_date[date] = []
        events_by_date[date].append(event)
    
    # Display events
    for date, date_events in sorted(events_by_date.items()):
        with st.expander(date):
            for event in date_events:
                st.markdown(
                    f"""
                    <div style='background-color: white; padding: 10px; border-radius: 5px; margin-bottom: 5px;'>
                        <h4>{event.get('title')}</h4>
                        <p>{event.get('description')}</p>
                        <p><small>Time: {event.get('time')}</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

def show_notification(message, type="info"):
    """Show a notification message."""
    if type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    else:
        st.info(message)

def show_file_uploader(label, type=None, key=None):
    """Show a file uploader."""
    return st.file_uploader(label, type=type, key=key)

def format_date(date_str):
    """Format a date string."""
    try:
        date = datetime.fromisoformat(date_str)
        return date.strftime("%B %d, %Y")
    except:
        return date_str

def format_datetime(datetime_str):
    """Format a datetime string."""
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%B %d, %Y %I:%M %p")
    except:
        return datetime_str 