import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime, show_performance_chart
)
from utils.database import (
    get_student_submissions, get_student_attendance,
    get_student_certificates, get_student_courses,
    get_student_exam_results, get_exams, get_subjects
)
from utils.ai_analysis import analyze_with_gemini

@role_required(["student"])
def show_student_performance():
    """Show the performance page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Performance", "View and analyze your academic performance")
    
    # Create tabs for different performance views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Submissions", "Attendance", "Certificates", "AI Analysis"
    ])
    
    with tab1:
        show_performance_overview(email, user)
    
    with tab2:
        show_submissions_performance(email, user)
    
    with tab3:
        show_attendance_performance(email, user)
    
    with tab4:
        show_certificates_performance(email, user)
    
    with tab5:
        show_performance_ai_analysis(email, user)

def show_performance_overview(email, user):
    """Show performance overview."""
    st.markdown("### Performance Overview")
    
    # Get student data
    submissions = get_student_submissions(email)
    attendance = get_student_attendance(email)
    certificates = get_student_certificates(email)
    courses = get_student_courses(email)
    exam_results = get_student_exam_results(email)
    exams = get_exams()
    subjects = get_subjects()
    
    # Calculate performance metrics
    total_submissions = len(submissions)
    graded_submissions = sum(1 for s in submissions if s.get("grade") is not None)
    completion_rate = (graded_submissions / total_submissions) * 100 if total_submissions > 0 else 0
    
    total_attendance = sum(len(a.get("sessions", [])) for a in attendance.values())
    present_sessions = sum(sum(1 for s in a.get("sessions", []) if s.get("status") == "present") for a in attendance.values())
    attendance_rate = (present_sessions / total_attendance) * 100 if total_attendance > 0 else 0
    
    total_certificates = len(certificates)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Courses", len(courses))
    
    with col2:
        st.metric("Completion Rate", f"{completion_rate:.2f}%")
    
    with col3:
        st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
    
    with col4:
        st.metric("Certificates", total_certificates)
    
    # Show performance chart
    st.markdown("### Performance Chart")
    
    # Prepare data for chart
    chart_data = {
        "Submissions": completion_rate,
        "Attendance": attendance_rate,
        "Certificates": min(total_certificates * 10, 100)  # Scale certificates to percentage
    }
    
    # Add exam performance if available
    if exam_results:
        exam_percentages = []
        
        for exam_id, subject_results in exam_results.items():
            if exam_id in exams:
                exam = exams[exam_id]
                
                # Calculate total and percentage
                total_marks = 0
                max_total = 0
                
                for subject_id, result in subject_results.items():
                    if subject_id in subjects:
                        total_marks += result.get("marks", 0)
                        max_total += exam.get("max_marks", 100)
                
                percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
                exam_percentages.append(percentage)
        
        if exam_percentages:
            chart_data["Exams"] = sum(exam_percentages) / len(exam_percentages)
    
    # Show chart
    show_performance_chart(chart_data)
    
    # Show recent activity
    st.markdown("### Recent Activity")
    
    # Combine recent submissions and attendance
    recent_activity = []
    
    # Add recent submissions
    for submission in submissions[:5]:
        recent_activity.append({
            "Date": format_datetime(submission.get("submission_date", "")),
            "Activity": f"Submitted assignment for {submission.get('course_name', 'Unknown')}",
            "Status": "Graded" if submission.get("grade") is not None else "Pending"
        })
    
    # Add recent attendance
    for course_id, course_attendance in attendance.items():
        for session in course_attendance.get("sessions", [])[:3]:
            recent_activity.append({
                "Date": format_date(session.get("date", "")),
                "Activity": f"Attended {course_attendance.get('course_name', 'Unknown')}",
                "Status": session.get("status", "Unknown").capitalize()
            })
    
    # Sort by date (newest first)
    recent_activity.sort(key=lambda x: x["Date"], reverse=True)
    
    # Show recent activity table
    if recent_activity:
        show_data_table(recent_activity[:10])
    else:
        st.info("No recent activity found.")

def show_submissions_performance(email, user):
    """Show submissions performance."""
    st.markdown("### Submissions Performance")
    
    # Get student submissions
    submissions = get_student_submissions(email)
    
    if not submissions:
        st.info("No submissions found.")
        return
    
    # Calculate submission metrics
    total_submissions = len(submissions)
    graded_submissions = sum(1 for s in submissions if s.get("grade") is not None)
    completion_rate = (graded_submissions / total_submissions) * 100 if total_submissions > 0 else 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Submissions", total_submissions)
    
    with col2:
        st.metric("Graded Submissions", graded_submissions)
    
    with col3:
        st.metric("Completion Rate", f"{completion_rate:.2f}%")
    
    # Prepare data for display
    submission_data = []
    
    for submission in submissions:
        submission_data.append({
            "Course": submission.get("course_name", "Unknown"),
            "Assignment": submission.get("assignment_name", "Unknown"),
            "Submission Date": format_datetime(submission.get("submission_date", "")),
            "Due Date": format_datetime(submission.get("due_date", "")),
            "Status": "Graded" if submission.get("grade") is not None else "Pending",
            "Grade": submission.get("grade", "N/A"),
            "Feedback": submission.get("feedback", "N/A")
        })
    
    # Sort by submission date (newest first)
    submission_data.sort(key=lambda x: x["Submission Date"], reverse=True)
    
    # Show submissions table
    show_data_table(submission_data)
    
    # Create visualizations
    if submission_data:
        # Create pie chart for submission status
        st.markdown("### Submission Status")
        
        status_counts = {
            "Graded": graded_submissions,
            "Pending": total_submissions - graded_submissions
        }
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
        
        # Create bar chart for grades (if available)
        if graded_submissions > 0:
            st.markdown("### Grade Distribution")
            
            # Extract grades
            grades = [s.get("grade", 0) for s in submissions if s.get("grade") is not None]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(grades, bins=10, alpha=0.7)
            ax.set_title("Grade Distribution")
            ax.set_xlabel("Grade")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)

def show_attendance_performance(email, user):
    """Show attendance performance."""
    st.markdown("### Attendance Performance")
    
    # Get student attendance
    attendance = get_student_attendance(email)
    
    if not attendance:
        st.info("No attendance records found.")
        return
    
    # Calculate attendance metrics
    total_sessions = sum(len(a.get("sessions", [])) for a in attendance.values())
    present_sessions = sum(sum(1 for s in a.get("sessions", []) if s.get("status") == "present") for a in attendance.values())
    absent_sessions = sum(sum(1 for s in a.get("sessions", []) if s.get("status") == "absent") for a in attendance.values())
    late_sessions = sum(sum(1 for s in a.get("sessions", []) if s.get("status") == "late") for a in attendance.values())
    
    attendance_rate = (present_sessions / total_sessions) * 100 if total_sessions > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Sessions", total_sessions)
    
    with col2:
        st.metric("Present", present_sessions)
    
    with col3:
        st.metric("Absent", absent_sessions)
    
    with col4:
        st.metric("Late", late_sessions)
    
    with col5:
        st.metric("Attendance Rate", f"{attendance_rate:.2f}%")
    
    # Create visualizations
    if total_sessions > 0:
        # Create pie chart for attendance status
        st.markdown("### Attendance Status")
        
        status_counts = {
            "Present": present_sessions,
            "Absent": absent_sessions,
            "Late": late_sessions
        }
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
    
    # Show course-wise attendance
    st.markdown("### Course-wise Attendance")
    
    # Prepare data for display
    course_attendance = []
    
    for course_id, course_data in attendance.items():
        course_sessions = len(course_data.get("sessions", []))
        course_present = sum(1 for s in course_data.get("sessions", []) if s.get("status") == "present")
        course_rate = (course_present / course_sessions) * 100 if course_sessions > 0 else 0
        
        course_attendance.append({
            "Course": course_data.get("course_name", "Unknown"),
            "Total Sessions": course_sessions,
            "Present": course_present,
            "Absent": sum(1 for s in course_data.get("sessions", []) if s.get("status") == "absent"),
            "Late": sum(1 for s in course_data.get("sessions", []) if s.get("status") == "late"),
            "Attendance Rate": f"{course_rate:.2f}%"
        })
    
    # Sort by course name
    course_attendance.sort(key=lambda x: x["Course"])
    
    # Show course attendance table
    show_data_table(course_attendance)
    
    # Create bar chart for course attendance
    if course_attendance:
        st.markdown("### Course Attendance Comparison")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="Course", y="Attendance Rate", data=pd.DataFrame(course_attendance), ax=ax)
        ax.set_title("Course Attendance Rates")
        ax.set_xlabel("Course")
        ax.set_ylabel("Attendance Rate (%)")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    
    # View detailed attendance for a specific course
    st.markdown("### Detailed Course Attendance")
    
    # Select course
    course_ids = list(attendance.keys())
    
    if course_ids:
        selected_course_id = st.selectbox(
            "Select Course",
            options=course_ids,
            format_func=lambda x: attendance[x].get("course_name", "Unknown")
        )
        
        if selected_course_id and selected_course_id in attendance:
            course_data = attendance[selected_course_id]
            sessions = course_data.get("sessions", [])
            
            if sessions:
                # Prepare session data
                session_data = []
                
                for session in sessions:
                    session_data.append({
                        "Date": format_date(session.get("date", "")),
                        "Status": session.get("status", "Unknown").capitalize(),
                        "Notes": session.get("notes", "")
                    })
                
                # Sort by date (newest first)
                session_data.sort(key=lambda x: x["Date"], reverse=True)
                
                # Show session table
                show_data_table(session_data)
                
                # Create timeline chart
                st.markdown("### Attendance Timeline")
                
                # Prepare timeline data
                timeline_data = []
                
                for session in sessions:
                    status_value = 1 if session.get("status") == "present" else (0.5 if session.get("status") == "late" else 0)
                    
                    timeline_data.append({
                        "Date": session.get("date", ""),
                        "Status Value": status_value,
                        "Status": session.get("status", "Unknown").capitalize()
                    })
                
                # Sort by date
                timeline_data.sort(key=lambda x: x["Date"])
                
                # Create line chart
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.lineplot(x="Date", y="Status Value", data=pd.DataFrame(timeline_data), ax=ax, marker='o')
                ax.set_title("Attendance Timeline")
                ax.set_xlabel("Date")
                ax.set_ylabel("Status (1=Present, 0.5=Late, 0=Absent)")
                ax.set_ylim(-0.1, 1.1)
                plt.xticks(rotation=45)
                st.pyplot(fig)

def show_certificates_performance(email, user):
    """Show certificates performance."""
    st.markdown("### Certificates")
    
    # Get student certificates
    certificates = get_student_certificates(email)
    
    if not certificates:
        st.info("No certificates found.")
        return
    
    # Display certificate count
    st.metric("Total Certificates", len(certificates))
    
    # Prepare data for display
    certificate_data = []
    
    for certificate in certificates:
        certificate_data.append({
            "Certificate Name": certificate.get("name", "Unknown"),
            "Issuing Organization": certificate.get("organization", "Unknown"),
            "Issue Date": format_date(certificate.get("issue_date", "")),
            "Expiry Date": format_date(certificate.get("expiry_date", "")) if certificate.get("expiry_date") else "No Expiry",
            "Credential ID": certificate.get("credential_id", "N/A"),
            "URL": certificate.get("url", "N/A")
        })
    
    # Sort by issue date (newest first)
    certificate_data.sort(key=lambda x: x["Issue Date"], reverse=True)
    
    # Show certificates table
    show_data_table(certificate_data)
    
    # Create visualizations
    if certificate_data:
        # Create bar chart for certificates by organization
        st.markdown("### Certificates by Organization")
        
        # Count certificates by organization
        org_counts = {}
        
        for cert in certificate_data:
            org = cert["Issuing Organization"]
            org_counts[org] = org_counts.get(org, 0) + 1
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=list(org_counts.keys()), y=list(org_counts.values()), ax=ax)
        ax.set_title("Certificates by Organization")
        ax.set_xlabel("Organization")
        ax.set_ylabel("Number of Certificates")
        plt.xticks(rotation=45)
        st.pyplot(fig)
        
        # Create timeline chart
        st.markdown("### Certificate Timeline")
        
        # Prepare timeline data
        timeline_data = []
        
        for cert in certificate_data:
            timeline_data.append({
                "Date": cert["Issue Date"],
                "Certificate": cert["Certificate Name"],
                "Organization": cert["Issuing Organization"]
            })
        
        # Sort by date
        timeline_data.sort(key=lambda x: x["Date"])
        
        # Create scatter plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot points
        for i, cert in enumerate(timeline_data):
            ax.scatter(cert["Date"], i, s=100, label=cert["Certificate"])
            ax.text(cert["Date"], i + 0.1, f"{cert['Certificate']} ({cert['Organization']})", fontsize=8)
        
        ax.set_title("Certificate Timeline")
        ax.set_xlabel("Date")
        ax.set_yticks([])
        ax.grid(True, axis='x')
        plt.xticks(rotation=45)
        st.pyplot(fig)

def show_performance_ai_analysis(email, user):
    """Show AI analysis of student performance."""
    st.markdown("### AI Analysis of Academic Performance")
    
    # Get all student data for comprehensive analysis
    submissions = get_student_submissions(email)
    attendance = get_student_attendance(email)
    certificates = get_student_certificates(email)
    courses = get_student_courses(email)
    exam_results = get_student_exam_results(email)
    exams = get_exams()
    subjects = get_subjects()
    
    # Calculate performance metrics
    total_submissions = len(submissions)
    graded_submissions = sum(1 for s in submissions if s.get("grade") is not None)
    completion_rate = (graded_submissions / total_submissions) * 100 if total_submissions > 0 else 0
    
    total_attendance = sum(len(a.get("sessions", [])) for a in attendance.values())
    present_sessions = sum(sum(1 for s in a.get("sessions", []) if s.get("status") == "present") for a in attendance.values())
    attendance_rate = (present_sessions / total_attendance) * 100 if total_attendance > 0 else 0
    
    # Prepare data for analysis
    analysis_data = {
        "student_info": {
            "name": user.get("name", "Unknown"),
            "email": email,
            "student_id": user.get("student_id", "N/A"),
            "department": user.get("department", "N/A"),
            "year": user.get("year", "N/A"),
            "semester": user.get("semester", "N/A"),
            "section": user.get("section", "N/A")
        },
        "academic_performance": {
            "total_submissions": total_submissions,
            "graded_submissions": graded_submissions,
            "completion_rate": completion_rate,
            "total_attendance": total_attendance,
            "present_sessions": present_sessions,
            "attendance_rate": attendance_rate,
            "total_certificates": len(certificates)
        },
        "attendance": {},
        "course_performance": {},
        "exam_performance": [],
        "certificates": []
    }
    
    # Process attendance data
    for course_id, course_data in attendance.items():
        course_sessions = len(course_data.get("sessions", []))
        course_present = sum(1 for s in course_data.get("sessions", []) if s.get("status") == "present")
        course_absent = sum(1 for s in course_data.get("sessions", []) if s.get("status") == "absent")
        course_late = sum(1 for s in course_data.get("sessions", []) if s.get("status") == "late")
        course_rate = (course_present / course_sessions) * 100 if course_sessions > 0 else 0
        
        analysis_data["attendance"][course_data.get("course_name", "Unknown")] = {
            "total_sessions": course_sessions,
            "present": course_present,
            "absent": course_absent,
            "late": course_late,
            "attendance_rate": course_rate
        }
    
    # Process course performance data
    for course in courses:
        course_name = course.get("course_name", "Unknown")
        course_submissions = [s for s in submissions if s.get("course_id") == course.get("course_id")]
        
        if course_submissions:
            total_course_submissions = len(course_submissions)
            graded_course_submissions = sum(1 for s in course_submissions if s.get("grade") is not None)
            course_grades = [s.get("grade", 0) for s in course_submissions if s.get("grade") is not None]
            avg_grade = sum(course_grades) / len(course_grades) if course_grades else 0
            
            analysis_data["course_performance"][course_name] = {
                "total_submissions": total_course_submissions,
                "graded_submissions": graded_course_submissions,
                "average_grade": avg_grade,
                "highest_grade": max(course_grades) if course_grades else 0,
                "lowest_grade": min(course_grades) if course_grades else 0
            }
    
    # Process exam results
    for exam_id, subject_results in exam_results.items():
        if exam_id in exams:
            exam = exams[exam_id]
            
            # Calculate overall percentage for this exam
            total_marks = 0
            max_total = 0
            
            subject_results_list = []
            
            for subject_id, result in subject_results.items():
                if subject_id in subjects:
                    subject = subjects[subject_id]
                    marks = result.get("marks", 0)
                    max_marks = exam.get("max_marks", 100)
                    
                    total_marks += marks
                    max_total += max_marks
                    
                    # Calculate percentage
                    subject_percentage = (marks / max_marks) * 100 if max_marks > 0 else 0
                    
                    subject_results_list.append({
                        "subject_name": subject.get("subject_name", "Unknown"),
                        "marks": marks,
                        "max_marks": max_marks,
                        "percentage": subject_percentage
                    })
            
            percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
            
            analysis_data["exam_performance"].append({
                "exam_name": exam.get("exam_name", "Unknown"),
                "exam_type": exam.get("exam_type", "Unknown"),
                "exam_date": exam.get("exam_date", ""),
                "total_marks": total_marks,
                "total_max_marks": max_total,
                "percentage": percentage,
                "subject_results": subject_results_list
            })
    
    # Process certificates
    for certificate in certificates:
        analysis_data["certificates"].append({
            "name": certificate.get("name", "Unknown"),
            "organization": certificate.get("organization", "Unknown"),
            "issue_date": certificate.get("issue_date", ""),
            "expiry_date": certificate.get("expiry_date", ""),
            "credential_id": certificate.get("credential_id", "N/A"),
            "url": certificate.get("url", "N/A")
        })
    
    # Display a summary of the data being analyzed
    st.markdown("### Data Being Analyzed")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Courses", len(courses))
    
    with col2:
        st.metric("Submissions", total_submissions)
    
    with col3:
        st.metric("Exams", len(analysis_data["exam_performance"]))
    
    with col4:
        st.metric("Certificates", len(certificates))
    
    # Add option to use test mode with sample data
    use_test_mode = st.checkbox("Use test mode (for debugging)", value=False, key="profile_test_mode")
    
    # Create AI analysis button
    if st.button("Generate Comprehensive AI Analysis", key="analyze_profile_button"):
        with st.spinner("Analyzing your academic profile... This may take a moment."):
            if use_test_mode:
                # Use sample data for testing
                analysis_result = """
                # Comprehensive Academic Profile Analysis

                ## Overall Academic Profile Assessment

                Based on the comprehensive analysis of your academic data, you demonstrate a **strong academic profile** with consistent performance across multiple areas. Your overall completion rate of 85% for assignments and attendance rate of 92% indicate excellent academic discipline and commitment to your studies.

                ## Strengths

                1. **Excellent Attendance**: Your attendance record is exemplary, particularly in core subjects where you maintain a 95%+ attendance rate.
                2. **Consistent Assignment Completion**: You consistently complete and submit assignments on time, with a high grading rate.
                3. **Strong Performance in Technical Subjects**: Your exam results show particular strength in mathematics, programming, and data analysis courses.
                4. **Certification Initiative**: You have obtained relevant industry certifications that complement your academic coursework.

                ## Areas for Improvement

                1. **Performance Variability in Theoretical Courses**: Your grades in theoretical subjects show more variability than in practical/technical courses.
                2. **Participation in Group Projects**: While individual assignment completion is strong, there's room for more active participation in collaborative projects.
                3. **Time Management in Exam Preparation**: Exam results suggest potential for improved performance with better exam preparation strategies.

                ## Correlation Between Attendance and Academic Performance

                There is a strong positive correlation (r=0.78) between your attendance and academic performance. Courses where your attendance exceeds 90% show an average grade improvement of 12% compared to courses with lower attendance. This clearly demonstrates that your consistent presence in class translates directly to better academic outcomes.

                ## Course-Specific Insights

                ### Computer Science Fundamentals
                - **Strength**: Exceptional performance in programming assignments (94% average)
                - **Opportunity**: Deepen theoretical understanding of algorithms and complexity analysis

                ### Data Structures and Algorithms
                - **Strength**: Strong problem-solving skills demonstrated in practical assessments
                - **Opportunity**: More consistent performance across different algorithm categories

                ### Database Management
                - **Strength**: Excellent SQL implementation skills
                - **Opportunity**: Strengthen conceptual understanding of database normalization

                ## Career Readiness Assessment

                Your current profile indicates **strong career readiness** with particular alignment to roles in software development, data analysis, and IT project management. Your combination of technical skills, consistent academic performance, and relevant certifications positions you well for entry-level professional roles.

                ## Personalized Academic Improvement Plan

                1. **Short-term Goals (Next Semester)**
                   - Implement spaced repetition study techniques for theoretical subjects
                   - Participate in at least two collaborative projects
                   - Maintain 95%+ attendance across all courses

                2. **Medium-term Goals (Next Year)**
                   - Develop a portfolio of applied projects in your area of specialization
                   - Obtain at least two additional industry certifications
                   - Improve exam preparation strategies with practice tests and study groups

                3. **Long-term Goals (Graduation)**
                   - Maintain a cumulative GPA of 3.5+
                   - Complete an industry internship
                   - Develop specialized expertise in your chosen field

                ## Recommended Extracurricular Activities and Skill Development

                1. **Technical Skill Development**
                   - Join a coding club or participate in hackathons
                   - Contribute to open-source projects related to your field
                   - Develop a personal project that showcases your technical abilities

                2. **Soft Skill Enhancement**
                   - Join Toastmasters or similar public speaking groups
                   - Participate in student leadership opportunities
                   - Engage in team-based extracurricular activities

                3. **Professional Development**
                   - Attend industry conferences and networking events
                   - Connect with alumni in your field of interest
                   - Participate in mock interviews and resume workshops

                ## Potential Career Paths

                Based on your current performance and interests, the following career paths show strong alignment:

                1. **Software Development**
                   - Your strong programming skills and consistent performance in technical courses align well with this path
                   - Recommended focus: Full-stack development, mobile app development

                2. **Data Analysis/Data Science**
                   - Your analytical abilities and performance in mathematics and statistics courses support this direction
                   - Recommended focus: Machine learning, data visualization

                3. **IT Project Management**
                   - Your consistent completion rates and balanced performance across technical and theoretical subjects indicate potential here
                   - Recommended focus: Agile methodologies, team leadership

                Your academic trajectory shows excellent potential for continued growth. By addressing the identified areas for improvement and building on your existing strengths, you are well-positioned for academic success and a strong transition to your professional career.
                """
                st.success("Analysis completed in test mode!")
            else:
                # Perform actual analysis
                analysis_result = analyze_with_gemini(analysis_data, "profile")
            
            # Display the analysis
            st.markdown("## AI Analysis Results")
            st.markdown(analysis_result)
            
            # Add download option for the analysis
            st.markdown("### Save Your Analysis")
            st.download_button(
                label="Download Analysis Report",
                data=analysis_result,
                file_name=f"academic_profile_analysis_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            ) 