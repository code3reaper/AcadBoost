import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_exams, get_student_exam_results, get_subjects,
    get_exam_results_by_exam
)
from utils.ai_analysis import analyze_with_gemini

@role_required(["student"])
def show_student_exams():
    """Show the exams page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Exams", "View and analyze your exam performance")
    
    # Get student's exam results
    exams = get_exams()
    subjects = get_subjects()
    student_results = get_student_exam_results(email)
    
    # Create tabs for different exam views
    tab1, tab2, tab3 = st.tabs(["Exam Results", "Subject Performance", "AI Analysis"])
    
    with tab1:
        show_exam_results(email, user, student_results, exams, subjects)
    
    with tab2:
        show_subject_wise_performance(email, user, student_results, exams, subjects)
    
    with tab3:
        show_exam_ai_analysis(email, user, student_results, exams, subjects)

def show_exam_results(email, user, student_results, exams, subjects):
    """Show exam results for the student."""
    st.markdown("### My Exam Results")
    
    if not student_results:
        st.info("No exam results found.")
        return
    
    # Prepare data for display
    exam_data = []
    
    for exam_id, subject_results in student_results.items():
        if exam_id in exams:
            exam = exams[exam_id]
            
            # Calculate total and percentage
            total_marks = 0
            max_total = 0
            subject_count = 0
            
            for subject_id, result in subject_results.items():
                if subject_id in subjects:
                    total_marks += result.get("marks", 0)
                    max_total += exam.get("max_marks", 100)
                    subject_count += 1
            
            percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
            
            exam_data.append({
                "Exam ID": exam_id,
                "Exam Name": exam.get("exam_name", "Unknown"),
                "Exam Type": exam.get("exam_type", "Unknown"),
                "Date": format_date(exam.get("exam_date", "")),
                "Marks": f"{total_marks}/{max_total}",
                "Percentage": f"{percentage:.2f}%"
            })
    
    # Show exam results table
    if exam_data:
        show_data_table(exam_data)
        
        # Create bar chart for exam performance
        fig = plt.figure(figsize=(10, 6))
        ax = sns.barplot(x="Exam Name", y="Percentage", data=pd.DataFrame(exam_data), ax=fig.gca())
        ax.set_title("Exam Performance")
        ax.set_xlabel("Exam")
        ax.set_ylabel("Percentage (%)")
        st.pyplot(fig)
    else:
        st.info("No exam results found.")
    
    # View detailed results for a specific exam
    st.markdown("### Detailed Exam Results")
    
    # Select exam
    exam_ids = list(student_results.keys())
    
    if exam_ids:
        selected_exam_id = st.selectbox(
            "Select Exam",
            options=exam_ids,
            format_func=lambda x: exams[x].get("exam_name", "Unknown") if x in exams else "Unknown"
        )
        
        if selected_exam_id and selected_exam_id in student_results:
            selected_exam = exams[selected_exam_id]
            subject_results = student_results[selected_exam_id]
            
            st.markdown(f"**Exam:** {selected_exam.get('exam_name', 'Unknown')}")
            st.markdown(f"**Type:** {selected_exam.get('exam_type', 'Unknown')}")
            st.markdown(f"**Date:** {format_date(selected_exam.get('exam_date', ''))}")
            
            # Get detailed results for this exam
            detailed_results = []
            
            for subject_id, result in subject_results.items():
                if subject_id in subjects:
                    subject = subjects[subject_id]
                    
                    # Calculate percentage
                    marks = result.get("marks", 0)
                    max_marks = selected_exam.get("max_marks", 100)
                    percentage = (marks / max_marks) * 100 if max_marks > 0 else 0
                    
                    detailed_results.append({
                        "Subject": subject.get("subject_name", "Unknown"),
                        "Marks": f"{marks}/{max_marks}",
                        "Percentage": percentage
                    })
            
            if detailed_results:
                # Show detailed results table
                show_data_table(detailed_results)
                
                # Create bar chart for subject-wise performance
                fig = plt.figure(figsize=(10, 6))
                ax = sns.barplot(x="Subject", y="Percentage", data=pd.DataFrame(detailed_results), ax=fig.gca())
                ax.set_title("Subject-wise Performance")
                ax.set_xlabel("Subject")
                ax.set_ylabel("Percentage (%)")
                st.pyplot(fig)
                
                # Show class performance if available
                exam_results = get_exam_results_by_exam(selected_exam_id)
                
                if len(exam_results) > 1:  # More than just this student
                    st.markdown("### Class Performance")
                    
                    # Calculate class statistics
                    class_stats = {
                        "Highest": 0,
                        "Lowest": 100,
                        "Average": 0,
                        "Total Students": 0
                    }
                    
                    student_percentages = []
                    
                    for student_email, student_subjects in exam_results.items():
                        # Calculate student's percentage
                        student_total = 0
                        student_max = 0
                        
                        for subject_id, result in student_subjects.items():
                            if subject_id in subjects:
                                student_total += result.get("marks", 0)
                                student_max += selected_exam.get("max_marks", 100)
                        
                        if student_max > 0:
                            student_percentage = (student_total / student_max) * 100
                            student_percentages.append(student_percentage)
                            
                            # Update class statistics
                            class_stats["Highest"] = max(class_stats["Highest"], student_percentage)
                            class_stats["Lowest"] = min(class_stats["Lowest"], student_percentage)
                            class_stats["Total Students"] += 1
                    
                    if student_percentages:
                        class_stats["Average"] = sum(student_percentages) / len(student_percentages)
                    
                    # Show class statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Your Percentage", f"{percentage:.2f}%")
                    
                    with col2:
                        st.metric("Class Average", f"{class_stats['Average']:.2f}%")
                    
                    with col3:
                        st.metric("Highest", f"{class_stats['Highest']:.2f}%")
                    
                    with col4:
                        st.metric("Lowest", f"{class_stats['Lowest']:.2f}%")
                    
                    # Create histogram for class distribution
                    fig = plt.figure(figsize=(10, 6))
                    ax = sns.histplot(student_percentages, ax=fig.gca())
                    ax.set_title("Class Grade Distribution")
                    ax.set_xlabel("Percentage (%)")
                    ax.set_ylabel("Number of Students")
                    st.pyplot(fig)

def show_subject_wise_performance(email, user, student_results, exams, subjects):
    """Show subject-wise performance for the student."""
    st.markdown("### Subject-wise Performance")
    
    if not student_results:
        st.info("No exam results found.")
        return
    
    # Prepare data for subject-wise analysis
    subject_performance = {}
    
    for exam_id, subject_results in student_results.items():
        if exam_id in exams:
            exam = exams[exam_id]
            
            for subject_id, result in subject_results.items():
                if subject_id in subjects:
                    subject = subjects[subject_id]
                    
                    if subject_id not in subject_performance:
                        subject_performance[subject_id] = {
                            "Subject ID": subject_id,
                            "Subject Name": subject.get("subject_name", "Unknown"),
                            "Exams": [],
                            "Total Marks": 0,
                            "Maximum Marks": 0
                        }
                    
                    # Calculate percentage
                    marks = result.get("marks", 0)
                    max_marks = exam.get("max_marks", 100)
                    percentage = (marks / max_marks) * 100 if max_marks > 0 else 0
                    
                    # Add exam result
                    subject_performance[subject_id]["Exams"].append({
                        "exam_name": exam.get("exam_name", "Unknown"),
                        "marks": marks,
                        "max_marks": max_marks,
                        "percentage": percentage
                    })
                    
                    # Update totals
                    subject_performance[subject_id]["Total Marks"] += marks
                    subject_performance[subject_id]["Maximum Marks"] += max_marks
    
    # Prepare data for display
    subject_data = []
    
    for subject_id, data in subject_performance.items():
        # Calculate overall percentage
        percentage = (data["Total Marks"] / data["Maximum Marks"]) * 100 if data["Maximum Marks"] > 0 else 0
        
        subject_data.append({
            "Subject Name": data["Subject Name"],
            "Total Marks": f"{data['Total Marks']}/{data['Maximum Marks']}",
            "Percentage": percentage,
            "Exams": len(data["Exams"])
        })
    
    # Show subject performance table
    if subject_data:
        show_data_table(subject_data)
        
        # Create bar chart for subject performance
        fig = plt.figure(figsize=(10, 6))
        ax = sns.barplot(x="Subject Name", y="Percentage", data=pd.DataFrame(subject_data), ax=fig.gca())
        ax.set_title("Subject Performance")
        ax.set_xlabel("Subject")
        ax.set_ylabel("Percentage (%)")
        st.pyplot(fig)
    else:
        st.info("No subject performance data available.")
    
    # View detailed results for a specific subject
    st.markdown("### Detailed Subject Results")
    
    # Select subject
    subject_ids = list(subject_performance.keys())
    
    if subject_ids:
        selected_subject_id = st.selectbox(
            "Select Subject",
            options=subject_ids,
            format_func=lambda x: subject_performance[x]["Subject Name"] if x in subject_performance else "Unknown"
        )
        
        if selected_subject_id and selected_subject_id in subject_performance:
            # Get exam results for this subject
            exam_results = subject_performance[selected_subject_id]["Exams"]
            
            if exam_results:
                # Show exam results table
                show_data_table(exam_results)
                
                # Create line chart for exam performance
                fig = plt.figure(figsize=(10, 6))
                ax = sns.lineplot(x="exam_name", y="percentage", data=pd.DataFrame(exam_results), ax=fig.gca())
                ax.set_title("Exam Performance Trend")
                ax.set_xlabel("Exam")
                ax.set_ylabel("Percentage (%)")
                st.pyplot(fig)

def show_exam_ai_analysis(email, user, student_results, exams, subjects):
    """Show AI analysis of exam results."""
    st.markdown("### AI Analysis of Exam Results")
    
    if not student_results:
        st.info("No exam results found for analysis.")
        return
    
    # Initialize exam_results_data
    exam_results_data = []
    
    # Prepare data for analysis
    analysis_data = {
        "student_info": {
            "name": user.get("name", "Unknown"),
            "email": email,
            "student_id": user.get("student_id", "N/A"),
            "department": user.get("department", "N/A"),
            "semester": user.get("semester", "N/A"),
            "section": user.get("section", "N/A")
        },
        "exam_results": [],
        "subject_performance": [],
        "overall_performance": {
            "total_exams": 0,
            "average_percentage": 0,
            "highest_percentage": 0,
            "lowest_percentage": 0
        }
    }
    
    # Process exam results
    all_percentages = []
    subject_performance = {}
    
    for exam_id, subject_results in student_results.items():
        if exam_id in exams:
            exam = exams[exam_id]
            
            # Calculate total and percentage for this exam
            total_marks = 0
            max_total = 0
            subject_count = 0
            
            exam_subjects = []
            
            for subject_id, result in subject_results.items():
                if subject_id in subjects:
                    subject = subjects[subject_id]
                    marks = result.get("marks", 0)
                    max_marks = exam.get("max_marks", 100)
                    
                    total_marks += marks
                    max_total += max_marks
                    subject_count += 1
                    
                    # Add subject result
                    exam_subjects.append({
                        "subject_name": subject.get("subject_name", "Unknown"),
                        "marks": marks,
                        "max_marks": max_marks,
                        "percentage": (marks / max_marks) * 100 if max_marks > 0 else 0,
                        "remarks": result.get("remarks", "")
                    })
            
            percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
            all_percentages.append(percentage)
            
            # Add exam data
            analysis_data["exam_results"].append({
                "exam_name": exam.get("exam_name", "Unknown"),
                "exam_type": exam.get("exam_type", "Unknown"),
                "exam_date": exam.get("exam_date", ""),
                "total_marks": total_marks,
                "total_max_marks": max_total,
                "percentage": percentage,
                "subject_marks": exam_subjects
            })
            
            # Process subject-wise performance
            for subject_id, result in subject_results.items():
                if subject_id in subjects:
                    subject = subjects[subject_id]
                    subject_name = subject.get("subject_name", "Unknown")
                
                    if subject_name not in subject_performance:
                        subject_performance[subject_name] = {
                            "subject_name": subject_name,
                            "exams": [],
                            "total_marks": 0,
                            "max_marks": 0
                        }
                    
                    marks = result.get("marks", 0)
                    max_marks = exam.get("max_marks", 100)
                
                    # Add exam result for this subject
                    subject_performance[subject_name]["exams"].append({
                        "exam_name": exam.get("exam_name", "Unknown"),
                        "exam_type": exam.get("exam_type", "Unknown"),
                        "marks": marks,
                        "max_marks": max_marks,
                        "percentage": (marks / max_marks) * 100 if max_marks > 0 else 0
                    })
                    
                    # Update totals
                    subject_performance[subject_name]["total_marks"] += marks
                    subject_performance[subject_name]["max_marks"] += max_marks
    
    # Calculate percentages for subjects and add to analysis data
    for subject_name, data in subject_performance.items():
        percentage = (data["total_marks"] / data["max_marks"]) * 100 if data["max_marks"] > 0 else 0
        
        analysis_data["subject_performance"].append({
            "subject_name": subject_name,
            "total_marks": data["total_marks"],
            "max_marks": data["max_marks"],
            "percentage": percentage,
            "exams": data["exams"]
        })
    
    # Calculate overall performance
    if all_percentages:
        analysis_data["overall_performance"] = {
            "total_exams": len(analysis_data["exam_results"]),
            "average_percentage": sum(all_percentages) / len(all_percentages),
            "highest_percentage": max(all_percentages),
            "lowest_percentage": min(all_percentages)
        }
    
    # Prepare data for the exam results chart
    for subject in analysis_data["subject_performance"]:
        exam_results_data.append({
            "Subject": subject["subject_name"],
            "Marks": subject["total_marks"],
            "Max Marks": subject["max_marks"],
            "Percentage": subject["percentage"]
        })
    
    # Show the exam results chart
    if exam_results_data:
        st.markdown("### Exam Results Summary")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="Subject", y="Percentage", data=pd.DataFrame(exam_results_data), ax=ax)
        plt.title("Exam Results by Subject")
        plt.xlabel("Subject")
        plt.ylabel("Percentage (%)")
        st.pyplot(fig)
    
    # Add option to use test mode with sample data
    use_test_mode = st.checkbox("Use test mode (for debugging)", value=False, key="exam_test_mode")
    
    # Create AI analysis button
    if st.button("Generate AI Analysis", key="analyze_exams_button"):
        with st.spinner("Analyzing your exam performance... This may take a moment."):
            if use_test_mode:
                # Use sample data for testing
                analysis_result = """
                # Exam Performance Analysis

                ## Overall Performance Assessment
                Your overall exam performance shows a solid average of 78.5% across all exams. This places you in the upper-middle range of academic achievement. Your performance has been relatively consistent, with your highest score being 92% and your lowest being 65%.

                ## Strengths and Weaknesses by Subject

                ### Strengths:
                - **Mathematics**: Consistently strong performance with an average of 85%. You excel particularly in calculus and algebra sections.
                - **Computer Science**: Your highest-performing subject with an average of 88%. Programming assignments show excellent problem-solving skills.
                - **Physics**: Good conceptual understanding reflected in your 79% average.

                ### Weaknesses:
                - **Chemistry**: Your lowest-performing subject with an average of 65%. Organic chemistry sections show the most room for improvement.
                - **English Literature**: While not failing, your 72% average suggests room for improvement in analytical writing.

                ## Performance Trends Over Time
                Your performance shows a positive upward trend over the semester, with a 7% improvement from your first to your most recent exams. This suggests effective adaptation to course requirements and successful implementation of study strategies.

                ## Comparison with Class Averages
                In most subjects, you are performing 5-10% above the class average. Your strongest relative performance is in Computer Science (15% above average), while Chemistry is closest to the class norm (only 2% above average).

                ## Study Strategies for Improvement

                ### For Chemistry:
                1. Increase practice with molecular structures and reactions
                2. Form a study group specifically for organic chemistry
                3. Utilize visualization tools and molecular modeling software
                4. Schedule regular review sessions with your teaching assistant

                ### For English Literature:
                1. Practice more analytical writing with peer review
                2. Develop stronger thesis statements in your essays
                3. Improve textual evidence integration in your arguments
                4. Read supplementary critical analyses of assigned texts

                ## Recommendations for Maintaining Performance

                ### For Mathematics and Computer Science:
                1. Continue your current study approach
                2. Consider taking advanced courses in these areas
                3. Explore research opportunities that combine these strengths
                4. Mentor other students to reinforce your own understanding

                ## Test-Taking Strategies
                1. Allocate time proportionally to question values
                2. Begin with your strongest subjects to build confidence
                3. For chemistry exams specifically, draw out structures before attempting to solve problems
                4. Review all answers before submission, focusing extra time on chemistry questions

                Your overall academic trajectory is positive, and with targeted improvements in your weaker subjects, you have excellent potential for achieving even higher results in future examinations.
                """
                st.success("Analysis completed in test mode!")
            else:
                # Perform actual analysis
                analysis_result = analyze_with_gemini(analysis_data, "exams")
            
            # Display the analysis
            st.markdown("## AI Analysis Results")
            st.markdown(analysis_result)
            
            # Add download option for the analysis
            st.markdown("### Save Your Analysis")
            st.download_button(
                label="Download Analysis Report",
                data=analysis_result,
                file_name=f"exam_analysis_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            ) 
