import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table, show_attendance_chart,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_teacher_courses, get_attendance, mark_attendance
)

@role_required(["teacher"])
def show_teacher_attendance():
    """Show the attendance page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("Attendance Management", "Manage student attendance for your courses")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Create tabs for different attendance functions
    tab1, tab2, tab3 = st.tabs([
        "Mark Attendance", 
        "View Attendance", 
        "Attendance Reports"
    ])
    
    with tab1:
        show_mark_attendance(courses)
    
    with tab2:
        show_view_attendance(courses)
    
    with tab3:
        show_attendance_reports(courses)

def show_mark_attendance(courses):
    """Show interface for marking attendance."""
    st.markdown("### Mark Attendance")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})"
    )
    
    if course_id:
        # Get attendance data
        attendance = get_attendance().get(course_id, {})
        
        # Get unique students from attendance
        students = set()
        for date, student_records in attendance.items():
            for student_email in student_records.keys():
                students.add(student_email)
        
        # If no students found, show message
        if not students:
            st.warning("No students found for this course. Please add students to the course first.")
            
            # Option to add students manually
            with st.expander("Add Students Manually"):
                with st.form("add_students_form"):
                    student_emails = st.text_area(
                        "Enter student emails (one per line)",
                        height=150
                    )
                    
                    submit = st.form_submit_button("Add Students")
                    
                    if submit and student_emails:
                        # Parse student emails
                        emails = [email.strip() for email in student_emails.split("\n") if email.strip()]
                        
                        if emails:
                            # Mark attendance for these students (as absent) for today
                            today = datetime.now().date().isoformat()
                            
                            for student_email in emails:
                                success, message = mark_attendance(
                                    course_id=course_id,
                                    date=today,
                                    student_email=student_email,
                                    status="Absent"
                                )
                            
                            show_notification(f"Added {len(emails)} students to the course.", "success")
                            st.rerun()
                        else:
                            show_notification("No valid emails provided.", "error")
            
            return
        
        # Select date
        date = st.date_input("Select Date", value=datetime.now().date())
        date_str = date.isoformat()
        
        # Check if attendance already marked for this date
        if date_str in attendance:
            st.info(f"Attendance for {date_str} has already been marked. You can update it below.")
        
        # Create attendance form
        with st.form("mark_attendance_form"):
            st.markdown(f"### Mark Attendance for {date_str}")
            
            # Create attendance inputs for each student
            attendance_data = {}
            
            for student_email in sorted(students):
                # Get current status if available
                current_status = "Present"
                if date_str in attendance and student_email in attendance[date_str]:
                    current_status = attendance[date_str][student_email].get("status", "Present")
                
                # Create radio buttons for status
                status = st.radio(
                    f"Student: {student_email}",
                    options=["Present", "Absent", "Late", "Excused"],
                    index=["Present", "Absent", "Late", "Excused"].index(current_status),
                    key=f"status_{student_email}",
                    horizontal=True
                )
                
                attendance_data[student_email] = status
            
            submit = st.form_submit_button("Save Attendance")
            
            if submit:
                # Mark attendance for each student
                success_count = 0
                
                for student_email, status in attendance_data.items():
                    success, message = mark_attendance(
                        course_id=course_id,
                        date=date_str,
                        student_email=student_email,
                        status=status
                    )
                    
                    if success:
                        success_count += 1
                
                if success_count > 0:
                    show_notification(f"Attendance marked for {success_count} students.", "success")
                else:
                    show_notification("Failed to mark attendance.", "error")

def show_view_attendance(courses):
    """Show interface for viewing attendance."""
    st.markdown("### View Attendance")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="view_course"
    )
    
    if course_id:
        # Get attendance data
        attendance = get_attendance().get(course_id, {})
        
        if not attendance:
            st.info("No attendance records found for this course.")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            # Select date range
            date_range = st.selectbox(
                "Date Range",
                options=["All", "Last Week", "Last Month", "Custom"],
                index=0
            )
            
            if date_range == "Custom":
                start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
                end_date = st.date_input("End Date", value=datetime.now().date())
            else:
                # Calculate date range
                end_date = datetime.now().date()
                
                if date_range == "Last Week":
                    start_date = end_date - timedelta(days=7)
                elif date_range == "Last Month":
                    start_date = end_date - timedelta(days=30)
                else:  # All
                    start_date = datetime.min.date()
        
        with col2:
            # Select student (optional)
            students = set()
            for date, student_records in attendance.items():
                for student_email in student_records.keys():
                    students.add(student_email)
            
            student_filter = st.selectbox(
                "Filter by Student",
                options=["All"] + sorted(list(students)),
                index=0
            )
        
        # Filter attendance data
        filtered_attendance = {}
        
        for date, student_records in attendance.items():
            try:
                date_obj = datetime.fromisoformat(date).date()
                if start_date <= date_obj <= end_date:
                    if student_filter == "All":
                        filtered_attendance[date] = student_records
                    else:
                        if student_filter in student_records:
                            filtered_attendance[date] = {student_filter: student_records[student_filter]}
            except:
                # If date parsing fails, include the data
                if student_filter == "All":
                    filtered_attendance[date] = student_records
                else:
                    if student_filter in student_records:
                        filtered_attendance[date] = {student_filter: student_records[student_filter]}
        
        # Show attendance data
        if filtered_attendance:
            # Prepare data for table
            attendance_data = []
            
            for date, student_records in filtered_attendance.items():
                for student_email, record in student_records.items():
                    attendance_data.append({
                        "Date": date,
                        "Student": student_email,
                        "Status": record.get("status", "Unknown"),
                        "Marked At": format_datetime(record.get("marked_at", ""))
                    })
            
            # Sort by date (newest first) and then by student
            attendance_data.sort(key=lambda x: (x["Date"], x["Student"]), reverse=True)
            
            # Show table
            show_data_table(attendance_data)
            
            # Export option
            if st.button("Export Attendance Data"):
                # Convert to DataFrame
                df = pd.DataFrame(attendance_data)
                
                # Create CSV
                csv = df.to_csv(index=False)
                
                # Offer download
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"attendance_{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No attendance records found for the selected filters.")

def show_attendance_reports(courses):
    """Show attendance reports."""
    st.markdown("### Attendance Reports")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="report_course"
    )
    
    if course_id:
        # Get attendance data
        attendance = get_attendance().get(course_id, {})
        
        if not attendance:
            st.info("No attendance records found for this course.")
            return
        
        # Show attendance summary chart
        st.markdown("#### Attendance Summary")
        
        # Filter attendance data for this course
        course_attendance = {course_id: attendance}
        show_attendance_chart(course_attendance)
        
        # Show attendance by student
        st.markdown("#### Attendance by Student")
        
        # Get unique students
        students = set()
        for date, student_records in attendance.items():
            for student_email in student_records.keys():
                students.add(student_email)
        
        # Calculate attendance statistics by student
        student_stats = {}
        
        for student_email in students:
            student_stats[student_email] = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": 0
            }
            
            for date, student_records in attendance.items():
                if student_email in student_records:
                    status = student_records[student_email].get("status")
                    if status in student_stats[student_email]:
                        student_stats[student_email][status] += 1
                    student_stats[student_email]["Total"] += 1
        
        # Prepare data for table
        student_data = []
        
        for student_email, stats in student_stats.items():
            attendance_rate = (stats["Present"] / stats["Total"]) * 100 if stats["Total"] > 0 else 0
            
            student_data.append({
                "Student": student_email,
                "Present": stats["Present"],
                "Absent": stats["Absent"],
                "Late": stats["Late"],
                "Excused": stats["Excused"],
                "Total": stats["Total"],
                "Attendance Rate (%)": f"{attendance_rate:.2f}%"
            })
        
        # Sort by attendance rate (highest first)
        student_data.sort(key=lambda x: float(x["Attendance Rate (%)"].replace("%", "")), reverse=True)
        
        # Show table
        show_data_table(student_data)
        
        # Show attendance by date
        st.markdown("#### Attendance by Date")
        
        # Calculate attendance statistics by date
        date_stats = {}
        
        for date, student_records in attendance.items():
            date_stats[date] = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": len(student_records)
            }
            
            for student_email, record in student_records.items():
                status = record.get("status")
                if status in date_stats[date]:
                    date_stats[date][status] += 1
        
        # Prepare data for table
        date_data = []
        
        for date, stats in date_stats.items():
            attendance_rate = (stats["Present"] / stats["Total"]) * 100 if stats["Total"] > 0 else 0
            
            date_data.append({
                "Date": date,
                "Present": stats["Present"],
                "Absent": stats["Absent"],
                "Late": stats["Late"],
                "Excused": stats["Excused"],
                "Total": stats["Total"],
                "Attendance Rate (%)": f"{attendance_rate:.2f}%"
            })
        
        # Sort by date (newest first)
        date_data.sort(key=lambda x: x["Date"], reverse=True)
        
        # Show table
        show_data_table(date_data) 