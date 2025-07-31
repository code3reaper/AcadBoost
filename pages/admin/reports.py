import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json

from utils.auth import role_required, get_users
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_datetime
)
from utils.database import (
    get_courses, get_attendance, get_assignments, get_submissions,
    get_projects, get_certificates
)
from pages.admin.department_management import get_departments

@role_required(["admin"])
def show_reports():
    """Show the reports page for administrators."""
    show_header("Reports", "View and generate system reports")
    
    # Create tabs for different report types
    tab1, tab2, tab3, tab4 = st.tabs([
        "Attendance Reports", 
        "Academic Performance", 
        "Department Statistics",
        "System Usage"
    ])
    
    with tab1:
        show_attendance_reports()
    
    with tab2:
        show_academic_performance_reports()
    
    with tab3:
        show_department_statistics()
    
    with tab4:
        show_system_usage_reports()

def show_attendance_reports():
    """Show attendance reports."""
    st.markdown("### Attendance Reports")
    
    # Get data
    courses = get_courses()
    attendance = get_attendance()
    users = get_users()
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        course_id = st.selectbox(
            "Select Course",
            options=["All"] + list(courses.keys()),
            format_func=lambda x: f"{courses[x]['course_name']} ({x})" if x != "All" else "All Courses"
        )
    
    with col2:
        time_period = st.selectbox(
            "Time Period",
            options=["Last Week", "Last Month", "Last Semester", "All Time"],
            index=1
        )
    
    # Calculate date range based on time period
    end_date = datetime.now()
    if time_period == "Last Week":
        start_date = end_date - timedelta(days=7)
    elif time_period == "Last Month":
        start_date = end_date - timedelta(days=30)
    elif time_period == "Last Semester":
        start_date = end_date - timedelta(days=180)
    else:  # All Time
        start_date = datetime.min
    
    # Filter attendance data
    filtered_attendance = {}
    
    if course_id == "All":
        # Include all courses
        for c_id, dates in attendance.items():
            filtered_attendance[c_id] = {}
            for date, students in dates.items():
                try:
                    date_obj = datetime.fromisoformat(date)
                    if start_date <= date_obj <= end_date:
                        filtered_attendance[c_id][date] = students
                except:
                    # If date parsing fails, include the data
                    filtered_attendance[c_id][date] = students
    else:
        # Include only selected course
        if course_id in attendance:
            filtered_attendance[course_id] = {}
            for date, students in attendance[course_id].items():
                try:
                    date_obj = datetime.fromisoformat(date)
                    if start_date <= date_obj <= end_date:
                        filtered_attendance[course_id][date] = students
                except:
                    # If date parsing fails, include the data
                    filtered_attendance[course_id][date] = students
    
    # Calculate attendance statistics
    attendance_stats = {
        "Present": 0,
        "Absent": 0,
        "Late": 0,
        "Excused": 0
    }
    
    for c_id, dates in filtered_attendance.items():
        for date, students in dates.items():
            for student_email, record in students.items():
                status = record.get("status")
                if status in attendance_stats:
                    attendance_stats[status] += 1
    
    # Show attendance pie chart
    st.markdown("#### Attendance Summary")
    
    if sum(attendance_stats.values()) > 0:
        fig = px.pie(
            names=list(attendance_stats.keys()),
            values=list(attendance_stats.values()),
            title="Attendance Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No attendance data available for the selected filters.")
    
    # Show attendance by course bar chart
    if course_id == "All" and filtered_attendance:
        st.markdown("#### Attendance by Course")
        
        course_attendance = {}
        for c_id, dates in filtered_attendance.items():
            course_attendance[c_id] = {
                "Present": 0,
                "Absent": 0,
                "Late": 0,
                "Excused": 0,
                "Total": 0
            }
            
            for date, students in dates.items():
                for student_email, record in students.items():
                    status = record.get("status")
                    if status in course_attendance[c_id]:
                        course_attendance[c_id][status] += 1
                    course_attendance[c_id]["Total"] += 1
        
        # Prepare data for chart
        chart_data = []
        for c_id, stats in course_attendance.items():
            if stats["Total"] > 0:
                course_name = courses.get(c_id, {}).get("course_name", c_id)
                attendance_rate = (stats["Present"] / stats["Total"]) * 100 if stats["Total"] > 0 else 0
                
                chart_data.append({
                    "Course": course_name,
                    "Attendance Rate (%)": attendance_rate
                })
        
        if chart_data:
            df = pd.DataFrame(chart_data)
            fig = px.bar(
                df,
                x="Course",
                y="Attendance Rate (%)",
                title="Attendance Rate by Course",
                color="Attendance Rate (%)",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No attendance data available for courses.")
    
    # Show detailed attendance data
    st.markdown("#### Detailed Attendance Data")
    
    if filtered_attendance:
        # Prepare data for table
        attendance_data = []
        
        for c_id, dates in filtered_attendance.items():
            course_name = courses.get(c_id, {}).get("course_name", c_id)
            
            for date, students in dates.items():
                for student_email, record in students.items():
                    student = users.get(student_email, {})
                    
                    attendance_data.append({
                        "Course": course_name,
                        "Date": date,
                        "Student": student.get("name", student_email),
                        "Status": record.get("status", "Unknown"),
                        "Marked At": format_datetime(record.get("marked_at", ""))
                    })
        
        # Sort by date (newest first)
        attendance_data.sort(key=lambda x: x["Date"], reverse=True)
        
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
                file_name=f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No attendance data available for the selected filters.")

def show_academic_performance_reports():
    """Show academic performance reports."""
    st.markdown("### Academic Performance Reports")
    
    # Get data
    courses = get_courses()
    assignments = get_assignments()
    submissions = get_submissions()
    users = get_users()
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        course_id = st.selectbox(
            "Select Course",
            options=["All"] + list(courses.keys()),
            format_func=lambda x: f"{courses[x]['course_name']} ({x})" if x != "All" else "All Courses",
            key="performance_course"
        )
    
    with col2:
        report_type = st.selectbox(
            "Report Type",
            options=["Grade Distribution", "Student Performance", "Assignment Statistics"],
            index=0
        )
    
    # Show different reports based on selection
    if report_type == "Grade Distribution":
        show_grade_distribution(course_id, courses, assignments, submissions, users)
    
    elif report_type == "Student Performance":
        show_student_performance(course_id, courses, assignments, submissions, users)
    
    elif report_type == "Assignment Statistics":
        show_assignment_statistics(course_id, courses, assignments, submissions, users)

def show_grade_distribution(course_id, courses, assignments, submissions, users):
    """Show grade distribution report."""
    st.markdown("#### Grade Distribution")
    
    # Get all grades
    grades = []
    course_names = {}
    
    if course_id == "All":
        # Include all courses
        for c_id, course_assignments in assignments.items():
            course_names[c_id] = courses.get(c_id, {}).get("course_name", c_id)
            
            for assignment in course_assignments:
                assignment_id = assignment.get("assignment_id")
                max_points = assignment.get("max_points", 100)
                
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        grade = submission.get("grade")
                        if grade is not None:
                            # Calculate percentage
                            percentage = (grade / max_points) * 100
                            
                            grades.append({
                                "Course": course_names[c_id],
                                "Grade (%)": percentage
                            })
    else:
        # Include only selected course
        if course_id in assignments:
            course_names[course_id] = courses.get(course_id, {}).get("course_name", course_id)
            
            for assignment in assignments[course_id]:
                assignment_id = assignment.get("assignment_id")
                max_points = assignment.get("max_points", 100)
                
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        grade = submission.get("grade")
                        if grade is not None:
                            # Calculate percentage
                            percentage = (grade / max_points) * 100
                            
                            grades.append({
                                "Course": course_names[course_id],
                                "Grade (%)": percentage
                            })
    
    if grades:
        # Convert to DataFrame
        df = pd.DataFrame(grades)
        
        # Create histogram
        fig = px.histogram(
            df,
            x="Grade (%)",
            color="Course" if course_id == "All" else None,
            nbins=10,
            title="Grade Distribution",
            labels={"Grade (%)": "Grade (%)", "count": "Number of Students"},
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show grade statistics
        st.markdown("#### Grade Statistics")
        
        if course_id == "All":
            # Group by course
            course_stats = df.groupby("Course")["Grade (%)"].agg(["mean", "median", "min", "max", "count"]).reset_index()
            course_stats.columns = ["Course", "Average", "Median", "Minimum", "Maximum", "Count"]
            
            show_data_table(course_stats)
        else:
            # Overall statistics
            stats = {
                "Average": df["Grade (%)"].mean(),
                "Median": df["Grade (%)"].median(),
                "Minimum": df["Grade (%)"].min(),
                "Maximum": df["Grade (%)"].max(),
                "Count": len(df)
            }
            
            # Show as metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Average", f"{stats['Average']:.2f}%")
            
            with col2:
                st.metric("Median", f"{stats['Median']:.2f}%")
            
            with col3:
                st.metric("Minimum", f"{stats['Minimum']:.2f}%")
            
            with col4:
                st.metric("Maximum", f"{stats['Maximum']:.2f}%")
            
            with col5:
                st.metric("Count", stats["Count"])
    else:
        st.info("No grade data available for the selected course.")

def show_student_performance(course_id, courses, assignments, submissions, users):
    """Show student performance report."""
    st.markdown("#### Student Performance")
    
    # Get student performance data
    student_performance = {}
    
    if course_id == "All":
        # Include all courses
        for c_id, course_assignments in assignments.items():
            course_name = courses.get(c_id, {}).get("course_name", c_id)
            
            for assignment in course_assignments:
                assignment_id = assignment.get("assignment_id")
                assignment_title = assignment.get("title", "")
                max_points = assignment.get("max_points", 100)
                
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        student_email = submission.get("student_email")
                        grade = submission.get("grade")
                        
                        if grade is not None:
                            if student_email not in student_performance:
                                student_performance[student_email] = {
                                    "Student": users.get(student_email, {}).get("name", student_email),
                                    "Assignments": 0,
                                    "Total Points": 0,
                                    "Max Points": 0,
                                    "Average (%)": 0
                                }
                            
                            student_performance[student_email]["Assignments"] += 1
                            student_performance[student_email]["Total Points"] += grade
                            student_performance[student_email]["Max Points"] += max_points
    else:
        # Include only selected course
        if course_id in assignments:
            course_name = courses.get(course_id, {}).get("course_name", course_id)
            
            for assignment in assignments[course_id]:
                assignment_id = assignment.get("assignment_id")
                assignment_title = assignment.get("title", "")
                max_points = assignment.get("max_points", 100)
                
                if assignment_id in submissions:
                    for submission in submissions[assignment_id]:
                        student_email = submission.get("student_email")
                        grade = submission.get("grade")
                        
                        if grade is not None:
                            if student_email not in student_performance:
                                student_performance[student_email] = {
                                    "Student": users.get(student_email, {}).get("name", student_email),
                                    "Assignments": 0,
                                    "Total Points": 0,
                                    "Max Points": 0,
                                    "Average (%)": 0
                                }
                            
                            student_performance[student_email]["Assignments"] += 1
                            student_performance[student_email]["Total Points"] += grade
                            student_performance[student_email]["Max Points"] += max_points
    
    # Calculate averages
    for student_email, data in student_performance.items():
        if data["Max Points"] > 0:
            data["Average (%)"] = (data["Total Points"] / data["Max Points"]) * 100
    
    if student_performance:
        # Convert to list
        performance_data = list(student_performance.values())
        
        # Sort by average (highest first)
        performance_data.sort(key=lambda x: x["Average (%)"], reverse=True)
        
        # Show table
        show_data_table(performance_data)
        
        # Show bar chart of top 10 students
        st.markdown("#### Top 10 Students")
        
        if len(performance_data) > 0:
            top_students = performance_data[:10]
            
            fig = px.bar(
                top_students,
                x="Student",
                y="Average (%)",
                title="Top 10 Students by Average Grade",
                color="Average (%)",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No student performance data available for the selected course.")

def show_assignment_statistics(course_id, courses, assignments, submissions, users):
    """Show assignment statistics report."""
    st.markdown("#### Assignment Statistics")
    
    # Get assignment statistics
    assignment_stats = {}
    
    if course_id == "All":
        # Include all courses
        for c_id, course_assignments in assignments.items():
            course_name = courses.get(c_id, {}).get("course_name", c_id)
            
            for assignment in course_assignments:
                assignment_id = assignment.get("assignment_id")
                assignment_title = assignment.get("title", "")
                max_points = assignment.get("max_points", 100)
                
                key = f"{course_name}: {assignment_title}"
                assignment_stats[key] = {
                    "Course": course_name,
                    "Assignment": assignment_title,
                    "Submissions": 0,
                    "Graded": 0,
                    "Average (%)": 0,
                    "Total Points": 0
                }
                
                if assignment_id in submissions:
                    assignment_stats[key]["Submissions"] = len(submissions[assignment_id])
                    
                    total_points = 0
                    graded_count = 0
                    
                    for submission in submissions[assignment_id]:
                        grade = submission.get("grade")
                        
                        if grade is not None:
                            graded_count += 1
                            total_points += grade
                    
                    assignment_stats[key]["Graded"] = graded_count
                    
                    if graded_count > 0:
                        assignment_stats[key]["Total Points"] = total_points
                        assignment_stats[key]["Average (%)"] = (total_points / (graded_count * max_points)) * 100
    else:
        # Include only selected course
        if course_id in assignments:
            course_name = courses.get(course_id, {}).get("course_name", course_id)
            
            for assignment in assignments[course_id]:
                assignment_id = assignment.get("assignment_id")
                assignment_title = assignment.get("title", "")
                max_points = assignment.get("max_points", 100)
                
                key = assignment_title
                assignment_stats[key] = {
                    "Assignment": assignment_title,
                    "Submissions": 0,
                    "Graded": 0,
                    "Average (%)": 0,
                    "Total Points": 0
                }
                
                if assignment_id in submissions:
                    assignment_stats[key]["Submissions"] = len(submissions[assignment_id])
                    
                    total_points = 0
                    graded_count = 0
                    
                    for submission in submissions[assignment_id]:
                        grade = submission.get("grade")
                        
                        if grade is not None:
                            graded_count += 1
                            total_points += grade
                    
                    assignment_stats[key]["Graded"] = graded_count
                    
                    if graded_count > 0:
                        assignment_stats[key]["Total Points"] = total_points
                        assignment_stats[key]["Average (%)"] = (total_points / (graded_count * max_points)) * 100
    
    if assignment_stats:
        # Convert to list
        stats_data = list(assignment_stats.values())
        
        # Sort by average (highest first)
        stats_data.sort(key=lambda x: x["Average (%)"], reverse=True)
        
        # Show table
        show_data_table(stats_data)
        
        # Show bar chart
        st.markdown("#### Assignment Performance")
        
        if len(stats_data) > 0:
            fig = px.bar(
                stats_data,
                x="Assignment" if course_id != "All" else "Course",
                y="Average (%)",
                title="Assignment Performance",
                color="Average (%)",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show submission rate
            st.markdown("#### Submission Rate")
            
            for stat in stats_data:
                if "Submissions" in stat:
                    stat["Submission Rate (%)"] = (stat["Graded"] / stat["Submissions"]) * 100 if stat["Submissions"] > 0 else 0
            
            fig = px.bar(
                stats_data,
                x="Assignment" if course_id != "All" else "Course",
                y="Submission Rate (%)",
                title="Assignment Submission Rate",
                color="Submission Rate (%)",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No assignment statistics available for the selected course.")

def show_department_statistics():
    """Show department statistics."""
    st.markdown("### Department Statistics")
    
    # Get data
    departments = get_departments()
    courses = get_courses()
    users = get_users()
    
    # Prepare department statistics
    department_stats = {}
    
    for dept_id, dept in departments.items():
        dept_name = dept["name"]
        department_stats[dept_name] = {
            "Department": dept_name,
            "Courses": 0,
            "Teachers": 0,
            "Students": 0,
            "Head of Department": dept["hod_email"]
        }
    
    # Count courses by department
    for course_id, course in courses.items():
        dept_name = course.get("department")
        if dept_name in department_stats:
            department_stats[dept_name]["Courses"] += 1
    
    # Count teachers and students by department
    for email, user in users.items():
        dept_name = user.get("department")
        if dept_name in department_stats:
            if user.get("role") == "teacher":
                department_stats[dept_name]["Teachers"] += 1
            elif user.get("role") == "student":
                department_stats[dept_name]["Students"] += 1
    
    if department_stats:
        # Convert to list
        stats_data = list(department_stats.values())
        
        # Sort by number of students (highest first)
        stats_data.sort(key=lambda x: x["Students"], reverse=True)
        
        # Show table
        show_data_table(stats_data)
        
        # Show bar chart of department sizes
        st.markdown("#### Department Sizes")
        
        # Prepare data for stacked bar chart
        dept_names = [stat["Department"] for stat in stats_data]
        teachers = [stat["Teachers"] for stat in stats_data]
        students = [stat["Students"] for stat in stats_data]
        
        fig = go.Figure(data=[
            go.Bar(name="Teachers", x=dept_names, y=teachers),
            go.Bar(name="Students", x=dept_names, y=students)
        ])
        
        fig.update_layout(
            title="Department Sizes",
            xaxis_title="Department",
            yaxis_title="Count",
            barmode="stack"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show pie chart of course distribution
        st.markdown("#### Course Distribution by Department")
        
        fig = px.pie(
            stats_data,
            names="Department",
            values="Courses",
            title="Course Distribution by Department",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No department statistics available.")

def show_system_usage_reports():
    """Show system usage reports."""
    st.markdown("### System Usage Reports")
    
    # Get data
    users = get_users()
    
    # Calculate user statistics
    user_stats = {
        "admin": 0,
        "teacher": 0,
        "student": 0
    }
    
    user_creation_dates = []
    
    for email, user in users.items():
        role = user.get("role")
        if role in user_stats:
            user_stats[role] += 1
        
        created_at = user.get("created_at")
        if created_at:
            try:
                date = datetime.fromisoformat(created_at).date()
                user_creation_dates.append({
                    "Date": date,
                    "Role": role.capitalize()
                })
            except:
                pass
    
    # Show user statistics
    st.markdown("#### User Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", sum(user_stats.values()))
    
    with col2:
        st.metric("Admins", user_stats["admin"])
    
    with col3:
        st.metric("Teachers", user_stats["teacher"])
    
    with col4:
        st.metric("Students", user_stats["student"])
    
    # Show user pie chart
    fig = px.pie(
        names=[role.capitalize() for role in user_stats.keys()],
        values=list(user_stats.values()),
        title="User Distribution by Role",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show user creation timeline
    if user_creation_dates:
        st.markdown("#### User Creation Timeline")
        
        # Convert to DataFrame
        df = pd.DataFrame(user_creation_dates)
        
        # Group by date and role
        timeline_data = df.groupby(["Date", "Role"]).size().reset_index(name="Count")
        
        # Create line chart
        fig = px.line(
            timeline_data,
            x="Date",
            y="Count",
            color="Role",
            title="User Creation Timeline",
            labels={"Count": "Number of Users Created"},
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Show system activity
    st.markdown("#### System Activity")
    
    st.info("This section would show system activity metrics like logins, page views, etc. This data is not currently being tracked in this demo.") 
