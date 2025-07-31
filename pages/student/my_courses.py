import streamlit as st
import pandas as pd
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_assignments, get_projects,
    get_student_attendance, get_student_submissions
)

@role_required(["student"])
def show_student_courses():
    """Show the courses page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Courses", "View your enrolled courses")
    
    # Get all courses
    courses = get_courses()
    
    # Get student's attendance to determine enrolled courses
    attendance = get_student_attendance(email)
    
    # Get student's submissions
    submissions = get_student_submissions(email)
    
    # Find enrolled courses based on attendance records
    enrolled_courses = {}
    
    for course_id in attendance.keys():
        if course_id in courses:
            enrolled_courses[course_id] = courses[course_id]
    
    # Also check submissions for courses
    for submission in submissions:
        assignment_id = submission.get("assignment_id")
        
        # Find the course for this assignment/project
        for course_id, course_assignments in get_assignments().items():
            for assignment in course_assignments:
                if assignment.get("assignment_id") == assignment_id:
                    if course_id in courses and course_id not in enrolled_courses:
                        enrolled_courses[course_id] = courses[course_id]
        
        for course_id, course_projects in get_projects().items():
            for project in course_projects:
                if project.get("project_id") == assignment_id:
                    if course_id in courses and course_id not in enrolled_courses:
                        enrolled_courses[course_id] = courses[course_id]
    
    if not enrolled_courses:
        st.info("You are not enrolled in any courses yet.")
        return
    
    # Display enrolled courses
    st.markdown("### Enrolled Courses")
    
    # Prepare data for table
    course_data = []
    
    for course_id, course in enrolled_courses.items():
        course_data.append({
            "Course ID": course_id,
            "Course Name": course.get("course_name", "Unknown Course"),
            "Department": course.get("department", "Unknown Department"),
            "Teacher": course.get("teacher_email", "Unknown Teacher"),
            "Credits": course.get("credits", 3)
        })
    
    # Sort by course name
    course_data.sort(key=lambda x: x["Course Name"])
    
    # Show table
    show_data_table(course_data)
    
    # Show course details
    st.markdown("### Course Details")
    
    # Select course
    selected_course = st.selectbox(
        "Select Course",
        options=list(enrolled_courses.keys()),
        format_func=lambda x: f"{enrolled_courses[x].get('course_name', 'Unknown Course')} ({x})"
    )
    
    if selected_course:
        show_course_details(selected_course, enrolled_courses[selected_course], email)

def show_course_details(course_id, course, email):
    """Show details for a specific course."""
    # Create tabs for different course views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Course Info", 
        "Assignments", 
        "Projects", 
        "Attendance"
    ])
    
    with tab1:
        show_course_info(course_id, course)
    
    with tab2:
        show_course_assignments(course_id, email)
    
    with tab3:
        show_course_projects(course_id, email)
    
    with tab4:
        show_course_attendance(course_id, email)

def show_course_info(course_id, course):
    """Show general information about the course."""
    st.markdown("### Course Information")
    
    st.markdown(f"**Course ID:** {course_id}")
    st.markdown(f"**Course Name:** {course.get('course_name', 'Unknown Course')}")
    st.markdown(f"**Department:** {course.get('department', 'Unknown Department')}")
    st.markdown(f"**Teacher:** {course.get('teacher_email', 'Unknown Teacher')}")
    st.markdown(f"**Credits:** {course.get('credits', 3)}")
    
    if course.get("description"):
        st.markdown("### Description")
        st.markdown(course["description"])

def show_course_assignments(course_id, email):
    """Show assignments for the course."""
    st.markdown("### Course Assignments")
    
    # Get assignments for this course
    assignments = get_assignments().get(course_id, [])
    
    if not assignments:
        st.info("No assignments found for this course.")
        return
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    # Prepare data for table
    assignment_data = []
    
    for assignment in assignments:
        assignment_id = assignment.get("assignment_id")
        
        # Check if the assignment is submitted
        submission = None
        for sub in student_submissions:
            if sub.get("assignment_id") == assignment_id:
                submission = sub
                break
        
        assignment_data.append({
            "Title": assignment.get("title", "No Title"),
            "Due Date": format_date(assignment.get("due_date", "")),
            "Max Points": assignment.get("max_points", 100),
            "Status": "Submitted" if submission else "Not Submitted",
            "Grade": submission.get("grade", "Not graded") if submission else "N/A"
        })
    
    # Sort by due date (earliest first)
    assignment_data.sort(key=lambda x: x["Due Date"])
    
    # Show table
    show_data_table(assignment_data)
    
    # Show assignment details
    for i, assignment in enumerate(assignments):
        assignment_id = assignment.get("assignment_id")
        
        # Find submission for this assignment
        submission = None
        for sub in student_submissions:
            if sub.get("assignment_id") == assignment_id:
                submission = sub
                break
        
        with st.expander(f"{assignment.get('title', 'No Title')} - Due: {format_date(assignment.get('due_date', ''))}"):
            st.markdown(f"**Description:** {assignment.get('description', 'No description')}")
            st.markdown(f"**Maximum Points:** {assignment.get('max_points', 100)}")
            
            if submission:
                st.markdown("### Your Submission")
                st.markdown(f"**Submitted At:** {format_datetime(submission.get('submitted_at', ''))}")
                
                if submission.get("grade") is not None:
                    st.markdown(f"**Grade:** {submission['grade']} / {assignment.get('max_points', 100)} ({(submission['grade'] / assignment.get('max_points', 100)) * 100:.2f}%)")
                    st.markdown(f"**Feedback:** {submission.get('feedback', 'No feedback')}")
                else:
                    st.info("This submission has not been graded yet.")
                
                st.text_area(
                    "Submission Text",
                    value=submission.get("submission_text", ""),
                    height=200,
                    disabled=True
                )
                
                if submission.get("file_path"):
                    st.markdown(f"**Uploaded File:** {submission.get('file_path')}")
            else:
                st.warning("You have not submitted this assignment yet.")

def show_course_projects(course_id, email):
    """Show projects for the course."""
    st.markdown("### Course Projects")
    
    # Get projects for this course
    projects = get_projects().get(course_id, [])
    
    if not projects:
        st.info("No projects found for this course.")
        return
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    # Prepare data for table
    project_data = []
    
    for project in projects:
        project_id = project.get("project_id")
        
        # Check if the project is submitted
        submission = None
        for sub in student_submissions:
            if sub.get("assignment_id") == project_id:
                submission = sub
                break
        
        project_data.append({
            "Title": project.get("title", "No Title"),
            "Due Date": format_date(project.get("due_date", "")),
            "Max Points": project.get("max_points", 100),
            "Group Project": "Yes" if project.get("group_project", False) else "No",
            "Status": "Submitted" if submission else "Not Submitted",
            "Grade": submission.get("grade", "Not graded") if submission else "N/A"
        })
    
    # Sort by due date (earliest first)
    project_data.sort(key=lambda x: x["Due Date"])
    
    # Show table
    show_data_table(project_data)
    
    # Show project details
    for i, project in enumerate(projects):
        project_id = project.get("project_id")
        
        # Find submission for this project
        submission = None
        for sub in student_submissions:
            if sub.get("assignment_id") == project_id:
                submission = sub
                break
        
        with st.expander(f"{project.get('title', 'No Title')} - Due: {format_date(project.get('due_date', ''))}"):
            st.markdown(f"**Description:** {project.get('description', 'No description')}")
            st.markdown(f"**Maximum Points:** {project.get('max_points', 100)}")
            st.markdown(f"**Group Project:** {'Yes' if project.get('group_project', False) else 'No'}")
            
            if submission:
                st.markdown("### Your Submission")
                st.markdown(f"**Submitted At:** {format_datetime(submission.get('submitted_at', ''))}")
                
                # Show group members if any
                if submission.get("group_members"):
                    st.markdown(f"**Group Members:** {', '.join(submission.get('group_members', []))}")
                
                if submission.get("grade") is not None:
                    st.markdown(f"**Grade:** {submission['grade']} / {project.get('max_points', 100)} ({(submission['grade'] / project.get('max_points', 100)) * 100:.2f}%)")
                    st.markdown(f"**Feedback:** {submission.get('feedback', 'No feedback')}")
                else:
                    st.info("This submission has not been graded yet.")
                
                st.text_area(
                    "Submission Text",
                    value=submission.get("submission_text", ""),
                    height=200,
                    disabled=True
                )
                
                if submission.get("file_path"):
                    st.markdown(f"**Uploaded File:** {submission.get('file_path')}")
            else:
                st.warning("You have not submitted this project yet.")

def show_course_attendance(course_id, email):
    """Show attendance for the course."""
    st.markdown("### Course Attendance")
    
    # Get student's attendance
    attendance = get_student_attendance(email)
    
    if not attendance or course_id not in attendance:
        st.info("No attendance records found for this course.")
        return
    
    # Get attendance records for this course
    course_attendance = attendance.get(course_id, {})
    
    # Calculate attendance statistics
    attendance_stats = {
        "Present": 0,
        "Absent": 0,
        "Late": 0,
        "Excused": 0,
        "Total": 0
    }
    
    for date, status in course_attendance.items():
        attendance_stats[status] += 1
        attendance_stats["Total"] += 1
    
    # Display attendance statistics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Present", attendance_stats["Present"])
    
    with col2:
        st.metric("Absent", attendance_stats["Absent"])
    
    with col3:
        st.metric("Late", attendance_stats["Late"])
    
    with col4:
        st.metric("Excused", attendance_stats["Excused"])
    
    with col5:
        attendance_rate = (attendance_stats["Present"] / attendance_stats["Total"]) * 100 if attendance_stats["Total"] > 0 else 0
        st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
    
    # Create pie chart for attendance
    import plotly.express as px
    
    fig = px.pie(
        names=["Present", "Absent", "Late", "Excused"],
        values=[attendance_stats["Present"], attendance_stats["Absent"], attendance_stats["Late"], attendance_stats["Excused"]],
        title="Attendance Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed attendance records
    st.markdown("### Detailed Attendance Records")
    
    # Prepare data for table
    attendance_data = []
    
    for date, status in course_attendance.items():
        try:
            formatted_date = format_date(date)
        except:
            formatted_date = date
        
        attendance_data.append({
            "Date": formatted_date,
            "Status": status
        })
    
    # Sort by date (newest first)
    attendance_data.sort(key=lambda x: x["Date"], reverse=True)
    
    # Show table
    show_data_table(attendance_data) 