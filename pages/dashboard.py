import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from utils.auth import is_authenticated, role_required
from utils.ui import (
    show_header, show_card, show_metric_card, 
    show_data_table, show_attendance_chart, show_performance_chart, format_datetime
)
from utils.database import (
    get_courses, get_teacher_courses, get_assignments, get_projects,
    get_submissions, get_student_submissions, get_filtered_announcements,
    get_attendance, get_announcements, get_certificates
)

@role_required(["admin", "teacher", "student"])
def show_dashboard():
    """Show the dashboard page."""
    user = st.session_state.user
    email = st.session_state.email
    role = user["role"]
    
    show_header("Dashboard", f"Welcome, {user.get('name', 'User')}!")
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Show announcements
        st.markdown("### Announcements")
        
        # Get announcements for this user
        announcements = get_filtered_announcements(
            role=role, 
            department=user.get("department"), 
            email=email
        )
        
        if announcements:
            # Sort by creation date (newest first)
            announcements.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Display announcements
            for announcement in announcements[:5]:  # Show only the 5 most recent
                with st.expander(f"{announcement.get('title')} - {format_datetime(announcement.get('created_at', ''))}"):
                    st.markdown(announcement.get("content"))
                    st.markdown(f"*Posted by: {announcement.get('author_email')}*")
        else:
            st.info("No announcements available.")
        
        # Show role-specific content
        if role == "admin":
            show_admin_dashboard(user)
        elif role == "teacher":
            show_teacher_dashboard(user, email)
        elif role == "student":
            show_student_dashboard(user, email)

    with col2:
        # Show user profile summary
        st.markdown("### Profile Summary")
        
        st.markdown(f"**Name:** {user.get('name', 'Not set')}")
        st.markdown(f"**Email:** {email}")
        st.markdown(f"**Role:** {role.capitalize()}")
        
        if role == "teacher":
            st.markdown(f"**Department:** {user.get('department', 'Not set')}")
        elif role == "student":
            st.markdown(f"**Student ID:** {user.get('student_id', 'Not set')}")
            st.markdown(f"**Department:** {user.get('department', 'Not set')}")
            st.markdown(f"**Year:** {user.get('year', 'Not set')}")
            st.markdown(f"**Semester:** {user.get('semester', 'Not set')}")
            st.markdown(f"**Section:** {user.get('section', 'Not set')}")
        
        # Quick links
        st.markdown("### Quick Links")
        
        if role == "admin":
            if st.button("Manage Users", use_container_width=True, key="dashboard_manage_users"):
                st.session_state.page = "users"
                st.rerun()
            
            if st.button("Manage Courses", use_container_width=True, key="dashboard_manage_courses"):
                st.session_state.page = "courses"
                st.rerun()
        
        elif role == "teacher":
            if st.button("View Courses", use_container_width=True, key="dashboard_view_courses"):
                st.session_state.page = "my_courses"
                st.rerun()
            
            if st.button("Student Reports", use_container_width=True, key="dashboard_student_reports"):
                st.session_state.page = "student_reports"
                st.rerun()
                
            if st.button("Create Announcement", use_container_width=True, key="dashboard_create_announcement"):
                st.session_state.page = "announcements"
                st.rerun()
        
        elif role == "student":
            if st.button("My Courses", use_container_width=True, key="dashboard_my_courses"):
                st.session_state.page = "my_courses"
                st.rerun()
            
            if st.button("My Performance", use_container_width=True, key="dashboard_my_performance"):
                st.session_state.page = "my_performance"
                st.rerun()

def show_admin_dashboard(user):
    """Show the admin dashboard."""
    # Get data
    courses = get_courses()
    attendance = get_attendance()
    assignments = get_assignments()
    submissions = get_submissions()
    announcements = get_announcements()
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_metric_card("Total Courses", len(courses))
    
    with col2:
        # Count unique students from submissions
        unique_students = set()
        for assignment_id, assignment_submissions in submissions.items():
            for submission in assignment_submissions:
                unique_students.add(submission.get("student_email"))
        
        show_metric_card("Total Students", len(unique_students))
    
    with col3:
        # Count unique teachers from courses
        unique_teachers = set()
        for course_id, course in courses.items():
            unique_teachers.add(course.get("teacher_email"))
        
        show_metric_card("Total Teachers", len(unique_teachers))
    
    with col4:
        show_metric_card("Total Announcements", len(announcements))
    
    # Show recent announcements
    st.markdown("### Recent Announcements")
    
    if announcements:
        # Sort announcements by date (newest first)
        sorted_announcements = sorted(
            announcements, 
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )
        
        # Show the 5 most recent announcements
        for announcement in sorted_announcements[:5]:
            show_card(
                announcement.get("title", "No Title"),
                announcement.get("content", "No Content"),
                color="#4F8BF9"
            )
    else:
        st.info("No announcements available.")
    
    # Show course statistics
    st.markdown("### Course Statistics")
    
    if courses:
        # Prepare data for table
        course_data = []
        for course_id, course in courses.items():
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
                "Assignments": assignment_count,
                "Attendance Records": attendance_count
            })
        
        # Show table
        show_data_table(course_data)
    else:
        st.info("No courses available.")

def show_teacher_dashboard(user, email):
    """Show the teacher dashboard."""
    # Get data
    all_courses = get_courses()
    attendance = get_attendance()
    all_assignments = get_assignments()
    submissions = get_submissions()
    
    # Filter courses taught by this teacher
    courses = {k: v for k, v in all_courses.items() if v.get("teacher_email") == email}
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_metric_card("My Courses", len(courses))
    
    with col2:
        # Count assignments created by this teacher
        assignment_count = 0
        for course_id in courses.keys():
            if course_id in all_assignments:
                assignment_count += len(all_assignments[course_id])
        
        show_metric_card("Assignments", assignment_count)
    
    with col3:
        # Count submissions to this teacher's assignments
        submission_count = 0
        for course_id in courses.keys():
            if course_id in all_assignments:
                for assignment in all_assignments[course_id]:
                    assignment_id = assignment.get("assignment_id")
                    if assignment_id in submissions:
                        submission_count += len(submissions[assignment_id])
        
        show_metric_card("Submissions", submission_count)
    
    with col4:
        # Count attendance records for this teacher's courses
        attendance_count = 0
        for course_id in courses.keys():
            if course_id in attendance:
                for date, records in attendance[course_id].items():
                    attendance_count += len(records)
        
        show_metric_card("Attendance Records", attendance_count)
    
    # Show attendance chart
    st.markdown("### Attendance Summary")
    
    # Filter attendance for this teacher's courses
    teacher_attendance = {k: v for k, v in attendance.items() if k in courses}
    show_attendance_chart(teacher_attendance)
    
    # Show recent submissions
    st.markdown("### Recent Submissions")
    
    # Get recent submissions for this teacher's assignments
    recent_submissions = []
    for course_id in courses.keys():
        if course_id in all_assignments:
            for assignment in all_assignments[course_id]:
                assignment_id = assignment.get("assignment_id")
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        recent_submissions.append({
                            "Course": course_id,
                            "Assignment": assignment.get("title", ""),
                            "Student": submission.get("student_email", ""),
                            "Submitted At": submission.get("submitted_at", ""),
                            "Graded": "Yes" if submission.get("grade") is not None else "No"
                        })
    
    if recent_submissions:
        # Sort by submission date (newest first)
        recent_submissions.sort(key=lambda x: x.get("Submitted At", ""), reverse=True)
        
        # Show the 10 most recent submissions
        show_data_table(recent_submissions[:10])
    else:
        st.info("No submissions available.")

def show_student_dashboard(user, email):
    """Show the student dashboard."""
    # Get data
    all_courses = get_courses()
    attendance = get_attendance()
    all_assignments = get_assignments()
    submissions = get_submissions()
    certificates = get_certificates()
    
    # Get student's department
    department = user.get("department", "")
    
    # Get announcements for students in this department
    announcements = get_filtered_announcements(role="student", department=department)
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Count courses this student is enrolled in (based on attendance)
        enrolled_courses = set()
        for course_id, dates in attendance.items():
            for date, students in dates.items():
                if email in students:
                    enrolled_courses.add(course_id)
        
        show_metric_card("My Courses", len(enrolled_courses))
    
    with col2:
        # Count assignments submitted by this student
        submission_count = 0
        for assignment_id, assignment_submissions in submissions.items():
            for submission in assignment_submissions:
                if submission.get("student_email") == email:
                    submission_count += 1
        
        show_metric_card("Submissions", submission_count)
    
    with col3:
        # Count attendance records for this student
        attendance_count = 0
        for course_id, dates in attendance.items():
            for date, students in dates.items():
                if email in students:
                    attendance_count += 1
        
        show_metric_card("Attendance Records", attendance_count)
    
    with col4:
        # Count certificates submitted by this student
        certificate_count = 0
        if email in certificates:
            certificate_count = len(certificates[email])
        
        show_metric_card("Certificates", certificate_count)
    
    # Show recent announcements
    st.markdown("### Recent Announcements")
    
    if announcements:
        # Sort announcements by date (newest first)
        sorted_announcements = sorted(
            announcements, 
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )
        
        # Show the 5 most recent announcements
        for announcement in sorted_announcements[:5]:
            show_card(
                announcement.get("title", "No Title"),
                announcement.get("content", "No Content"),
                color="#4F8BF9"
            )
    else:
        st.info("No announcements available.")
    
    # Show performance chart
    st.markdown("### My Performance")
    
    # Get student's submissions with grades
    student_submissions = {}
    for assignment_id, assignment_submissions in submissions.items():
        for submission in assignment_submissions:
            if submission.get("student_email") == email:
                student_submissions[assignment_id] = submission
    
    show_performance_chart(student_submissions)
    
    # Show upcoming assignments
    st.markdown("### Upcoming Assignments")
    
    # Get assignments for courses this student is enrolled in
    upcoming_assignments = []
    for course_id in enrolled_courses:
        if course_id in all_assignments:
            for assignment in all_assignments[course_id]:
                assignment_id = assignment.get("assignment_id")
                
                # Check if the assignment is not submitted yet
                submitted = False
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        if submission.get("student_email") == email:
                            submitted = True
                            break
                
                # Check if the due date is in the future
                due_date = assignment.get("due_date", "")
                try:
                    due_datetime = datetime.fromisoformat(due_date)
                    is_upcoming = due_datetime > datetime.now()
                except:
                    is_upcoming = True  # If can't parse date, assume it's upcoming
                
                if not submitted and is_upcoming:
                    upcoming_assignments.append({
                        "Course": course_id,
                        "Title": assignment.get("title", ""),
                        "Due Date": due_date,
                        "Max Points": assignment.get("max_points", 100)
                    })
    
    if upcoming_assignments:
        # Sort by due date (soonest first)
        upcoming_assignments.sort(key=lambda x: x.get("Due Date", ""))
        
        # Show the upcoming assignments
        show_data_table(upcoming_assignments) 