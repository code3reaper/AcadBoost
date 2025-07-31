import streamlit as st
import pandas as pd
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_teacher_courses, get_course_assignments, get_course_attendance,
    get_assignments, get_projects, get_submissions, mark_attendance, remove_student_from_course
)

@role_required(["teacher"])
def show_teacher_courses():
    """Show the teacher's courses page."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Courses", "Manage and view your assigned courses")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Display courses
    st.markdown("### Your Courses")
    
    # Prepare course data for display
    course_data = []
    
    for course_id, course in courses.items():
        course_data.append({
            "Course ID": course_id,
            "Course Name": course.get("course_name", "No Name"),
            "Department": course.get("department", "N/A"),
            "Credits": course.get("credits", 3),
            "Created": format_datetime(course.get("created_at", ""))
        })
    
    # Sort by course name
    course_data.sort(key=lambda x: x["Course Name"])
    
    # Show course table
    show_data_table(course_data)
    
    # Select course for details
    selected_course = st.selectbox(
        "Select Course for Details",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})"
    )
    
    if selected_course:
        show_course_details(selected_course, courses[selected_course])

def show_course_details(course_id, course):
    """Show details for a selected course."""
    st.markdown("---")
    
    st.markdown(f"## {course.get('course_name', 'No Name')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Course ID:** {course_id}")
        st.markdown(f"**Department:** {course.get('department', 'N/A')}")
    
    with col2:
        st.markdown(f"**Credits:** {course.get('credits', 3)}")
        st.markdown(f"**Created:** {format_datetime(course.get('created_at', ''))}")
    
    if course.get("description"):
        st.markdown(f"**Description:** {course.get('description')}")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Assignments & Projects", "Students", "Attendance"])
    
    with tab1:
        show_course_assignments(course_id)
    
    with tab2:
        show_course_students(course_id)
    
    with tab3:
        show_course_attendance(course_id)

def show_course_assignments(course_id):
    """Show assignments and projects for a course."""
    st.markdown("### Assignments")
    
    # Get assignments for this course
    assignments = get_assignments().get(course_id, [])
    
    if assignments:
        # Prepare assignment data
        assignment_data = []
        
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            
            # Get submissions for this assignment
            submissions = get_submissions().get(assignment_id, [])
            
            # Calculate statistics
            total_submissions = len(submissions)
            graded_submissions = len([s for s in submissions if s.get("grade") is not None])
            
            assignment_data.append({
                "Title": assignment.get("title", "No Title"),
                "Due Date": format_date(assignment.get("due_date", "")),
                "Max Points": assignment.get("max_points", 100),
                "Submissions": total_submissions,
                "Graded": graded_submissions
            })
        
        # Sort by due date
        assignment_data.sort(key=lambda x: x["Due Date"])
        
        # Show assignment table
        show_data_table(assignment_data)
    else:
        st.info("No assignments found for this course.")
    
    st.markdown("### Projects")
    
    # Get projects for this course
    projects = get_projects().get(course_id, [])
    
    if projects:
        # Prepare project data
        project_data = []
        
        for project in projects:
            project_id = project.get("project_id")
            
            # Get submissions for this project
            submissions = get_submissions().get(project_id, [])
            
            # Calculate statistics
            total_submissions = len(submissions)
            graded_submissions = len([s for s in submissions if s.get("grade") is not None])
            
            project_data.append({
                "Title": project.get("title", "No Title"),
                "Due Date": format_date(project.get("due_date", "")),
                "Max Points": project.get("max_points", 100),
                "Group Project": "Yes" if project.get("group_project") else "No",
                "Submissions": total_submissions,
                "Graded": graded_submissions
            })
        
        # Sort by due date
        project_data.sort(key=lambda x: x["Due Date"])
        
        # Show project table
        show_data_table(project_data)
    else:
        st.info("No projects found for this course.")

def show_course_students(course_id):
    """Show students enrolled in a course."""
    st.markdown("### Students")
    
    # Get all submissions to find students in this course
    submissions = get_submissions()
    
    # Get all assignments and projects for this course
    assignments = get_assignments().get(course_id, [])
    projects = get_projects().get(course_id, [])
    
    # Get attendance for this course
    attendance = get_course_attendance(course_id)
    
    # Find students in this course
    student_emails = set()
    
    # Check assignments
    for assignment in assignments:
        assignment_id = assignment.get("assignment_id")
        if assignment_id in submissions:
            for submission in submissions[assignment_id]:
                student_emails.add(submission.get("student_email"))
    
    # Check projects
    for project in projects:
        project_id = project.get("project_id")
        if project_id in submissions:
            for submission in submissions[project_id]:
                student_emails.add(submission.get("student_email"))
    
    # Check attendance
    for date, records in attendance.items():
        for student_email in records.keys():
            student_emails.add(student_email)
    
    # Get student details
    from utils.auth import get_users
    users = get_users()
    
    # Prepare student data
    student_data = []
    
    for email in student_emails:
        student = users.get(email, {})
        
        if student.get("role") == "student":
            student_data.append({
                "Email": email,
                "Name": student.get("name", "Unknown"),
                "Student ID": student.get("student_id", "N/A"),
                "Department": student.get("department", "N/A"),
                "Year": student.get("year", "N/A"),
                "Semester": student.get("semester", "N/A"),
                "Section": student.get("section", "N/A")
            })
    
    # Sort by name
    student_data.sort(key=lambda x: x["Name"])
    
    # Create tabs for viewing and managing students
    tab1, tab2 = st.tabs(["View Students", "Manage Students"])
    
    with tab1:
        # Show student table
        if student_data:
            show_data_table(student_data)
            
            # Show student count
            st.markdown(f"**Total Students:** {len(student_data)}")
        else:
            st.info("No students found for this course.")
    
    with tab2:
        st.markdown("### Add Students")
        
        # Get all students
        all_students = {email: user for email, user in users.items() if user.get("role") == "student"}
        
        # Filter out students already in the course
        available_students = {email: user for email, user in all_students.items() if email not in student_emails}
        
        if available_students:
            # Create a list of students to display
            student_options = [f"{user.get('name', 'Unknown')} ({email})" for email, user in available_students.items()]
            
            # Allow selecting multiple students
            selected_students = st.multiselect(
                "Select Students to Add",
                options=student_options
            )
            
            if selected_students:
                # Extract emails from selected options
                selected_emails = [option.split("(")[-1].strip(")") for option in selected_students]
                
                # Add button
                if st.button("Add Selected Students"):
                    # Mark attendance for these students (as absent) for today
                    today = datetime.now().date().isoformat()
                    
                    for student_email in selected_emails:
                        success, message = mark_attendance(
                            course_id=course_id,
                            date=today,
                            student_email=student_email,
                            status="Absent"
                        )
                    
                    show_notification(f"Added {len(selected_emails)} students to the course.", "success")
                    st.rerun()
        else:
            st.info("All students are already enrolled in this course.")
        
        st.markdown("### Add Students Manually")
        
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
        
        st.markdown("### Remove Students")
        
        if student_data:
            # Create a list of students to display
            student_options = [f"{student['Name']} ({student['Email']})" for student in student_data]
            
            # Allow selecting multiple students
            selected_students = st.multiselect(
                "Select Students to Remove",
                options=student_options,
                key="remove_students"
            )
            
            if selected_students:
                # Extract emails from selected options
                selected_emails = [option.split("(")[-1].strip(")") for option in selected_students]
                
                # Remove button
                if st.button("Remove Selected Students"):
                    # Remove button
                    for student_email in selected_emails:
                        success, message = remove_student_from_course(
                            course_id=course_id,
                            student_email=student_email
                        )
                    
                    show_notification(f"Removed {len(selected_emails)} students from the course.", "success")
                    st.rerun()
        else:
            st.info("No students found for this course.")

def show_course_attendance(course_id):
    """Show attendance for a course."""
    st.markdown("### Attendance")
    
    # Get attendance for this course
    attendance = get_course_attendance(course_id)
    
    if attendance:
        # Get dates
        dates = sorted(attendance.keys(), reverse=True)
        
        # Select date
        selected_date = st.selectbox("Select Date", options=dates)
        
        if selected_date:
            # Get attendance for this date
            date_attendance = attendance.get(selected_date, {})
            
            if date_attendance:
                # Prepare attendance data
                attendance_data = []
                
                for student_email, record in date_attendance.items():
                    # Get student details
                    from utils.auth import get_user_by_email
                    student = get_user_by_email(student_email)
                    
                    attendance_data.append({
                        "Email": student_email,
                        "Name": student.get("name", "Unknown") if student else "Unknown",
                        "Student ID": student.get("student_id", "N/A") if student else "N/A",
                        "Status": record.get("status", "N/A"),
                        "Marked At": format_datetime(record.get("marked_at", ""))
                    })
                
                # Sort by name
                attendance_data.sort(key=lambda x: x["Name"])
                
                # Show attendance table
                show_data_table(attendance_data)
                
                # Show attendance statistics
                statuses = {"Present": 0, "Absent": 0, "Late": 0, "Excused": 0}
                
                for record in attendance_data:
                    status = record.get("Status")
                    if status in statuses:
                        statuses[status] += 1
                
                # Display statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Present", statuses["Present"])
                
                with col2:
                    st.metric("Absent", statuses["Absent"])
                
                with col3:
                    st.metric("Late", statuses["Late"])
                
                with col4:
                    st.metric("Excused", statuses["Excused"])
                
                # Create pie chart
                import plotly.express as px
                
                fig = px.pie(
                    names=list(statuses.keys()),
                    values=list(statuses.values()),
                    title=f"Attendance for {selected_date}",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No attendance records found for this date.")
    else:
        st.info("No attendance records found for this course.") 