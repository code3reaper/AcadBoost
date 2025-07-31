import streamlit as st
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table, show_card,
    format_datetime
)
from utils.database import (
    get_courses, get_teacher_courses, get_attendance, get_assignments,
    get_submissions
)

@role_required(["teacher"])
def show_teacher_courses():
    """Show the courses page for teachers."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Courses", "Manage your courses")
    
    # Get teacher's courses
    courses = get_teacher_courses(email)
    
    if not courses:
        st.info("You are not assigned to any courses yet. Please contact the administrator.")
        return
    
    # Show course overview
    st.markdown("### Course Overview")
    
    # Create course cards
    col1, col2 = st.columns(2)
    
    for i, (course_id, course) in enumerate(courses.items()):
        with col1 if i % 2 == 0 else col2:
            with st.expander(f"{course.get('course_name', 'No Name')} ({course_id})", expanded=True):
                st.markdown(f"**Department:** {course.get('department', 'N/A')}")
                st.markdown(f"**Credits:** {course.get('credits', 3)}")
                
                if course.get('description'):
                    st.markdown(f"**Description:** {course.get('description')}")
                
                # Show course actions
                if st.button(f"View Course Details", key=f"view_{course_id}"):
                    st.session_state.selected_course = course_id
                    st.session_state.course_view = "details"
                    st.rerun()
    
    # Show selected course details if any
    if "selected_course" in st.session_state and "course_view" in st.session_state:
        show_course_details(st.session_state.selected_course, courses)

def show_course_details(course_id, courses):
    """Show details for a specific course."""
    course = courses.get(course_id, {})
    
    st.markdown("---")
    st.markdown(f"## {course.get('course_name', 'No Name')} ({course_id})")
    
    # Create tabs for different course views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Course Info", 
        "Students", 
        "Assignments",
        "Performance"
    ])
    
    with tab1:
        show_course_info(course_id, course)
    
    with tab2:
        show_course_students(course_id)
    
    with tab3:
        show_course_assignments(course_id)
    
    with tab4:
        show_course_performance(course_id)

def show_course_info(course_id, course):
    """Show course information."""
    st.markdown("### Course Information")
    
    # Course details
    st.markdown(f"**Course ID:** {course_id}")
    st.markdown(f"**Course Name:** {course.get('course_name', 'No Name')}")
    st.markdown(f"**Department:** {course.get('department', 'N/A')}")
    st.markdown(f"**Credits:** {course.get('credits', 3)}")
    
    if course.get('description'):
        st.markdown(f"**Description:** {course.get('description')}")
    
    st.markdown(f"**Created At:** {format_datetime(course.get('created_at', ''))}")
    
    # Course statistics
    st.markdown("### Course Statistics")
    
    # Get data
    attendance = get_attendance().get(course_id, {})
    assignments = get_assignments().get(course_id, [])
    
    # Calculate statistics
    student_count = 0
    attendance_count = 0
    
    for date, students in attendance.items():
        student_count = max(student_count, len(students))
        attendance_count += len(students)
    
    # Show statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Students", student_count)
    
    with col2:
        st.metric("Attendance Records", attendance_count)
    
    with col3:
        st.metric("Assignments", len(assignments))

def show_course_students(course_id):
    """Show students enrolled in the course."""
    st.markdown("### Course Students")
    
    # Get data
    attendance = get_attendance().get(course_id, {})
    
    # Get unique students from attendance
    students = set()
    for date, student_records in attendance.items():
        for student_email in student_records.keys():
            students.add(student_email)
    
    if students:
        # Prepare data for table
        student_data = []
        
        for student_email in students:
            # Count attendance
            present_count = 0
            absent_count = 0
            late_count = 0
            excused_count = 0
            
            for date, student_records in attendance.items():
                if student_email in student_records:
                    status = student_records[student_email].get("status")
                    if status == "Present":
                        present_count += 1
                    elif status == "Absent":
                        absent_count += 1
                    elif status == "Late":
                        late_count += 1
                    elif status == "Excused":
                        excused_count += 1
            
            total_count = present_count + absent_count + late_count + excused_count
            attendance_rate = (present_count / total_count) * 100 if total_count > 0 else 0
            
            student_data.append({
                "Student Email": student_email,
                "Present": present_count,
                "Absent": absent_count,
                "Late": late_count,
                "Excused": excused_count,
                "Attendance Rate (%)": f"{attendance_rate:.2f}%"
            })
        
        # Sort by attendance rate (highest first)
        student_data.sort(key=lambda x: float(x["Attendance Rate (%)"].replace("%", "")), reverse=True)
        
        # Show table
        show_data_table(student_data)
    else:
        st.info("No students have attendance records for this course.")

def show_course_assignments(course_id):
    """Show assignments for the course."""
    st.markdown("### Course Assignments")
    
    # Get data
    assignments = get_assignments().get(course_id, [])
    submissions = get_submissions()
    
    if assignments:
        # Create new assignment button
        if st.button("Create New Assignment"):
            st.session_state.creating_assignment = True
        
        # Show assignment creation form
        if st.session_state.get("creating_assignment", False):
            with st.form("create_assignment_form"):
                st.markdown("#### Create New Assignment")
                
                title = st.text_input("Title")
                description = st.text_area("Description")
                due_date = st.date_input("Due Date")
                max_points = st.number_input("Maximum Points", min_value=1, max_value=100, value=100)
                
                submit = st.form_submit_button("Create Assignment")
                
                if submit:
                    if not title:
                        show_notification("Please enter a title for the assignment.", "error")
                    else:
                        # Format due date
                        due_date_str = due_date.isoformat()
                        
                        # Create assignment
                        from utils.database import create_assignment
                        success, message, assignment_id = create_assignment(
                            course_id=course_id,
                            title=title,
                            description=description,
                            due_date=due_date_str,
                            max_points=max_points
                        )
                        
                        if success:
                            show_notification(message, "success")
                            st.session_state.creating_assignment = False
                            st.rerun()
                        else:
                            show_notification(message, "error")
        
        # Show assignments
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            
            with st.expander(f"{assignment.get('title', 'No Title')} - Due: {assignment.get('due_date', 'No Date')}"):
                st.markdown(f"**Description:** {assignment.get('description', 'No description')}")
                st.markdown(f"**Maximum Points:** {assignment.get('max_points', 100)}")
                st.markdown(f"**Created At:** {format_datetime(assignment.get('created_at', ''))}")
                
                # Show submissions
                if assignment_id in submissions:
                    st.markdown(f"**Submissions:** {len(submissions[assignment_id])}")
                    
                    # Prepare submission data
                    submission_data = []
                    
                    for submission in submissions[assignment_id]:
                        submission_data.append({
                            "Student": submission.get("student_email", "Unknown"),
                            "Submitted At": format_datetime(submission.get("submitted_at", "")),
                            "Grade": submission.get("grade", "Not graded"),
                            "Feedback": submission.get("feedback", "No feedback")
                        })
                    
                    # Show submission table
                    show_data_table(submission_data)
                    
                    # Grade submissions
                    if st.button(f"Grade Submissions for {assignment.get('title')}", key=f"grade_{assignment_id}"):
                        st.session_state.grading_assignment = assignment_id
                        st.session_state.grading_submissions = submissions[assignment_id]
                        st.rerun()
                else:
                    st.markdown("**Submissions:** 0")
                    st.info("No submissions for this assignment yet.")
    else:
        st.info("No assignments created for this course yet.")
    
    # Show grading interface if selected
    if "grading_assignment" in st.session_state and "grading_submissions" in st.session_state:
        show_grading_interface(
            course_id,
            st.session_state.grading_assignment,
            st.session_state.grading_submissions
        )

def show_grading_interface(course_id, assignment_id, submissions):
    """Show interface for grading submissions."""
    st.markdown("---")
    st.markdown("### Grade Submissions")
    
    # Get assignment details
    assignments = get_assignments().get(course_id, [])
    assignment = next((a for a in assignments if a.get("assignment_id") == assignment_id), {})
    
    st.markdown(f"**Assignment:** {assignment.get('title', 'No Title')}")
    st.markdown(f"**Maximum Points:** {assignment.get('max_points', 100)}")
    
    # Create tabs for each submission
    if submissions:
        tabs = st.tabs([f"Student: {s.get('student_email', 'Unknown')}" for s in submissions])
        
        for i, (tab, submission) in enumerate(zip(tabs, submissions)):
            with tab:
                student_email = submission.get("student_email", "Unknown")
                
                st.markdown(f"**Submission Text:**")
                st.text_area(
                    "Submission",
                    value=submission.get("submission_text", "No text"),
                    height=200,
                    key=f"submission_text_{i}",
                    disabled=True
                )
                
                if submission.get("file_path"):
                    st.markdown(f"**File:** {submission.get('file_path')}")
                
                st.markdown(f"**Submitted At:** {format_datetime(submission.get('submitted_at', ''))}")
                
                # Grading form
                with st.form(f"grade_form_{i}"):
                    current_grade = submission.get("grade")
                    current_feedback = submission.get("feedback", "")
                    
                    grade = st.number_input(
                        "Grade",
                        min_value=0,
                        max_value=assignment.get("max_points", 100),
                        value=current_grade if current_grade is not None else 0,
                        key=f"grade_input_{i}"
                    )
                    
                    feedback = st.text_area(
                        "Feedback",
                        value=current_feedback,
                        key=f"feedback_input_{i}"
                    )
                    
                    submit = st.form_submit_button("Submit Grade")
                    
                    if submit:
                        # Grade submission
                        from utils.database import grade_submission
                        success, message = grade_submission(
                            assignment_id=assignment_id,
                            student_email=student_email,
                            grade=grade,
                            feedback=feedback
                        )
                        
                        if success:
                            show_notification(message, "success")
                        else:
                            show_notification(message, "error")
        
        # Button to return to assignments
        if st.button("Return to Assignments"):
            del st.session_state.grading_assignment
            del st.session_state.grading_submissions
            st.rerun()
    else:
        st.info("No submissions to grade.")

def show_course_performance(course_id):
    """Show performance statistics for the course."""
    st.markdown("### Course Performance")
    
    # Get data
    assignments = get_assignments().get(course_id, [])
    submissions = get_submissions()
    
    if assignments:
        # Calculate performance statistics
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
                "Assignment": title,
                "Submissions": submission_count,
                "Graded": graded_count,
                "Average (%)": f"{average:.2f}%"
            })
        
        # Show assignment statistics
        st.markdown("#### Assignment Statistics")
        show_data_table(assignment_stats)
        
        # Show grade distribution
        st.markdown("#### Grade Distribution")
        
        # Collect all grades
        all_grades = []
        
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
                            "Grade (%)": percentage
                        })
        
        if all_grades:
            # Convert to DataFrame
            import pandas as pd
            df = pd.DataFrame(all_grades)
            
            # Create histogram
            import plotly.express as px
            fig = px.histogram(
                df,
                x="Grade (%)",
                nbins=10,
                title="Grade Distribution",
                labels={"Grade (%)": "Grade (%)", "count": "Number of Students"},
                color_discrete_sequence=["#4F8BF9"]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No grades available for this course.")
    else:
        st.info("No assignments created for this course yet.") 