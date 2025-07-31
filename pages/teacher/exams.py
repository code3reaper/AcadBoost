import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

from utils.auth import role_required, get_users
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_exams, get_exam, add_exam, update_exam, delete_exam,
    get_subjects, get_subject, add_subject, update_subject, delete_subject,
    get_exam_results, get_exam_results_by_exam, add_exam_result, delete_exam_result
)

@role_required(["teacher"])
def show_teacher_exams():
    """Show the exams page for teachers."""
    show_header("Exams Management", "Create and manage exams, subjects, and student marks")
    
    # Create tabs for different exam management functions
    tab1, tab2, tab3 = st.tabs(["Subjects", "Exams", "Student Marks"])
    
    with tab1:
        show_subjects_management()
    
    with tab2:
        show_exams_management()
    
    with tab3:
        show_student_marks_management()

def show_subjects_management():
    """Show the subjects management section."""
    st.markdown("### Subjects Management")
    
    # Get all subjects
    subjects = get_subjects()
    
    # Display existing subjects
    if subjects:
        # Prepare subjects data
        subjects_data = []
        
        for subject_id, subject in subjects.items():
            subjects_data.append({
                "Subject ID": subject_id,
                "Subject Name": subject.get("subject_name", "No Name"),
                "Semester": subject.get("semester", "N/A"),
                "Department": subject.get("department", "N/A")
            })
        
        # Sort by semester and name
        subjects_data.sort(key=lambda x: (x["Semester"], x["Subject Name"]))
        
        # Show subjects table
        st.markdown("#### Existing Subjects")
        show_data_table(subjects_data)
    else:
        st.info("No subjects found. Add a new subject below.")
    
    # Add new subject
    st.markdown("#### Add New Subject")
    
    with st.form("add_subject_form"):
        subject_name = st.text_input("Subject Name", key="new_subject_name")
        semester = st.selectbox("Semester", options=list(range(1, 9)), key="new_subject_semester")
        department = st.text_input("Department (Optional)", key="new_subject_department")
        
        submit_button = st.form_submit_button("Add Subject")
        
        if submit_button:
            if not subject_name:
                st.error("Subject name is required.")
            else:
                subject_id = add_subject(subject_name, semester, department)
                st.success(f"Subject '{subject_name}' added successfully!")
                st.rerun()
    
    # Edit or delete subject
    if subjects:
        st.markdown("#### Edit or Delete Subject")
        
        selected_subject_id = st.selectbox(
            "Select Subject",
            options=[s["Subject ID"] for s in subjects_data],
            format_func=lambda x: next((s["Subject Name"] for s in subjects_data if s["Subject ID"] == x), "Unknown"),
            key="edit_subject_id"
        )
        
        if selected_subject_id:
            selected_subject = get_subject(selected_subject_id)
            
            if selected_subject:
                with st.form("edit_subject_form"):
                    edit_subject_name = st.text_input("Subject Name", value=selected_subject.get("subject_name", ""))
                    edit_semester = st.selectbox("Semester", options=list(range(1, 9)), index=int(selected_subject.get("semester", 1)) - 1)
                    edit_department = st.text_input("Department", value=selected_subject.get("department", ""))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        update_button = st.form_submit_button("Update Subject")
                    
                    with col2:
                        delete_button = st.form_submit_button("Delete Subject", type="primary")
                    
                    if update_button:
                        if not edit_subject_name:
                            st.error("Subject name is required.")
                        else:
                            update_subject(selected_subject_id, edit_subject_name, edit_semester, edit_department)
                            st.success(f"Subject '{edit_subject_name}' updated successfully!")
                            st.rerun()
                    
                    if delete_button:
                        delete_subject(selected_subject_id)
                        st.success(f"Subject deleted successfully!")
                        st.rerun()

def show_exams_management():
    """Show the exams management section."""
    st.markdown("### Exams Management")
    
    # Get all exams
    exams = get_exams()
    
    # Display existing exams
    if exams:
        # Prepare exams data
        exams_data = []
        
        for exam_id, exam in exams.items():
            exams_data.append({
                "Exam ID": exam_id,
                "Exam Name": exam.get("exam_name", "No Name"),
                "Exam Type": exam.get("exam_type", "N/A"),
                "Semester": exam.get("semester", "N/A"),
                "Date": format_date(exam.get("date", "")),
                "Max Marks": exam.get("max_marks", 100)
            })
        
        # Sort by date (newest first)
        exams_data.sort(key=lambda x: x["Date"], reverse=True)
        
        # Show exams table
        st.markdown("#### Existing Exams")
        show_data_table(exams_data)
    else:
        st.info("No exams found. Add a new exam below.")
    
    # Add new exam
    st.markdown("#### Add New Exam")
    
    with st.form("add_exam_form"):
        exam_name = st.text_input("Exam Name", key="new_exam_name")
        exam_type = st.selectbox("Exam Type", options=["Mid Sem 1", "Mid Sem 2", "End Sem"], key="new_exam_type")
        semester = st.selectbox("Semester", options=list(range(1, 9)), key="new_exam_semester")
        date = st.date_input("Exam Date", key="new_exam_date")
        max_marks = st.number_input("Maximum Marks", min_value=1, value=100, key="new_exam_max_marks")
        
        submit_button = st.form_submit_button("Add Exam")
        
        if submit_button:
            if not exam_name:
                st.error("Exam name is required.")
            else:
                exam_id = add_exam(exam_name, exam_type, semester, date.strftime("%Y-%m-%d"), max_marks)
                st.success(f"Exam '{exam_name}' added successfully!")
                st.rerun()
    
    # Edit or delete exam
    if exams:
        st.markdown("#### Edit or Delete Exam")
        
        selected_exam_id = st.selectbox(
            "Select Exam",
            options=[e["Exam ID"] for e in exams_data],
            format_func=lambda x: next((e["Exam Name"] for e in exams_data if e["Exam ID"] == x), "Unknown"),
            key="edit_exam_id"
        )
        
        if selected_exam_id:
            selected_exam = get_exam(selected_exam_id)
            
            if selected_exam:
                with st.form("edit_exam_form"):
                    edit_exam_name = st.text_input("Exam Name", value=selected_exam.get("exam_name", ""))
                    
                    exam_types = ["Mid Sem 1", "Mid Sem 2", "End Sem"]
                    edit_exam_type = st.selectbox(
                        "Exam Type", 
                        options=exam_types,
                        index=exam_types.index(selected_exam.get("exam_type", "Mid Sem 1")) if selected_exam.get("exam_type", "") in exam_types else 0
                    )
                    
                    edit_semester = st.selectbox("Semester", options=list(range(1, 9)), index=int(selected_exam.get("semester", 1)) - 1)
                    
                    try:
                        default_date = datetime.strptime(selected_exam.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
                    except:
                        default_date = datetime.now().date()
                    
                    edit_date = st.date_input("Exam Date", value=default_date)
                    edit_max_marks = st.number_input("Maximum Marks", min_value=1, value=int(selected_exam.get("max_marks", 100)))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        update_button = st.form_submit_button("Update Exam")
                    
                    with col2:
                        delete_button = st.form_submit_button("Delete Exam", type="primary")
                    
                    if update_button:
                        if not edit_exam_name:
                            st.error("Exam name is required.")
                        else:
                            update_exam(
                                selected_exam_id, 
                                edit_exam_name, 
                                edit_exam_type, 
                                edit_semester, 
                                edit_date.strftime("%Y-%m-%d"), 
                                edit_max_marks
                            )
                            st.success(f"Exam '{edit_exam_name}' updated successfully!")
                            st.rerun()
                    
                    if delete_button:
                        delete_exam(selected_exam_id)
                        st.success(f"Exam deleted successfully!")
                        st.rerun()

def show_student_marks_management():
    """Show the student marks management section."""
    st.markdown("### Student Marks Management")
    
    # Get all exams
    exams = get_exams()
    
    if not exams:
        st.info("No exams found. Please add an exam first.")
        return
    
    # Get all subjects
    subjects = get_subjects()
    
    if not subjects:
        st.info("No subjects found. Please add a subject first.")
        return
    
    # Get all users
    users = get_users()
    
    # Filter students
    students = {email: user for email, user in users.items() if user.get("role") == "student"}
    
    if not students:
        st.info("No students found in the system.")
        return
    
    # Select exam
    exam_data = []
    for exam_id, exam in exams.items():
        exam_data.append({
            "Exam ID": exam_id,
            "Exam Name": exam.get("exam_name", "No Name"),
            "Exam Type": exam.get("exam_type", "N/A"),
            "Semester": exam.get("semester", "N/A"),
            "Date": format_date(exam.get("date", ""))
        })
    
    # Sort by date (newest first)
    exam_data.sort(key=lambda x: x["Date"], reverse=True)
    
    selected_exam_id = st.selectbox(
        "Select Exam",
        options=[e["Exam ID"] for e in exam_data],
        format_func=lambda x: f"{next((e['Exam Name'] for e in exam_data if e['Exam ID'] == x), 'Unknown')} ({next((e['Exam Type'] for e in exam_data if e['Exam ID'] == x), 'Unknown')})",
        key="marks_exam_id"
    )
    
    if selected_exam_id:
        selected_exam = get_exam(selected_exam_id)
        
        if selected_exam:
            st.markdown(f"#### {selected_exam.get('exam_name', 'Exam')} ({selected_exam.get('exam_type', 'Exam')})")
            st.markdown(f"**Semester:** {selected_exam.get('semester', 'N/A')}")
            st.markdown(f"**Date:** {format_date(selected_exam.get('date', ''))}")
            st.markdown(f"**Maximum Marks:** {selected_exam.get('max_marks', 100)}")
            
            # Filter subjects by semester
            semester_subjects = {
                subject_id: subject for subject_id, subject in subjects.items() 
                if str(subject.get("semester", "")) == str(selected_exam.get("semester", ""))
            }
            
            if not semester_subjects:
                st.warning(f"No subjects found for semester {selected_exam.get('semester', 'N/A')}. Please add subjects for this semester.")
                return
            
            # Filter students by semester
            semester_students = {
                email: student for email, student in students.items() 
                if str(student.get("semester", "")) == str(selected_exam.get("semester", ""))
            }
            
            if not semester_students:
                st.warning(f"No students found for semester {selected_exam.get('semester', 'N/A')}.")
                return
            
            # Get exam results
            exam_results = get_exam_results_by_exam(selected_exam_id)
            
            # Create tabs for different mark management functions
            tab1, tab2 = st.tabs(["Enter Marks", "View Results"])
            
            with tab1:
                show_enter_marks(selected_exam_id, selected_exam, semester_subjects, semester_students, exam_results)
            
            with tab2:
                show_view_results(selected_exam_id, selected_exam, semester_subjects, semester_students, exam_results)

def show_enter_marks(exam_id, exam, subjects, students, exam_results):
    """Show the enter marks section."""
    st.markdown("### Enter Student Marks")
    
    # Select subject
    subject_data = []
    for subject_id, subject in subjects.items():
        subject_data.append({
            "Subject ID": subject_id,
            "Subject Name": subject.get("subject_name", "No Name")
        })
    
    # Sort by name
    subject_data.sort(key=lambda x: x["Subject Name"])
    
    selected_subject_id = st.selectbox(
        "Select Subject",
        options=[s["Subject ID"] for s in subject_data],
        format_func=lambda x: next((s["Subject Name"] for s in subject_data if s["Subject ID"] == x), "Unknown"),
        key="marks_subject_id"
    )
    
    if selected_subject_id:
        selected_subject = subjects.get(selected_subject_id)
        
        if selected_subject:
            st.markdown(f"#### {selected_subject.get('subject_name', 'Subject')}")
            
            # Prepare student data
            student_data = []
            
            for email, student in students.items():
                # Get existing mark
                existing_mark = None
                existing_remarks = None
                
                if email in exam_results and selected_subject_id in exam_results[email]:
                    existing_mark = exam_results[email][selected_subject_id].get("marks")
                    existing_remarks = exam_results[email][selected_subject_id].get("remarks")
                
                student_data.append({
                    "Email": email,
                    "Name": student.get("name", "Unknown"),
                    "Student ID": student.get("student_id", "N/A"),
                    "Section": student.get("section", "N/A"),
                    "Existing Mark": existing_mark,
                    "Existing Remarks": existing_remarks
                })
            
            # Sort by name
            student_data.sort(key=lambda x: x["Name"])
            
            # Show form for entering marks
            with st.form("enter_marks_form"):
                st.markdown("Enter marks for each student:")
                
                # Create input fields for each student
                student_marks = {}
                student_remarks = {}
                
                for student in student_data:
                    col1, col2, col3 = st.columns([3, 1, 2])
                    
                    with col1:
                        st.markdown(f"**{student['Name']}** ({student['Student ID']})")
                    
                    with col2:
                        student_marks[student["Email"]] = st.number_input(
                            f"Mark for {student['Name']}",
                            min_value=0,
                            max_value=int(exam.get("max_marks", 100)),
                            value=int(student["Existing Mark"]) if student["Existing Mark"] is not None else 0,
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        student_remarks[student["Email"]] = st.text_input(
                            f"Remarks for {student['Name']}",
                            value=student["Existing Remarks"] if student["Existing Remarks"] else "",
                            placeholder="Optional remarks",
                            label_visibility="collapsed"
                        )
                
                submit_button = st.form_submit_button("Save Marks")
                
                if submit_button:
                    # Save marks for each student
                    for email, mark in student_marks.items():
                        add_exam_result(
                            exam_id,
                            email,
                            selected_subject_id,
                            mark,
                            student_remarks[email]
                        )
                    
                    st.success("Marks saved successfully!")
                    st.rerun()

def show_view_results(exam_id, exam, subjects, students, exam_results):
    """Show the view results section."""
    st.markdown("### View Exam Results")
    
    if not exam_results:
        st.info("No results found for this exam.")
        return
    
    # Prepare results data
    results_data = []
    
    for email, student_results in exam_results.items():
        if email in students:
            student = students[email]
            
            # Calculate total and percentage
            total_marks = 0
            max_total = 0
            
            for subject_id, result in student_results.items():
                if subject_id in subjects:
                    total_marks += result.get("marks", 0)
                    max_total += exam.get("max_marks", 100)
            
            percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
            
            # Add to results data
            results_data.append({
                "Email": email,
                "Name": student.get("name", "Unknown"),
                "Student ID": student.get("student_id", "N/A"),
                "Section": student.get("section", "N/A"),
                "Total Marks": total_marks,
                "Maximum Marks": max_total,
                "Percentage": percentage
            })
    
    # Sort by percentage (highest first)
    results_data.sort(key=lambda x: x["Percentage"], reverse=True)
    
    # Show results table
    show_data_table(results_data)
    
    # Create visualizations
    if results_data:
        # Create histogram for grade distribution
        fig = px.histogram(
            results_data,
            x="Percentage",
            nbins=10,
            title="Grade Distribution",
            labels={"Percentage": "Percentage (%)", "count": "Number of Students"},
            color_discrete_sequence=["#4F8BF9"]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show top performers
        st.markdown("#### Top Performers")
        
        top_students = pd.DataFrame(results_data).nlargest(5, "Percentage")
        
        fig = px.bar(
            top_students,
            x="Name",
            y="Percentage",
            title="Top 5 Students by Percentage",
            color="Percentage",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show section-wise performance if sections exist
        sections = set(s["Section"] for s in results_data if s["Section"] != "N/A")
        
        if sections:
            st.markdown("#### Section-wise Performance")
            
            # Calculate section statistics
            section_stats = []
            
            for section in sections:
                section_students = [s for s in results_data if s["Section"] == section]
                
                if section_students:
                    avg_percentage = sum(s["Percentage"] for s in section_students) / len(section_students)
                    
                    section_stats.append({
                        "Section": section,
                        "Students": len(section_students),
                        "Average Percentage": avg_percentage
                    })
            
            # Sort by average percentage
            section_stats.sort(key=lambda x: x["Average Percentage"], reverse=True)
            
            # Show table
            show_data_table(section_stats)
            
            # Create bar chart
            fig = px.bar(
                section_stats,
                x="Section",
                y="Average Percentage",
                title="Section-wise Performance",
                labels={
                    "Section": "Section",
                    "Average Percentage": "Average Percentage (%)"
                },
                color="Average Percentage",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # View detailed results for a specific student
    st.markdown("#### Detailed Student Results")
    
    selected_student_email = st.selectbox(
        "Select Student",
        options=[s["Email"] for s in results_data],
        format_func=lambda x: f"{next((s['Name'] for s in results_data if s['Email'] == x), 'Unknown')} ({x})",
        key="detailed_results_student"
    )
    
    if selected_student_email and selected_student_email in exam_results:
        student = students[selected_student_email]
        student_results = exam_results[selected_student_email]
        
        st.markdown(f"**Student:** {student.get('name', 'Unknown')}")
        st.markdown(f"**Student ID:** {student.get('student_id', 'N/A')}")
        st.markdown(f"**Section:** {student.get('section', 'N/A')}")
        
        # Prepare detailed results
        detailed_results = []
        
        for subject_id, result in student_results.items():
            if subject_id in subjects:
                subject = subjects[subject_id]
                
                detailed_results.append({
                    "Subject": subject.get("subject_name", "Unknown"),
                    "Marks": result.get("marks", 0),
                    "Maximum Marks": exam.get("max_marks", 100),
                    "Percentage": (result.get("marks", 0) / exam.get("max_marks", 100)) * 100,
                    "Remarks": result.get("remarks", "")
                })
        
        # Sort by subject name
        detailed_results.sort(key=lambda x: x["Subject"])
        
        # Show detailed results
        show_data_table(detailed_results)
        
        # Create bar chart for subject-wise performance
        fig = px.bar(
            detailed_results,
            x="Subject",
            y="Percentage",
            title="Subject-wise Performance",
            labels={
                "Subject": "Subject",
                "Percentage": "Percentage (%)"
            },
            color="Percentage",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        st.plotly_chart(fig, use_container_width=True) 
