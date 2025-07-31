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
    get_courses, get_teacher_courses, get_attendance, get_assignments,
    get_submissions, get_projects
)

@role_required(["teacher"])
def show_student_performance():
    """Show the student performance page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("Student Performance", "Analyze and track student performance")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Create tabs for different performance views
    tab1, tab2, tab3 = st.tabs([
        "Course Performance", 
        "Student Analysis", 
        "Comparative Reports"
    ])
    
    with tab1:
        show_course_performance(courses)
    
    with tab2:
        show_student_analysis(courses)
    
    with tab3:
        show_comparative_reports(courses)

def show_course_performance(courses):
    """Show performance statistics for courses."""
    st.markdown("### Course Performance")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="course_performance"
    )
    
    if course_id:
        # Get data
        assignments = get_assignments().get(course_id, [])
        projects = get_projects().get(course_id, [])
        submissions = get_submissions()
        attendance = get_attendance().get(course_id, {})
        
        # Show course overview
        st.markdown("#### Course Overview")
        
        # Calculate statistics
        total_assignments = len(assignments)
        total_projects = len(projects)
        
        # Get unique students from attendance
        students = set()
        for date, student_records in attendance.items():
            for student_email in student_records.keys():
                students.add(student_email)
        
        total_students = len(students)
        
        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Students", total_students)
        
        with col2:
            st.metric("Assignments", total_assignments)
        
        with col3:
            st.metric("Projects", total_projects)
        
        with col4:
            # Calculate average attendance rate
            attendance_rate = 0
            if attendance:
                present_count = 0
                total_count = 0
                
                for date, student_records in attendance.items():
                    for student_email, record in student_records.items():
                        total_count += 1
                        if record.get("status") == "Present":
                            present_count += 1
                
                attendance_rate = (present_count / total_count) * 100 if total_count > 0 else 0
            
            st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
        
        # Show grade distribution
        st.markdown("#### Grade Distribution")
        
        # Collect all grades
        all_grades = []
        
        # Add assignment grades
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            max_points = assignment.get("max_points", 100)
            
            if assignment_id in submissions:
                for submission in submissions[assignment_id]:
                    grade = submission.get("grade")
                    
                    if grade is not None:
                        # Calculate percentage
                        percentage = (grade / max_points) * 100
                        
                        all_grades.append({
                            "Student": submission.get("student_email", "Unknown"),
                            "Assignment": assignment.get("title", "No Title"),
                            "Type": "Assignment",
                            "Grade (%)": percentage
                        })
        
        # Add project grades
        for project in projects:
            project_id = project.get("project_id")
            max_points = project.get("max_points", 100)
            
            if project_id in submissions:
                for submission in submissions[project_id]:
                    grade = submission.get("grade")
                    
                    if grade is not None:
                        # Calculate percentage
                        percentage = (grade / max_points) * 100
                        
                        all_grades.append({
                            "Student": submission.get("student_email", "Unknown"),
                            "Assignment": project.get("title", "No Title"),
                            "Type": "Project",
                            "Grade (%)": percentage
                        })
        
        if all_grades:
            # Convert to DataFrame
            df = pd.DataFrame(all_grades)
            
            # Create histogram
            fig = px.histogram(
                df,
                x="Grade (%)",
                color="Type",
                nbins=10,
                title="Grade Distribution",
                labels={"Grade (%)": "Grade (%)", "count": "Number of Submissions"},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show grade statistics
            st.markdown("#### Grade Statistics")
            
            # Group by type
            type_stats = df.groupby("Type")["Grade (%)"].agg(["mean", "median", "min", "max", "count"]).reset_index()
            type_stats.columns = ["Type", "Average", "Median", "Minimum", "Maximum", "Count"]
            
            show_data_table(type_stats)
            
            # Show overall statistics
            st.markdown("#### Overall Statistics")
            
            overall_stats = {
                "Average": df["Grade (%)"].mean(),
                "Median": df["Grade (%)"].median(),
                "Minimum": df["Grade (%)"].min(),
                "Maximum": df["Grade (%)"].max(),
                "Count": len(df)
            }
            
            # Show as metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Average", f"{overall_stats['Average']:.2f}%")
            
            with col2:
                st.metric("Median", f"{overall_stats['Median']:.2f}%")
            
            with col3:
                st.metric("Minimum", f"{overall_stats['Minimum']:.2f}%")
            
            with col4:
                st.metric("Maximum", f"{overall_stats['Maximum']:.2f}%")
            
            with col5:
                st.metric("Count", overall_stats["Count"])
        else:
            st.info("No grade data available for this course.")
        
        # Show assignment performance
        st.markdown("#### Assignment Performance")
        
        # Calculate assignment statistics
        assignment_stats = []
        
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            title = assignment.get("title", "No Title")
            max_points = assignment.get("max_points", 100)
            
            # Count submissions and calculate average grade
            submission_count = 0
            graded_count = 0
            total_points = 0
            
            if assignment_id in submissions:
                submission_count = len(submissions[assignment_id])
                
                for submission in submissions[assignment_id]:
                    grade = submission.get("grade")
                    
                    if grade is not None:
                        graded_count += 1
                        total_points += grade
            
            # Calculate average
            average = (total_points / (graded_count * max_points)) * 100 if graded_count > 0 else 0
            
            assignment_stats.append({
                "Title": title,
                "Type": "Assignment",
                "Submissions": submission_count,
                "Graded": graded_count,
                "Average (%)": average
            })
        
        # Add project statistics
        for project in projects:
            project_id = project.get("project_id")
            title = project.get("title", "No Title")
            max_points = project.get("max_points", 100)
            
            # Count submissions and calculate average grade
            submission_count = 0
            graded_count = 0
            total_points = 0
            
            if project_id in submissions:
                submission_count = len(submissions[project_id])
                
                for submission in submissions[project_id]:
                    grade = submission.get("grade")
                    
                    if grade is not None:
                        graded_count += 1
                        total_points += grade
            
            # Calculate average
            average = (total_points / (graded_count * max_points)) * 100 if graded_count > 0 else 0
            
            assignment_stats.append({
                "Title": title,
                "Type": "Project",
                "Submissions": submission_count,
                "Graded": graded_count,
                "Average (%)": average
            })
        
        if assignment_stats:
            # Sort by average (highest first)
            assignment_stats.sort(key=lambda x: x["Average (%)"], reverse=True)
            
            # Show table
            show_data_table(assignment_stats)
            
            # Create bar chart
            df = pd.DataFrame(assignment_stats)
            
            fig = px.bar(
                df,
                x="Title",
                y="Average (%)",
                color="Type",
                title="Assignment and Project Performance",
                labels={"Title": "Assignment/Project", "Average (%)": "Average Grade (%)"},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assignment or project data available for this course.")

def show_student_analysis(courses):
    """Show analysis for individual students."""
    st.markdown("### Student Analysis")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="student_analysis_course"
    )
    
    if course_id:
        # Get data
        assignments = get_assignments().get(course_id, [])
        projects = get_projects().get(course_id, [])
        submissions = get_submissions()
        attendance = get_attendance().get(course_id, {})
        
        # Get unique students from attendance
        students = set()
        for date, student_records in attendance.items():
            for student_email in student_records.keys():
                students.add(student_email)
        
        # Add students from submissions
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            if assignment_id in submissions:
                for submission in submissions[assignment_id]:
                    students.add(submission.get("student_email"))
        
        for project in projects:
            project_id = project.get("project_id")
            if project_id in submissions:
                for submission in submissions[project_id]:
                    students.add(submission.get("student_email"))
        
        if not students:
            st.info("No students found for this course.")
            return
        
        # Select student
        student_email = st.selectbox(
            "Select Student",
            options=sorted(list(students)),
            key="student_analysis_student"
        )
        
        if student_email:
            st.markdown(f"#### Performance Analysis for {student_email}")
            
            # Calculate attendance statistics
            attendance_stats = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": 0
            }
            
            for date, student_records in attendance.items():
                if student_email in student_records:
                    status = student_records[student_email].get("status")
                    if status in attendance_stats:
                        attendance_stats[status] += 1
                    attendance_stats["Total"] += 1
            
            # Calculate attendance rate
            attendance_rate = (attendance_stats["Present"] / attendance_stats["Total"]) * 100 if attendance_stats["Total"] > 0 else 0
            
            # Show attendance statistics
            st.markdown("#### Attendance")
            
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
                st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
            
            # Get student's submissions
            student_submissions = []
            
            # Add assignment submissions
            for assignment in assignments:
                assignment_id = assignment.get("assignment_id")
                title = assignment.get("title", "No Title")
                max_points = assignment.get("max_points", 100)
                due_date = assignment.get("due_date", "")
                
                submission_found = False
                
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        if submission.get("student_email") == student_email:
                            submission_found = True
                            grade = submission.get("grade")
                            grade_percentage = (grade / max_points) * 100 if grade is not None else None
                            
                            student_submissions.append({
                                "Title": title,
                                "Type": "Assignment",
                                "Due Date": due_date,
                                "Submitted At": submission.get("submitted_at", ""),
                                "Grade": grade,
                                "Grade (%)": grade_percentage,
                                "Max Points": max_points,
                                "Feedback": submission.get("feedback", "")
                            })
                            break
                
                if not submission_found:
                    student_submissions.append({
                        "Title": title,
                        "Type": "Assignment",
                        "Due Date": due_date,
                        "Submitted At": "Not Submitted",
                        "Grade": None,
                        "Grade (%)": None,
                        "Max Points": max_points,
                        "Feedback": ""
                    })
            
            # Add project submissions
            for project in projects:
                project_id = project.get("project_id")
                title = project.get("title", "No Title")
                max_points = project.get("max_points", 100)
                due_date = project.get("due_date", "")
                
                submission_found = False
                
                if project_id in submissions:
                    for submission in submissions[project_id]:
                        if submission.get("student_email") == student_email:
                            submission_found = True
                            grade = submission.get("grade")
                            grade_percentage = (grade / max_points) * 100 if grade is not None else None
                            
                            student_submissions.append({
                                "Title": title,
                                "Type": "Project",
                                "Due Date": due_date,
                                "Submitted At": submission.get("submitted_at", ""),
                                "Grade": grade,
                                "Grade (%)": grade_percentage,
                                "Max Points": max_points,
                                "Feedback": submission.get("feedback", "")
                            })
                            break
                
                if not submission_found:
                    student_submissions.append({
                        "Title": title,
                        "Type": "Project",
                        "Due Date": due_date,
                        "Submitted At": "Not Submitted",
                        "Grade": None,
                        "Grade (%)": None,
                        "Max Points": max_points,
                        "Feedback": ""
                    })
            
            # Show submissions
            st.markdown("#### Submissions")
            
            if student_submissions:
                # Sort by due date
                student_submissions.sort(key=lambda x: x["Due Date"])
                
                # Show table
                show_data_table(student_submissions)
                
                # Calculate overall grade
                graded_submissions = [s for s in student_submissions if s["Grade"] is not None]
                
                if graded_submissions:
                    total_points = sum(s["Grade"] for s in graded_submissions)
                    max_total_points = sum(s["Max Points"] for s in graded_submissions)
                    overall_grade = (total_points / max_total_points) * 100 if max_total_points > 0 else 0
                    
                    st.markdown("#### Overall Grade")
                    st.metric("Overall Grade", f"{overall_grade:.2f}%")
                    
                    # Create grade chart
                    grades_df = pd.DataFrame([s for s in student_submissions if s["Grade (%)"] is not None])
                    
                    if not grades_df.empty:
                        fig = px.bar(
                            grades_df,
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
                            x1=len(grades_df) - 0.5,
                            y0=overall_grade,
                            y1=overall_grade,
                            line=dict(color="red", width=2, dash="dash"),
                        )
                        
                        # Add annotation for overall grade
                        fig.add_annotation(
                            x=len(grades_df) - 1,
                            y=overall_grade,
                            text=f"Overall: {overall_grade:.2f}%",
                            showarrow=True,
                            arrowhead=1,
                            ax=50,
                            ay=-30
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No graded submissions available for this student.")
            else:
                st.info("No submissions available for this student.")

def show_comparative_reports(courses):
    """Show comparative reports across students."""
    st.markdown("### Comparative Reports")
    
    # Select course
    course_id = st.selectbox(
        "Select Course",
        options=list(courses.keys()),
        format_func=lambda x: f"{courses[x].get('course_name', 'No Name')} ({x})",
        key="comparative_course"
    )
    
    if course_id:
        # Get data
        assignments = get_assignments().get(course_id, [])
        projects = get_projects().get(course_id, [])
        submissions = get_submissions()
        attendance = get_attendance().get(course_id, {})
        
        # Get unique students
        students = set()
        for date, student_records in attendance.items():
            for student_email in student_records.keys():
                students.add(student_email)
        
        # Add students from submissions
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            if assignment_id in submissions:
                for submission in submissions[assignment_id]:
                    students.add(submission.get("student_email"))
        
        for project in projects:
            project_id = project.get("project_id")
            if project_id in submissions:
                for submission in submissions[project_id]:
                    students.add(submission.get("student_email"))
        
        if not students:
            st.info("No students found for this course.")
            return
        
        # Calculate student performance
        student_performance = {}
        
        for student_email in students:
            student_performance[student_email] = {
                "Student": student_email,
                "Assignments Submitted": 0,
                "Projects Submitted": 0,
                "Total Points": 0,
                "Max Points": 0,
                "Overall Grade (%)": 0,
                "Attendance Rate (%)": 0
            }
            
            # Calculate attendance rate
            present_count = 0
            total_attendance = 0
            
            for date, student_records in attendance.items():
                if student_email in student_records:
                    total_attendance += 1
                    if student_records[student_email].get("status") == "Present":
                        present_count += 1
            
            attendance_rate = (present_count / total_attendance) * 100 if total_attendance > 0 else 0
            student_performance[student_email]["Attendance Rate (%)"] = attendance_rate
            
            # Calculate assignment grades
            for assignment in assignments:
                assignment_id = assignment.get("assignment_id")
                max_points = assignment.get("max_points", 100)
                
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        if submission.get("student_email") == student_email:
                            student_performance[student_email]["Assignments Submitted"] += 1
                            
                            grade = submission.get("grade")
                            if grade is not None:
                                student_performance[student_email]["Total Points"] += grade
                                student_performance[student_email]["Max Points"] += max_points
            
            # Calculate project grades
            for project in projects:
                project_id = project.get("project_id")
                max_points = project.get("max_points", 100)
                
                if project_id in submissions:
                    for submission in submissions[project_id]:
                        if submission.get("student_email") == student_email:
                            student_performance[student_email]["Projects Submitted"] += 1
                            
                            grade = submission.get("grade")
                            if grade is not None:
                                student_performance[student_email]["Total Points"] += grade
                                student_performance[student_email]["Max Points"] += max_points
            
            # Calculate overall grade
            if student_performance[student_email]["Max Points"] > 0:
                overall_grade = (student_performance[student_email]["Total Points"] / student_performance[student_email]["Max Points"]) * 100
                student_performance[student_email]["Overall Grade (%)"] = overall_grade
        
        # Convert to list
        performance_data = list(student_performance.values())
        
        # Sort by overall grade (highest first)
        performance_data.sort(key=lambda x: x["Overall Grade (%)"], reverse=True)
        
        # Show performance table
        st.markdown("#### Student Performance Comparison")
        
        if performance_data:
            show_data_table(performance_data)
            
            # Create performance chart
            df = pd.DataFrame(performance_data)
            
            if not df.empty and "Overall Grade (%)" in df.columns and "Attendance Rate (%)" in df.columns:
                # Create scatter plot
                fig = px.scatter(
                    df,
                    x="Attendance Rate (%)",
                    y="Overall Grade (%)",
                    hover_name="Student",
                    size="Assignments Submitted",
                    color="Projects Submitted",
                    title="Attendance vs. Performance",
                    labels={
                        "Attendance Rate (%)": "Attendance Rate (%)",
                        "Overall Grade (%)": "Overall Grade (%)"
                    },
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create grade distribution
                fig = px.histogram(
                    df,
                    x="Overall Grade (%)",
                    nbins=10,
                    title="Grade Distribution",
                    labels={"Overall Grade (%)": "Overall Grade (%)", "count": "Number of Students"},
                    color_discrete_sequence=["#4F8BF9"]
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show top performers
                st.markdown("#### Top Performers")
                
                top_students = df.nlargest(5, "Overall Grade (%)")
                
                fig = px.bar(
                    top_students,
                    x="Student",
                    y="Overall Grade (%)",
                    title="Top 5 Students by Overall Grade",
                    color="Overall Grade (%)",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available for this course.") 