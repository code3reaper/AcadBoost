import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_attendance, get_student_attendance
)

@role_required(["student"])
def show_student_attendance():
    """Show the attendance page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Attendance", "View your attendance records")
    
    # Create tabs for different attendance views
    tab1, tab2 = st.tabs(["Attendance Summary", "Detailed Records"])
    
    with tab1:
        show_attendance_summary(email)
    
    with tab2:
        show_attendance_details(email)

def show_attendance_summary(email):
    """Show attendance summary for the student."""
    st.markdown("### Attendance Summary")
    
    # Get all courses
    courses = get_courses()
    
    # Get student's attendance
    attendance = get_student_attendance(email)
    
    if not attendance:
        st.info("No attendance records found.")
        return
    
    # Calculate attendance statistics
    attendance_stats = {
        "Present": 0,
        "Absent": 0,
        "Late": 0,
        "Excused": 0,
        "Total": 0
    }
    
    # Process attendance data
    for course_id, dates in attendance.items():
        for date, status in dates.items():
            status_value = status.get("status", "Absent")
            if status_value in attendance_stats:
                attendance_stats[status_value] += 1
            attendance_stats["Total"] += 1
    
    # Calculate attendance rate
    attendance_rate = (attendance_stats["Present"] / attendance_stats["Total"]) * 100 if attendance_stats["Total"] > 0 else 0
    
    # Show attendance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
    
    with col2:
        st.metric("Present", attendance_stats["Present"])
    
    with col3:
        st.metric("Absent", attendance_stats["Absent"])
    
    with col4:
        st.metric("Late", attendance_stats["Late"])
    
    # Show attendance pie chart
    fig = px.pie(
        names=["Present", "Absent", "Late", "Excused"],
        values=[attendance_stats["Present"], attendance_stats["Absent"], attendance_stats["Late"], attendance_stats["Excused"]],
        title="Attendance Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate course-wise attendance
    course_attendance = {}
    
    for course_id, dates in attendance.items():
        if course_id in courses:
            course_name = courses[course_id].get("course_name", "Unknown Course")
            
            course_stats = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": 0
            }
            
            for date, status in dates.items():
                status_value = status.get("status", "Absent")
                if status_value in course_stats:
                    course_stats[status_value] += 1
                course_stats["Total"] += 1
            
            attendance_rate = (course_stats["Present"] / course_stats["Total"]) * 100 if course_stats["Total"] > 0 else 0
            
            course_attendance[course_id] = {
                "Course ID": course_id,
                "Course Name": course_name,
                "Present": course_stats["Present"],
                "Absent": course_stats["Absent"],
                "Late": course_stats["Late"],
                "Excused": course_stats["Excused"],
                "Total Classes": course_stats["Total"],
                "Attendance Rate (%)": attendance_rate
            }
    
    # Show course-wise attendance
    if course_attendance:
        st.markdown("### Course-wise Attendance")
        
        # Prepare data for table
        course_data = list(course_attendance.values())
        
        # Sort by attendance rate (highest first)
        course_data.sort(key=lambda x: x["Attendance Rate (%)"], reverse=True)
        
        # Show table
        show_data_table(course_data)
        
        # Show bar chart
        fig = px.bar(
            course_data,
            x="Course Name",
            y="Attendance Rate (%)",
            title="Attendance Rate by Course",
            color="Attendance Rate (%)",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_attendance_details(email):
    """Show detailed attendance records for the student."""
    st.markdown("### Detailed Attendance Records")
    
    # Get all courses
    courses = get_courses()
    
    # Get student's attendance
    attendance = get_student_attendance(email)
    
    if not attendance:
        st.info("No attendance records found.")
        return
    
    # Select course
    course_options = {
        course_id: courses.get(course_id, {}).get("course_name", "Unknown Course")
        for course_id in attendance.keys()
    }
    
    selected_course = st.selectbox(
        "Select Course",
        options=list(course_options.keys()),
        format_func=lambda x: f"{course_options[x]} ({x})"
    )
    
    if selected_course:
        # Get attendance records for selected course
        course_attendance = attendance.get(selected_course, {})
        
        if not course_attendance:
            st.info(f"No attendance records found for {course_options[selected_course]}.")
            return
        
        # Prepare data for table
        attendance_data = []
        
        for date, status in course_attendance.items():
            try:
                formatted_date = format_date(date)
            except:
                formatted_date = date
            
            # Check if status is a dictionary
            if isinstance(status, dict):
                actual_status = status.get("status", "Present")
            else:
                actual_status = status
                
            # Make sure status is a valid string
            if actual_status not in ["Present", "Absent", "Late", "Excused"]:
                actual_status = "Present"  # Default to Present if invalid
            
            attendance_data.append({
                "Date": formatted_date,
                "Status": actual_status
            })
        
        # Sort by date (newest first)
        attendance_data.sort(key=lambda x: x["Date"], reverse=True)
        
        # Show table
        show_data_table(attendance_data)
        
        # Create bar chart for status distribution
        status_counts = {
            "Present": 0,
            "Absent": 0,
            "Late": 0,
            "Excused": 0
        }
        
        for record in attendance_data:
            status = record["Status"]
            if status in status_counts:
                status_counts[status] += 1
        
        fig = px.bar(
            x=list(status_counts.keys()),
            y=list(status_counts.values()),
            title=f"Attendance Status Distribution for {course_options[selected_course]}",
            labels={"x": "Status", "y": "Count"},
            color=list(status_counts.keys()),
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True) 