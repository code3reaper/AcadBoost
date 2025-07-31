import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import base64

from utils.auth import role_required, get_users, get_user_by_email
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_courses, get_teacher_courses, get_assignments, get_projects,
    get_submissions, get_student_attendance, get_student_submissions, get_attendance,
    get_certificates, create_announcement, verify_certificate
)

@role_required(["teacher"])
def show_student_reports():
    """Show the student reports page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("Student Reports", "View detailed student profiles and performance")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Get all users
    users = get_users()
    
    # Filter students
    students = {email: user for email, user in users.items() if user.get("role") == "student"}
    
    if not students:
        st.info("No students found in the system.")
        return
    
    # Create tabs for different report views
    tab1, tab2, tab3 = st.tabs(["Student Profiles", "Class Reports", "Student Certificates"])
    
    with tab1:
        show_student_profiles(courses, students)
    
    with tab2:
        show_class_reports(courses, students)
        
    with tab3:
        show_student_certificates(courses, students)

def show_student_profiles(courses, students):
    """Show individual student profiles."""
    st.markdown("### Student Profiles")
    
    # Get course students
    course_students = {}
    
    # Get all submissions to find students in each course
    submissions = get_submissions()
    
    # Get all assignments and projects
    all_assignments = get_assignments()
    all_projects = get_projects()
    
    # Find students in each course
    for course_id, course in courses.items():
        course_students[course_id] = set()
        
        # Check assignments
        course_assignments = all_assignments.get(course_id, [])
        for assignment in course_assignments:
            assignment_id = assignment.get("assignment_id")
            if assignment_id in submissions:
                for submission in submissions[assignment_id]:
                    student_email = submission.get("student_email")
                    if student_email in students:
                        course_students[course_id].add(student_email)
        
        # Check projects
        course_projects = all_projects.get(course_id, [])
        for project in course_projects:
            project_id = project.get("project_id")
            if project_id in submissions:
                for submission in submissions[project_id]:
                    student_email = submission.get("student_email")
                    if student_email in students:
                        course_students[course_id].add(student_email)
        
        # Check attendance
        attendance = get_attendance()
        if course_id in attendance:
            for date, records in attendance[course_id].items():
                for student_email in records.keys():
                    if student_email in students:
                        course_students[course_id].add(student_email)
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="student_profiles_course"
    )
    
    if course_id:
        # Get students in this course
        course_student_emails = course_students.get(course_id, set())
        
        if not course_student_emails:
            st.info(f"No students found for {courses[course_id].get('course_name', 'this course')}.")
            return
        
        # Prepare student data
        student_data = []
        
        for student_email in course_student_emails:
            student = students.get(student_email, {})
            
            student_data.append({
                "Email": student_email,
                "Name": student.get("name", "Unknown"),
                "Student ID": student.get("student_id", "N/A"),
                "Department": student.get("department", "N/A"),
                "Year": student.get("year", "N/A"),
                "Semester": student.get("semester", "N/A"),
                "Section": student.get("section", "N/A")
            })
        
        # Sort by name
        student_data.sort(key=lambda x: x["Name"])
        
        # Show student table
        show_data_table(student_data)
        
        # Select student
        selected_student = st.selectbox(
            "Select Student",
            options=[s["Email"] for s in student_data],
            format_func=lambda x: f"{next((s['Name'] for s in student_data if s['Email'] == x), 'Unknown')} ({x})"
        )
        
        if selected_student:
            show_student_profile(selected_student, course_id)

def show_student_profile(student_email, course_id):
    """Show detailed profile for a specific student."""
    st.markdown("---")
    
    # Get student details
    student = get_user_by_email(student_email)
    
    if not student:
        st.error("Student not found.")
        return
    
    # Display student information
    st.markdown(f"## {student.get('name', 'Unknown Student')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Email:** {student_email}")
        st.markdown(f"**Student ID:** {student.get('student_id', 'N/A')}")
        st.markdown(f"**Department:** {student.get('department', 'N/A')}")
    
    with col2:
        st.markdown(f"**Year:** {student.get('year', 'N/A')}")
        st.markdown(f"**Semester:** {student.get('semester', 'N/A')}")
        st.markdown(f"**Section:** {student.get('section', 'N/A')}")
    
    # Show resume if available
    if student.get("resume_path") and os.path.exists(student.get("resume_path")):
        st.markdown("### Resume")
        resume_path = student.get("resume_path")
        st.markdown(f"**Resume:** {os.path.basename(resume_path)}")
        
        # Add a download button for the resume
        with open(resume_path, "rb") as file:
            st.download_button(
                label="Download Resume",
                data=file,
                file_name=os.path.basename(resume_path),
                mime="application/pdf"
            )
    
    # Get student's submissions for this course
    student_submissions = get_student_submissions(student_email)
    
    # Get assignments and projects for this course
    course_assignments = get_assignments().get(course_id, [])
    course_projects = get_projects().get(course_id, [])
    
    # Get student's attendance for this course
    attendance = get_student_attendance(student_email)
    course_attendance = attendance.get(course_id, {})
    
    # Calculate attendance statistics
    attendance_stats = {
        "Present": 0,
        "Absent": 0,
        "Late": 0,
        "Excused": 0,
        "Total": 0
    }
    
    for date, record in course_attendance.items():
        # Extract the status string from the record
        if isinstance(record, dict):
            status = record.get("status", "Absent")
        else:
            status = record
            
        if status in attendance_stats:
            attendance_stats[status] += 1
        attendance_stats["Total"] += 1
    
    # Calculate performance statistics
    total_submissions = 0
    graded_submissions = 0
    total_points = 0
    max_total_points = 0
    
    # Check assignments
    assignment_data = []
    for assignment in course_assignments:
        assignment_id = assignment.get("assignment_id")
        
        # Find submission for this assignment
        submission = None
        for sub in student_submissions:
            if sub.get("assignment_id") == assignment_id:
                submission = sub
                break
        
        if submission:
            total_submissions += 1
            
            if submission.get("grade") is not None:
                graded_submissions += 1
                total_points += submission.get("grade", 0)
                max_total_points += assignment.get("max_points", 100)
        
        assignment_data.append({
            "Title": assignment.get("title", "No Title"),
            "Type": "Assignment",
            "Due Date": format_date(assignment.get("due_date", "")),
            "Max Points": assignment.get("max_points", 100),
            "Status": "Submitted" if submission else "Not Submitted",
            "Grade": submission.get("grade", "Not graded") if submission else "N/A",
            "Feedback": submission.get("feedback", "No feedback") if submission else "N/A"
        })
    
    # Check projects
    for project in course_projects:
        project_id = project.get("project_id")
        
        # Find submission for this project
        submission = None
        for sub in student_submissions:
            if sub.get("assignment_id") == project_id:
                submission = sub
                break
        
        if submission:
            total_submissions += 1
            
            if submission.get("grade") is not None:
                graded_submissions += 1
                total_points += submission.get("grade", 0)
                max_total_points += project.get("max_points", 100)
        
        assignment_data.append({
            "Title": project.get("title", "No Title"),
            "Type": "Project",
            "Due Date": format_date(project.get("due_date", "")),
            "Max Points": project.get("max_points", 100),
            "Status": "Submitted" if submission else "Not Submitted",
            "Grade": submission.get("grade", "Not graded") if submission else "N/A",
            "Feedback": submission.get("feedback", "No feedback") if submission else "N/A"
        })
    
    # Calculate overall grade
    overall_grade = (total_points / max_total_points) * 100 if max_total_points > 0 else 0
    
    # Calculate submission rate
    total_assignments = len(course_assignments) + len(course_projects)
    submission_rate = (total_submissions / total_assignments) * 100 if total_assignments > 0 else 0
    
    # Calculate attendance rate
    attendance_rate = (attendance_stats["Present"] / attendance_stats["Total"]) * 100 if attendance_stats["Total"] > 0 else 0
    
    # Display performance metrics
    st.markdown("### Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
    
    with col2:
        st.metric("Submissions", f"{total_submissions}/{len(assignment_data)}" if assignment_data else "0/0")
    
    with col3:
        # Fix: Check if assignment_data is not empty before calculating submission rate
        if assignment_data:
            submission_rate = (total_submissions / len(assignment_data)) * 100 if len(assignment_data) > 0 else 0
        else:
            submission_rate = 0
        st.metric("Submission Rate", f"{submission_rate:.2f}%")
    
    with col4:
        st.metric("Overall Grade", f"{overall_grade:.2f}%")
    
    # Display attendance chart
    st.markdown("### Attendance")
    
    if attendance_stats["Total"] > 0:
        # Create pie chart
        fig = px.pie(
            names=["Present", "Absent", "Late", "Excused"],
            values=[attendance_stats["Present"], attendance_stats["Absent"], attendance_stats["Late"], attendance_stats["Excused"]],
            title="Attendance Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show attendance records
        attendance_data = []
        
        for date, record in course_attendance.items():
            # Extract the status string from the record
            if isinstance(record, dict):
                status = record.get("status", "Absent")
            else:
                status = record
            
            # Format the date safely
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
        
        st.markdown("#### Attendance Records")
        show_data_table(attendance_data)
    else:
        st.info("No attendance records found for this student.")
    
    # Display assignments and projects
    st.markdown("### Assignments and Projects")
    
    if assignment_data:
        # Sort by due date
        assignment_data.sort(key=lambda x: x["Due Date"])
        
        # Show table
        show_data_table(assignment_data)
        
        # Create grade chart for graded assignments
        graded_assignments = [a for a in assignment_data if a["Grade"] != "Not graded" and a["Grade"] != "N/A"]
        
        if graded_assignments:
            # Convert grades to numeric values
            for assignment in graded_assignments:
                # Ensure grade is numeric before calculating percentage
                if isinstance(assignment["Grade"], (int, float)):
                    assignment["Grade (%)"] = (assignment["Grade"] / assignment["Max Points"]) * 100
                else:
                    # Skip this assignment if grade is not numeric
                    continue
            
            # Create bar chart
            fig = px.bar(
                graded_assignments,
                x="Title",
                y="Grade (%)",
                color="Type",
                title="Grades by Assignment/Project",
                labels={"Title": "Assignment/Project", "Grade (%)": "Grade (%)"},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            # Add horizontal line for overall grade
            fig.add_shape(
                type="line",
                x0=-0.5,
                x1=len(graded_assignments) - 0.5,
                y0=overall_grade,
                y1=overall_grade,
                line=dict(color="red", width=2, dash="dash"),
            )
            
            # Add annotation for overall grade
            fig.add_annotation(
                x=len(graded_assignments) - 1,
                y=overall_grade,
                text=f"Overall: {overall_grade:.2f}%",
                showarrow=True,
                arrowhead=1,
                ax=50,
                ay=-30
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No assignments or projects found for this course.")
    
    # Show all submissions by the student
    st.markdown("### All Submissions")
    
    # Get all submissions by this student (not just for this course)
    all_submissions = get_student_submissions(student_email)
    
    if all_submissions:
        # Prepare submission data
        submission_data = []
        
        for submission in all_submissions:
            assignment_id = submission.get("assignment_id", "")
            
            # Determine if this is an assignment or project
            submission_type = "Unknown"
            title = "Unknown"
            course_name = "Unknown"
            max_points = 100
            
            # Check if it's an assignment
            for course_id, assignments in get_assignments().items():
                for assignment in assignments:
                    if assignment.get("assignment_id") == assignment_id:
                        submission_type = "Assignment"
                        title = assignment.get("title", "No Title")
                        course_name = get_courses().get(course_id, {}).get("course_name", "Unknown Course")
                        max_points = assignment.get("max_points", 100)
                        break
            
            # Check if it's a project
            if submission_type == "Unknown":
                for course_id, projects in get_projects().items():
                    for project in projects:
                        if project.get("project_id") == assignment_id:
                            submission_type = "Project"
                            title = project.get("title", "No Title")
                            course_name = get_courses().get(course_id, {}).get("course_name", "Unknown Course")
                            max_points = project.get("max_points", 100)
                            break
            
            # Get feedback safely
            feedback = submission.get("feedback", "No feedback")
            if feedback is None:
                feedback = "No feedback"
            
            submission_data.append({
                "Course": course_name,
                "Type": submission_type,
                "Title": title,
                "Submitted At": format_datetime(submission.get("submitted_at", "")),
                "Grade": submission.get("grade", "Not graded"),
                "Max Points": max_points,
                "Feedback": feedback
            })
        
        # Sort by submission date (newest first)
        submission_data.sort(key=lambda x: x["Submitted At"], reverse=True)
        
        # Show submission table
        show_data_table(submission_data)
    else:
        st.info("No submissions found for this student.")
    
    # Generate PDF Report
    st.markdown("### Generate Report")
    
    if st.button("Generate PDF Report"):
        try:
            # Try using ReportLab instead of pdfkit (no external dependencies)
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            # Create PDF file path
            pdf_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         "data", "reports", f"student_report_{student_email.replace('@', '_').replace('.', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
            
            # Ensure reports directory exists
            os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create content elements
            elements = []
            
            # Add title
            title_style = styles["Heading1"]
            elements.append(Paragraph("Student Report", title_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add student info
            student_name = student.get("name", "Unknown Student")
            elements.append(Paragraph(f"<b>{student_name}</b>", styles["Heading2"]))
            elements.append(Spacer(1, 0.1*inch))
            
            info_style = styles["Normal"]
            elements.append(Paragraph(f"<b>Email:</b> {student_email}", info_style))
            elements.append(Paragraph(f"<b>Student ID:</b> {student.get('student_id', 'N/A')}", info_style))
            elements.append(Paragraph(f"<b>Department:</b> {student.get('department', 'N/A')}", info_style))
            elements.append(Paragraph(f"<b>Year:</b> {student.get('year', 'N/A')}", info_style))
            elements.append(Paragraph(f"<b>Semester:</b> {student.get('semester', 'N/A')}", info_style))
            elements.append(Paragraph(f"<b>Section:</b> {student.get('section', 'N/A')}", info_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add course info
            course_name = get_courses().get(course_id, {}).get("course_name", "Unknown Course")
            elements.append(Paragraph(f"<b>Performance Metrics for {course_name}</b>", styles["Heading3"]))
            elements.append(Spacer(1, 0.1*inch))
            
            # Add performance metrics
            metrics_data = [
                ["Metric", "Value"],
                ["Attendance Rate", f"{attendance_rate:.2f}%"],
                ["Submission Rate", f"{submission_rate:.2f}%"],
                ["Overall Grade", f"{overall_grade:.2f}%"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(metrics_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Add assignments and projects
            elements.append(Paragraph("<b>Assignments and Projects</b>", styles["Heading3"]))
            elements.append(Spacer(1, 0.1*inch))
            
            if assignment_data:
                # Prepare assignment table data
                assignment_table_data = [["Title", "Type", "Due Date", "Status", "Grade", "Feedback"]]
                
                for a in assignment_data:
                    # Ensure feedback is a string and not None
                    feedback = a["Feedback"]
                    if feedback is None:
                        feedback = "No feedback"
                    elif isinstance(feedback, str) and len(feedback) > 30:
                        feedback = feedback[:30] + "..."
                    
                    assignment_table_data.append([
                        a["Title"],
                        a["Type"],
                        a["Due Date"],
                        a["Status"],
                        str(a["Grade"]),
                        feedback
                    ])
                
                # Create assignment table
                assignment_table = Table(assignment_table_data, colWidths=[1.2*inch, 0.8*inch, 1*inch, 0.8*inch, 0.8*inch, 1.4*inch])
                assignment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                
                elements.append(assignment_table)
            else:
                elements.append(Paragraph("No assignments or projects found for this course.", styles["Normal"]))
            
            elements.append(Spacer(1, 0.25*inch))
            
            # Add attendance records
            elements.append(Paragraph("<b>Attendance Records</b>", styles["Heading3"]))
            elements.append(Spacer(1, 0.1*inch))
            
            if attendance_data:
                # Prepare attendance table data
                attendance_table_data = [["Date", "Status"]]
                
                for a in attendance_data:
                    attendance_table_data.append([a["Date"], a["Status"]])
                
                # Create attendance table
                attendance_table = Table(attendance_table_data, colWidths=[2*inch, 2*inch])
                attendance_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                
                elements.append(attendance_table)
            else:
                elements.append(Paragraph("No attendance records found for this student.", styles["Normal"]))
            
            # Add footer
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Italic"]))
            
            # Build PDF
            doc.build(elements)
            
            # Provide download link
            with open(pdf_file_path, "rb") as f:
                st.download_button(
                    label="Download PDF Report",
                    data=f,
                    file_name=os.path.basename(pdf_file_path),
                    mime="application/pdf"
                )
            
            st.success(f"Report generated successfully!")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            st.info("To generate PDF reports, please install reportlab. Run: pip install reportlab")

def show_class_reports(courses, students):
    """Show reports for entire classes."""
    st.markdown("### Class Reports")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="class_reports_course"
    )
    
    if course_id:
        # Get all submissions
        submissions = get_submissions()
        
        # Get assignments and projects for this course
        course_assignments = get_assignments().get(course_id, [])
        course_projects = get_projects().get(course_id, [])
        
        # Get attendance for this course
        attendance = get_attendance()
        course_attendance = attendance.get(course_id, {})
        
        # Find students in this course
        course_students = set()
        
        # Check assignments
        for assignment in course_assignments:
            assignment_id = assignment.get("assignment_id")
            if assignment_id in submissions:
                for submission in submissions[assignment_id]:
                    student_email = submission.get("student_email")
                    if student_email in students:
                        course_students.add(student_email)
        
        # Check projects
        for project in course_projects:
            project_id = project.get("project_id")
            if project_id in submissions:
                for submission in submissions[project_id]:
                    student_email = submission.get("student_email")
                    if student_email in students:
                        course_students.add(student_email)
        
        # Check attendance
        if course_id in attendance:
            for date, records in attendance[course_id].items():
                for student_email in records.keys():
                    if student_email in students:
                        course_students.add(student_email)
        
        if not course_students:
            st.info(f"No students found for {courses[course_id].get('course_name', 'this course')}.")
            return
        
        # Calculate performance for each student
        student_performance = []
        
        for student_email in course_students:
            student = students.get(student_email, {})
            
            # Get student's submissions
            student_submissions = get_student_submissions(student_email)
            
            # Calculate attendance statistics
            student_attendance = {}
            if course_id in attendance:
                for date, records in attendance[course_id].items():
                    if student_email in records:
                        student_attendance[date] = records[student_email].get("status", "Absent")
            
            attendance_stats = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": 0
            }
            
            for date, status in student_attendance.items():
                if status in attendance_stats:
                    attendance_stats[status] += 1
                attendance_stats["Total"] += 1
            
            attendance_rate = (attendance_stats["Present"] / attendance_stats["Total"]) * 100 if attendance_stats["Total"] > 0 else 0
            
            # Calculate performance statistics
            total_submissions = 0
            graded_submissions = 0
            total_points = 0
            max_total_points = 0
            
            # Check assignments
            for assignment in course_assignments:
                assignment_id = assignment.get("assignment_id")
                
                # Find submission for this assignment
                submission = None
                for sub in student_submissions:
                    if sub.get("assignment_id") == assignment_id:
                        submission = sub
                        break
                
                if submission:
                    total_submissions += 1
                    
                    if submission.get("grade") is not None:
                        graded_submissions += 1
                        total_points += submission.get("grade", 0)
                        max_total_points += assignment.get("max_points", 100)
            
            # Check projects
            for project in course_projects:
                project_id = project.get("project_id")
                
                # Find submission for this project
                submission = None
                for sub in student_submissions:
                    if sub.get("assignment_id") == project_id:
                        submission = sub
                        break
                
                if submission:
                    total_submissions += 1
                    
                    if submission.get("grade") is not None:
                        graded_submissions += 1
                        total_points += submission.get("grade", 0)
                        max_total_points += project.get("max_points", 100)
            
            # Calculate overall grade
            overall_grade = (total_points / max_total_points) * 100 if max_total_points > 0 else 0
            
            # Calculate submission rate
            total_assignments = (len(course_assignments) if course_assignments else 0) + (len(course_projects) if course_projects else 0)
            submission_rate = (total_submissions / total_assignments) * 100 if total_assignments > 0 else 0
            
            # Add to student performance
            student_performance.append({
                "Email": student_email,
                "Name": student.get("name", "Unknown"),
                "Student ID": student.get("student_id", "N/A"),
                "Semester": student.get("semester", "N/A"),
                "Section": student.get("section", "N/A"),
                "Attendance Rate (%)": attendance_rate,
                "Submission Rate (%)": submission_rate,
                "Overall Grade (%)": overall_grade
            })
        
        # Sort by overall grade (highest first)
        student_performance.sort(key=lambda x: x["Overall Grade (%)"], reverse=True)
        
        # Show performance table
        st.markdown("#### Student Performance")
        show_data_table(student_performance)
        
        # Create performance charts
        if student_performance:
            # Create scatter plot for attendance vs. grade
            fig = px.scatter(
                student_performance,
                x="Attendance Rate (%)",
                y="Overall Grade (%)",
                hover_name="Name",
                size="Submission Rate (%)",
                color="Overall Grade (%)",
                title="Attendance vs. Performance",
                labels={
                    "Attendance Rate (%)": "Attendance Rate (%)",
                    "Overall Grade (%)": "Overall Grade (%)"
                },
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create grade distribution histogram
            fig = px.histogram(
                student_performance,
                x="Overall Grade (%)",
                nbins=10,
                title="Grade Distribution",
                labels={"Overall Grade (%)": "Grade (%)", "count": "Number of Students"},
                color_discrete_sequence=["#4F8BF9"]
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show top performers
            st.markdown("#### Top Performers")
            
            top_students = pd.DataFrame(student_performance).nlargest(5, "Overall Grade (%)")
            
            fig = px.bar(
                top_students,
                x="Name",
                y="Overall Grade (%)",
                title="Top 5 Students by Overall Grade",
                color="Overall Grade (%)",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show section-wise performance if sections exist
            sections = set(s["Section"] for s in student_performance if s["Section"] != "N/A")
            
            if sections:
                st.markdown("#### Section-wise Performance")
                
                # Calculate section statistics
                section_stats = []
                
                for section in sections:
                    section_students = [s for s in student_performance if s["Section"] == section]
                    
                    if section_students and len(section_students) > 0:
                        avg_attendance = sum(s["Attendance Rate (%)"] for s in section_students) / len(section_students)
                        avg_submission = sum(s["Submission Rate (%)"] for s in section_students) / len(section_students)
                        avg_grade = sum(s["Overall Grade (%)"] for s in section_students) / len(section_students)
                        
                        section_stats.append({
                            "Section": section,
                            "Students": len(section_students),
                            "Avg. Attendance (%)": avg_attendance,
                            "Avg. Submission (%)": avg_submission,
                            "Avg. Grade (%)": avg_grade
                        })
                
                if section_stats:
                    # Sort by average grade
                    section_stats.sort(key=lambda x: x["Avg. Grade (%)"], reverse=True)
                    
                    # Show table
                    show_data_table(section_stats)
                    
                    # Create bar chart
                    fig = px.bar(
                        section_stats,
                        x="Section",
                        y=["Avg. Attendance (%)", "Avg. Submission (%)", "Avg. Grade (%)"],
                        title="Section-wise Performance",
                        barmode="group",
                        labels={
                            "value": "Percentage",
                            "variable": "Metric"
                        },
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Show semester-wise performance if semesters exist
            semesters = set(s["Semester"] for s in student_performance if s["Semester"] != "N/A")
            
            if semesters:
                st.markdown("#### Semester-wise Performance")
                
                # Calculate semester statistics
                semester_stats = []
                
                for semester in semesters:
                    semester_students = [s for s in student_performance if s["Semester"] == semester]
                    
                    if semester_students and len(semester_students) > 0:
                        avg_attendance = sum(s["Attendance Rate (%)"] for s in semester_students) / len(semester_students)
                        avg_submission = sum(s["Submission Rate (%)"] for s in semester_students) / len(semester_students)
                        avg_grade = sum(s["Overall Grade (%)"] for s in semester_students) / len(semester_students)
                        
                        semester_stats.append({
                            "Semester": semester,
                            "Students": len(semester_students),
                            "Avg. Attendance (%)": avg_attendance,
                            "Avg. Submission (%)": avg_submission,
                            "Avg. Grade (%)": avg_grade
                        })
                
                if semester_stats:
                    # Sort by semester
                    semester_stats.sort(key=lambda x: x["Semester"])
                    
                    # Show table
                    show_data_table(semester_stats)
                    
                    # Create bar chart
                    fig = px.bar(
                        semester_stats,
                        x="Semester",
                        y=["Avg. Attendance (%)", "Avg. Submission (%)", "Avg. Grade (%)"],
                        title="Semester-wise Performance",
                        barmode="group",
                        labels={
                            "value": "Percentage",
                            "variable": "Metric"
                        },
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    
                    st.plotly_chart(fig, use_container_width=True) 

def show_student_certificates(courses, students):
    """Show certificates submitted by students and allow requesting specific certificates."""
    st.markdown("### Student Certificates")
    
    # Get all certificates
    all_certificates = get_certificates()
    
    # Find students in teacher's courses
    course_students = set()
    
    # Get all submissions to find students in each course
    submissions = get_submissions()
    
    # Get all assignments and projects
    all_assignments = get_assignments()
    all_projects = get_projects()
    
    # Get attendance
    attendance = get_attendance()
    
    # Find students in each course
    for course_id, course in courses.items():
        # Check assignments
        course_assignments = all_assignments.get(course_id, [])
        for assignment in course_assignments:
            assignment_id = assignment.get("assignment_id")
            if assignment_id in submissions:
                for submission in submissions[assignment_id]:
                    student_email = submission.get("student_email")
                    if student_email in students:
                        course_students.add(student_email)
        
        # Check projects
        course_projects = all_projects.get(course_id, [])
        for project in course_projects:
            project_id = project.get("project_id")
            if project_id in submissions:
                for submission in submissions[project_id]:
                    student_email = submission.get("student_email")
                    if student_email in students:
                        course_students.add(student_email)
        
        # Check attendance
        if course_id in attendance:
            for date, records in attendance[course_id].items():
                for student_email in records.keys():
                    if student_email in students:
                        course_students.add(student_email)
    
    if not course_students:
        st.info("No students found in your courses.")
        return
    
    # Convert to list for selectbox
    course_student_list = list(course_students)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Select student
        selected_student_email = st.selectbox(
            "Select Student",
            options=course_student_list,
            format_func=lambda x: f"{students[x].get('name', 'Unknown')} ({x})",
            key="student_certificates_selectbox"
        )
        
        if selected_student_email:
            selected_student = students[selected_student_email]
            
            # Display student info
            st.markdown(f"**Name:** {selected_student.get('name', 'Unknown')}")
            st.markdown(f"**Email:** {selected_student_email}")
            st.markdown(f"**Department:** {selected_student.get('department', 'N/A')}")
            st.markdown(f"**Year:** {selected_student.get('year', 'N/A')}")
            st.markdown(f"**Semester:** {selected_student.get('semester', 'N/A')}")
            st.markdown(f"**Section:** {selected_student.get('section', 'N/A')}")
            
            # Request certificate section
            st.markdown("### Request Certificate")
            
            with st.form("request_certificate_form"):
                certificate_title = st.text_input("Certificate Title", placeholder="e.g., Python Programming")
                issuing_organization = st.text_input("Issuing Organization", placeholder="e.g., Coursera, Udemy")
                additional_notes = st.text_area("Additional Notes", placeholder="Please provide any specific requirements...")
                
                submit_request = st.form_submit_button("Send Request")
                
                if submit_request:
                    # Create an announcement targeted to this student
                    success, message = create_announcement(
                        title=f"Certificate Request: {certificate_title}",
                        content=f"""
                        Dear Student,
                        
                        Please submit your certificate for {certificate_title} from {issuing_organization}.
                        
                        Additional Notes:
                        {additional_notes}
                        
                        Thank you,
                        {user.get('name', 'Your Teacher')}
                        """,
                        author_email=email,
                        target_roles=["student"],
                        target_emails=[selected_student_email]
                    )
                    
                    if success:
                        st.success(f"Certificate request sent to {selected_student.get('name', 'student')}!")
                    else:
                        st.error(f"Failed to send request: {message}")
    
    with col2:
        if selected_student_email:
            # Get certificates for this student
            student_certificates = []
            
            # Check if student has certificates
            if selected_student_email in all_certificates:
                student_certificates = all_certificates[selected_student_email]
            
            if student_certificates:
                st.markdown("### Submitted Certificates")
                
                # Prepare certificate data for display
                certificate_data = []
                
                for cert in student_certificates:
                    certificate_data.append({
                        "Title": cert.get("title", "No Title"),
                        "Organization": cert.get("issuing_organization", "Unknown"),
                        "Issue Date": cert.get("issue_date", "Unknown"),
                        "Verified": "Yes" if cert.get("verified", False) else "No",
                        "Submitted On": format_datetime(cert.get("submitted_at", "")),
                        "Certificate ID": cert.get("certificate_id", "")
                    })
                
                # Show certificate table
                show_data_table(certificate_data)
                
                # Select certificate for detailed view
                selected_cert_id = st.selectbox(
                    "Select Certificate for Details",
                    options=[cert["Certificate ID"] for cert in certificate_data],
                    format_func=lambda x: next((cert["Title"] for cert in certificate_data if cert["Certificate ID"] == x), "")
                )
                
                if selected_cert_id:
                    # Find the selected certificate
                    selected_cert = next((cert for cert in student_certificates if cert.get("certificate_id") == selected_cert_id), None)
                    
                    if selected_cert:
                        st.markdown("### Certificate Details")
                        
                        # Display certificate details
                        st.markdown(f"**Title:** {selected_cert.get('title', 'No Title')}")
                        st.markdown(f"**Issuing Organization:** {selected_cert.get('issuing_organization', 'Unknown')}")
                        st.markdown(f"**Issue Date:** {selected_cert.get('issue_date', 'Unknown')}")
                        st.markdown(f"**Submitted On:** {format_datetime(selected_cert.get('submitted_at', ''))}")
                        
                        # Display verification status
                        if selected_cert.get("verified", False):
                            st.success("This certificate has been verified.")
                            st.markdown(f"**Verified On:** {format_datetime(selected_cert.get('verified_at', ''))}")
                        else:
                            st.warning("This certificate has not been verified yet.")
                            
                            # Add verify button
                            if st.button("Verify Certificate"):
                                success, message = verify_certificate(selected_student_email, selected_cert_id)
                                
                                if success:
                                    st.success("Certificate verified successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to verify certificate: {message}")
                        
                        # Display certificate file if available
                        if selected_cert.get("file_path") and os.path.exists(selected_cert.get("file_path")):
                            st.markdown("### Certificate File")
                            
                            # Add download button
                            with open(selected_cert.get("file_path"), "rb") as file:
                                st.download_button(
                                    label="Download Certificate",
                                    data=file,
                                    file_name=os.path.basename(selected_cert.get("file_path")),
                                    mime="application/pdf"
                                )
                            
                            # Display PDF preview if it's a PDF
                            if selected_cert.get("file_path").lower().endswith(".pdf"):
                                try:
                                    # Create a base64 encoded version of the PDF
                                    with open(selected_cert.get("file_path"), "rb") as f:
                                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                    
                                    # Display PDF
                                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                    st.markdown(pdf_display, unsafe_allow_html=True)
                                except Exception as e:
                                    st.error(f"Error displaying PDF: {str(e)}")
                            # Display image preview if it's an image
                            elif any(selected_cert.get("file_path").lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                                st.image(selected_cert.get("file_path"))
            else:
                st.info(f"No certificates found for {selected_student.get('name', 'this student')}.")
                
                # Add a note about requesting certificates
                st.markdown("""
                You can request this student to submit specific certificates using the form on the left.
                The request will be sent as an announcement that the student will see when they log in.
                """)
        else:
            st.info("Please select a student to view their certificates.") 