import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    show_performance_chart, format_date, format_datetime
)
from utils.database import (
    get_courses, get_assignments, get_projects,
    get_student_attendance, get_student_submissions, get_student_certificates
)

@role_required(["student"])
def show_my_performance():
    """Show the performance page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Performance", "Track your academic performance")
    
    # Create tabs for different performance views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overall Performance", 
        "Course Performance", 
        "Attendance Analysis",
        "Profile Analysis"
    ])
    
    with tab1:
        show_overall_performance(email)
    
    with tab2:
        show_course_performance(email)
    
    with tab3:
        show_attendance_analysis(email)
        
    with tab4:
        show_profile_analysis(email)

def show_overall_performance(email):
    """Show overall performance for the student."""
    st.markdown("### Overall Performance")
    
    # Get all courses
    courses = get_courses()
    
    # Get all assignments and projects
    all_assignments = get_assignments()
    all_projects = get_projects()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    if not student_submissions:
        st.info("No submission data available to analyze performance.")
        return
    
    # Calculate overall statistics
    total_submissions = len(student_submissions)
    graded_submissions = [s for s in student_submissions if s.get("grade") is not None]
    total_graded = len(graded_submissions)
    
    # Calculate overall grade
    total_points = 0
    max_total_points = 0
    
    for submission in graded_submissions:
        assignment_id = submission.get("assignment_id")
        grade = submission.get("grade", 0)
        
        # Find the assignment/project to get max points
        max_points = 100  # Default
        
        # Check if it's an assignment
        for course_id, assignments in all_assignments.items():
            for assignment in assignments:
                if assignment.get("assignment_id") == assignment_id:
                    max_points = assignment.get("max_points", 100)
                    break
        
        # Check if it's a project
        for course_id, projects in all_projects.items():
            for project in projects:
                if project.get("project_id") == assignment_id:
                    max_points = project.get("max_points", 100)
                    break
        
        total_points += grade
        max_total_points += max_points
    
    # Display overall statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Submissions", total_submissions)
    
    with col2:
        st.metric("Graded Submissions", total_graded)
    
    with col3:
        completion_rate = (total_graded / total_submissions) * 100 if total_submissions > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.2f}%")
    
    with col4:
        overall_grade = (total_points / max_total_points) * 100 if max_total_points > 0 else 0
        st.metric("Overall Grade", f"{overall_grade:.2f}%")
    
    # Create grade distribution chart
    if graded_submissions:
        # Prepare data for chart
        grade_data = []
        
        for submission in graded_submissions:
            assignment_id = submission.get("assignment_id")
            grade = submission.get("grade", 0)
            
            # Find the assignment/project details
            assignment_title = "Unknown"
            assignment_type = "Unknown"
            course_name = "Unknown Course"
            max_points = 100
            
            # Check if it's an assignment
            for course_id, assignments in all_assignments.items():
                for assignment in assignments:
                    if assignment.get("assignment_id") == assignment_id:
                        assignment_title = assignment.get("title", "No Title")
                        assignment_type = "Assignment"
                        course_name = courses.get(course_id, {}).get("course_name", "Unknown Course")
                        max_points = assignment.get("max_points", 100)
                        break
            
            # Check if it's a project
            for course_id, projects in all_projects.items():
                for project in projects:
                    if project.get("project_id") == assignment_id:
                        assignment_title = project.get("title", "No Title")
                        assignment_type = "Project"
                        course_name = courses.get(course_id, {}).get("course_name", "Unknown Course")
                        max_points = project.get("max_points", 100)
                        break
            
            # Calculate percentage
            percentage = (grade / max_points) * 100
            
            grade_data.append({
                "Title": assignment_title,
                "Type": assignment_type,
                "Course": course_name,
                "Grade": grade,
                "Max Points": max_points,
                "Percentage": percentage
            })
        
        # Sort by submission date (newest first)
        grade_data.sort(key=lambda x: x["Percentage"], reverse=True)
        
        # Show grade table
        st.markdown("### Grade Summary")
        show_data_table(grade_data)
        
        # Create bar chart for grades
        fig = plt.figure(figsize=(10, 5))
        sns.barplot(x="Title", y="Percentage", hue="Type", data=pd.DataFrame(grade_data), palette="viridis")
        plt.title("Grades by Assignment/Project")
        plt.xlabel("Assignment/Project")
        plt.ylabel("Grade (%)")
        plt.legend(title="Type")
        st.pyplot(fig)
        
        # Create histogram for grade distribution
        fig = plt.figure(figsize=(10, 5))
        sns.histplot(x="Percentage", data=pd.DataFrame(grade_data), bins=10, kde=True, color="skyblue")
        plt.title("Grade Distribution")
        plt.xlabel("Grade (%)")
        plt.ylabel("Frequency")
        st.pyplot(fig)

def show_course_performance(email):
    """Show performance by course for the student."""
    st.markdown("### Course Performance")
    
    # Get all courses
    courses = get_courses()
    
    # Get all assignments and projects
    all_assignments = get_assignments()
    all_projects = get_projects()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    if not student_submissions:
        st.info("No submission data available to analyze performance.")
        return
    
    # Calculate course statistics
    course_stats = {}
    
    for submission in student_submissions:
        assignment_id = submission.get("assignment_id")
        grade = submission.get("grade")
        
        # Find the course for this assignment/project
        course_id = None
        course_name = "Unknown Course"
        assignment_type = "Unknown"
        max_points = 100
        
        # Check if it's an assignment
        for c_id, assignments in all_assignments.items():
            for assignment in assignments:
                if assignment.get("assignment_id") == assignment_id:
                    course_id = c_id
                    course_name = courses.get(c_id, {}).get("course_name", "Unknown Course")
                    assignment_type = "Assignment"
                    max_points = assignment.get("max_points", 100)
                    break
            if course_id:
                break
        
        # Check if it's a project
        if not course_id:
            for c_id, projects in all_projects.items():
                for project in projects:
                    if project.get("project_id") == assignment_id:
                        course_id = c_id
                        course_name = courses.get(c_id, {}).get("course_name", "Unknown Course")
                        assignment_type = "Project"
                        max_points = project.get("max_points", 100)
                        break
                if course_id:
                    break
        
        if course_id:
            # Initialize course stats if not exists
            if course_id not in course_stats:
                course_stats[course_id] = {
                    "course_name": course_name,
                    "total_submissions": 0,
                    "graded_submissions": 0,
                    "total_points": 0,
                    "max_total_points": 0,
                    "assignments": 0,
                    "projects": 0
                }
            
            # Update course stats
            course_stats[course_id]["total_submissions"] += 1
            
            if assignment_type == "Assignment":
                course_stats[course_id]["assignments"] += 1
            elif assignment_type == "Project":
                course_stats[course_id]["projects"] += 1
            
            if grade is not None:
                course_stats[course_id]["graded_submissions"] += 1
                course_stats[course_id]["total_points"] += grade
                course_stats[course_id]["max_total_points"] += max_points
    
    if not course_stats:
        st.info("No course data available to analyze performance.")
        return
    
    # Prepare data for display
    course_data = []
    
    for course_id, stats in course_stats.items():
        overall_grade = (stats["total_points"] / stats["max_total_points"]) * 100 if stats["max_total_points"] > 0 else 0
        completion_rate = (stats["graded_submissions"] / stats["total_submissions"]) * 100 if stats["total_submissions"] > 0 else 0
        
        course_data.append({
            "Course": stats["course_name"],
            "Submissions": stats["total_submissions"],
            "Graded": stats["graded_submissions"],
            "Assignments": stats["assignments"],
            "Projects": stats["projects"],
            "Completion Rate (%)": completion_rate,
            "Overall Grade (%)": overall_grade
        })
    
    # Sort by overall grade (highest first)
    course_data.sort(key=lambda x: x["Overall Grade (%)"], reverse=True)
    
    # Show course table
    show_data_table(course_data)
    
    # Create bar chart for course grades
    fig = plt.figure(figsize=(10, 5))
    sns.barplot(x="Course", y="Overall Grade (%)", data=pd.DataFrame(course_data), palette="viridis")
    plt.title("Overall Grade by Course")
    plt.xlabel("Course")
    plt.ylabel("Grade (%)")
    st.pyplot(fig)
    
    # Select course for detailed view
    st.markdown("### Course Details")
    
    selected_course = st.selectbox(
        "Select Course",
        options=[c["Course"] for c in course_data]
    )
    
    if selected_course:
        # Find course ID
        course_id = None
        for c_id, stats in course_stats.items():
            if stats["course_name"] == selected_course:
                course_id = c_id
                break
        
        if course_id:
            # Get assignments and projects for this course
            course_assignments = all_assignments.get(course_id, [])
            course_projects = all_projects.get(course_id, [])
            
            # Prepare data for display
            assignment_data = []
            
            # Add assignments
            for assignment in course_assignments:
                assignment_id = assignment.get("assignment_id")
                
                # Find submission for this assignment
                submission = None
                for sub in student_submissions:
                    if sub.get("assignment_id") == assignment_id:
                        submission = sub
                        break
                
                assignment_data.append({
                    "Title": assignment.get("title", "No Title"),
                    "Type": "Assignment",
                    "Due Date": format_date(assignment.get("due_date", "")),
                    "Max Points": assignment.get("max_points", 100),
                    "Status": "Submitted" if submission else "Not Submitted",
                    "Grade": submission.get("grade", "Not graded") if submission else "N/A",
                    "Percentage": (submission.get("grade", 0) / assignment.get("max_points", 100)) * 100 if submission and submission.get("grade") is not None else 0
                })
            
            # Add projects
            for project in course_projects:
                project_id = project.get("project_id")
                
                # Find submission for this project
                submission = None
                for sub in student_submissions:
                    if sub.get("assignment_id") == project_id:
                        submission = sub
                        break
                
                assignment_data.append({
                    "Title": project.get("title", "No Title"),
                    "Type": "Project",
                    "Due Date": format_date(project.get("due_date", "")),
                    "Max Points": project.get("max_points", 100),
                    "Status": "Submitted" if submission else "Not Submitted",
                    "Grade": submission.get("grade", "Not graded") if submission else "N/A",
                    "Percentage": (submission.get("grade", 0) / project.get("max_points", 100)) * 100 if submission and submission.get("grade") is not None else 0
                })
            
            # Sort by due date (earliest first)
            assignment_data.sort(key=lambda x: x["Due Date"])
            
            # Show assignment table
            st.markdown(f"### Assignments and Projects for {selected_course}")
            show_data_table(assignment_data)
            
            # Create bar chart for assignment grades
            graded_assignments = [a for a in assignment_data if a["Status"] == "Submitted" and a["Grade"] != "Not graded"]
            
            if graded_assignments:
                fig = plt.figure(figsize=(10, 5))
                sns.barplot(x="Title", y="Percentage", data=pd.DataFrame(graded_assignments), palette="viridis")
                plt.title(f"Grades for {selected_course}")
                plt.xlabel("Assignment/Project")
                plt.ylabel("Grade (%)")
                st.pyplot(fig)

def show_attendance_analysis(email):
    """Show attendance analysis for the student."""
    st.markdown("### Attendance Analysis")
    
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
    
    course_attendance = {}
    
    for course_id, dates in attendance.items():
        course_name = courses.get(course_id, {}).get("course_name", "Unknown Course")
        
        # Initialize course stats
        if course_name not in course_attendance:
            course_attendance[course_name] = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": 0
            }
        
        for date, status in dates.items():
            # Check if status is a dictionary (which would cause the error)
            if isinstance(status, dict):
                # Extract the actual status from the dictionary
                actual_status = status.get("status", "Present")
            else:
                actual_status = status
                
            # Make sure status is one of the valid keys
            if actual_status not in attendance_stats:
                actual_status = "Present"  # Default to Present if invalid
                
            # Update overall stats
            attendance_stats[actual_status] += 1
            attendance_stats["Total"] += 1
            
            # Update course stats
            course_attendance[course_name][actual_status] += 1
            course_attendance[course_name]["Total"] += 1
    
    # Display overall attendance statistics
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
    
    # Create pie chart for overall attendance
    fig = plt.figure(figsize=(5, 5))
    plt.pie(list(attendance_stats.values()), labels=attendance_stats.keys(), autopct='%1.1f%%', colors=sns.color_palette("viridis"))
    plt.title("Overall Attendance Distribution")
    st.pyplot(fig)
    
    # Display course-wise attendance statistics
    st.markdown("### Course-wise Attendance")
    
    # Prepare data for bar chart
    course_data = []
    
    for course_name, stats in course_attendance.items():
        attendance_rate = (stats["Present"] / stats["Total"]) * 100 if stats["Total"] > 0 else 0
        
        course_data.append({
            "Course": course_name,
            "Present": stats["Present"],
            "Absent": stats["Absent"],
            "Late": stats["Late"],
            "Excused": stats["Excused"],
            "Total": stats["Total"],
            "Attendance Rate (%)": attendance_rate
        })
    
    # Sort by attendance rate (highest first)
    course_data.sort(key=lambda x: x["Attendance Rate (%)"], reverse=True)
    
    # Show table
    show_data_table(course_data)
    
    # Create bar chart for course-wise attendance rate
    fig = plt.figure(figsize=(10, 5))
    sns.barplot(x="Course", y="Attendance Rate (%)", data=pd.DataFrame(course_data), palette="viridis")
    plt.title("Attendance Rate by Course")
    plt.xlabel("Course")
    plt.ylabel("Attendance Rate (%)")
    st.pyplot(fig)
    
    # Create stacked bar chart for attendance status by course
    fig = plt.figure(figsize=(10, 5))
    sns.barplot(x="Course", y="Present", data=pd.DataFrame(course_data), color="skyblue", label="Present")
    sns.barplot(x="Course", y="Absent", data=pd.DataFrame(course_data), color="salmon", label="Absent")
    sns.barplot(x="Course", y="Late", data=pd.DataFrame(course_data), color="lightgreen", label="Late")
    sns.barplot(x="Course", y="Excused", data=pd.DataFrame(course_data), color="pink", label="Excused")
    plt.title("Attendance Status by Course")
    plt.xlabel("Course")
    plt.ylabel("Count")
    plt.legend(title="Status")
    st.pyplot(fig)

def show_profile_analysis(email):
    """Show comprehensive profile analysis for the student."""
    st.markdown("### Complete Profile Analysis")
    
    # Get user information
    user = st.session_state.user
    
    # Get all courses
    courses = get_courses()
    
    # Get all assignments and projects
    all_assignments = get_assignments()
    all_projects = get_projects()
    
    # Get student's submissions
    student_submissions = get_student_submissions(email)
    
    # Get student's attendance
    attendance = get_student_attendance(email)
    
    # Get student's certificates
    certificates = get_student_certificates(email)
    
    if not student_submissions and not attendance:
        st.info("Not enough data available to analyze your profile. Please complete some assignments or attend classes.")
        return
    
    # Calculate overall statistics
    total_submissions = len(student_submissions) if student_submissions else 0
    graded_submissions = [s for s in student_submissions if s.get("grade") is not None] if student_submissions else []
    total_graded = len(graded_submissions)
    
    # Calculate overall grade
    total_points = 0
    max_total_points = 0
    
    for submission in graded_submissions:
        assignment_id = submission.get("assignment_id")
        grade = submission.get("grade", 0)
        
        # Find the assignment/project to get max points
        max_points = 100  # Default
        
        # Check if it's an assignment
        for course_id, assignments in all_assignments.items():
            for assignment in assignments:
                if assignment.get("assignment_id") == assignment_id:
                    max_points = assignment.get("max_points", 100)
                    break
        
        # Check if it's a project
        for course_id, projects in all_projects.items():
            for project in projects:
                if project.get("project_id") == assignment_id:
                    max_points = project.get("max_points", 100)
                    break
        
        total_points += grade
        max_total_points += max_points
    
    overall_grade = (total_points / max_total_points) * 100 if max_total_points > 0 else 0
    completion_rate = (total_graded / total_submissions) * 100 if total_submissions > 0 else 0
    
    # Calculate attendance statistics
    attendance_stats = {
        "Present": 0,
        "Absent": 0,
        "Late": 0,
        "Excused": 0,
        "Total": 0
    }
    
    course_attendance = {}
    
    if attendance:
        for course_id, dates in attendance.items():
            course_name = courses.get(course_id, {}).get("course_name", "Unknown Course")
            
            # Initialize course stats
            if course_name not in course_attendance:
                course_attendance[course_name] = {
                    "Present": 0,
                    "Absent": 0,
                    "Late": 0,
                    "Excused": 0,
                    "Total": 0
                }
            
            for date, status in dates.items():
                # Check if status is a dictionary
                if isinstance(status, dict):
                    actual_status = status.get("status", "Present")
                else:
                    actual_status = status
                    
                # Make sure status is one of the valid keys
                if actual_status not in attendance_stats:
                    actual_status = "Present"  # Default to Present if invalid
                    
                # Update overall stats
                attendance_stats[actual_status] += 1
                attendance_stats["Total"] += 1
                
                # Update course stats
                course_attendance[course_name][actual_status] += 1
                course_attendance[course_name]["Total"] += 1
    
    attendance_rate = (attendance_stats["Present"] / attendance_stats["Total"]) * 100 if attendance_stats["Total"] > 0 else 0
    
    # Calculate course statistics
    course_stats = {}
    
    if student_submissions:
        for submission in student_submissions:
            assignment_id = submission.get("assignment_id")
            grade = submission.get("grade")
            
            # Find the course for this assignment/project
            course_id = None
            course_name = "Unknown Course"
            assignment_type = "Unknown"
            max_points = 100
            
            # Check if it's an assignment
            for c_id, assignments in all_assignments.items():
                for assignment in assignments:
                    if assignment.get("assignment_id") == assignment_id:
                        course_id = c_id
                        course_name = courses.get(c_id, {}).get("course_name", "Unknown Course")
                        assignment_type = "Assignment"
                        max_points = assignment.get("max_points", 100)
                        break
                if course_id:
                    break
            
            # Check if it's a project
            if not course_id:
                for c_id, projects in all_projects.items():
                    for project in projects:
                        if project.get("project_id") == assignment_id:
                            course_id = c_id
                            course_name = courses.get(c_id, {}).get("course_name", "Unknown Course")
                            assignment_type = "Project"
                            max_points = project.get("max_points", 100)
                            break
                    if course_id:
                        break
            
            if course_id:
                # Initialize course stats if not exists
                if course_id not in course_stats:
                    course_stats[course_id] = {
                        "course_name": course_name,
                        "total_submissions": 0,
                        "graded_submissions": 0,
                        "total_points": 0,
                        "max_total_points": 0,
                        "assignments": 0,
                        "projects": 0
                    }
                
                # Update course stats
                course_stats[course_id]["total_submissions"] += 1
                
                if assignment_type == "Assignment":
                    course_stats[course_id]["assignments"] += 1
                elif assignment_type == "Project":
                    course_stats[course_id]["projects"] += 1
                
                if grade is not None:
                    course_stats[course_id]["graded_submissions"] += 1
                    course_stats[course_id]["total_points"] += grade
                    course_stats[course_id]["max_total_points"] += max_points
    
    # Prepare course performance data
    course_performance = []
    
    for course_id, stats in course_stats.items():
        course_grade = (stats["total_points"] / stats["max_total_points"]) * 100 if stats["max_total_points"] > 0 else 0
        course_completion = (stats["graded_submissions"] / stats["total_submissions"]) * 100 if stats["total_submissions"] > 0 else 0
        
        course_performance.append({
            "course_name": stats["course_name"],
            "submissions": stats["total_submissions"],
            "graded": stats["graded_submissions"],
            "assignments": stats["assignments"],
            "projects": stats["projects"],
            "completion_rate": course_completion,
            "grade": course_grade
        })
    
    # Display summary metrics
    st.markdown("#### Profile Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Grade", f"{overall_grade:.2f}%")
    
    with col2:
        st.metric("Completion Rate", f"{completion_rate:.2f}%")
    
    with col3:
        st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
    
    with col4:
        st.metric("Courses", len(course_stats))
    
    # Show the performance chart
    st.markdown("### Performance Trends")
    show_performance_chart(course_performance)
    
    # Remove AI analysis
    # show_ai_analysis_button(profile_data, "profile") 