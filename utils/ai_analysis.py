import streamlit as st
import requests
import json
import os
import base64
import PyPDF2
from io import BytesIO
from datetime import datetime
import google.generativeai as genai

# Gemini API key
GEMINI_API_KEY = "AIzaSyAisOs1gZstorFU109cha8ry14H-AirnWI"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY

def analyze_with_gemini(data, analysis_type):
    """
    Analyze data using Google's Gemini API.
    
    Args:
        data (dict): The data to analyze
        analysis_type (str): Type of analysis to perform (e.g., "resume", "exams", "certificates", "profile")
    
    Returns:
        str: The analysis result
    """
    # Check if API key is set
    api_key = GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY is not set. Please set your API key to use AI analysis."
    
    # Configure the Gemini API
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        error_msg = f"Error initializing Gemini model: {str(e)}"
        st.error(error_msg)
        return error_msg
    
    # Prepare prompt based on analysis type
    if analysis_type == "resume":
        # Extract text from PDF if available
        resume_text = ""
        if "resume_file" in data and os.path.exists(data["resume_file"]):
            try:
                with open(data["resume_file"], "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        resume_text += page.extract_text()
            except Exception as e:
                resume_text = f"Error extracting text from PDF: {str(e)}"
        
        # Create prompt for resume analysis
        prompt = f"""
        You are an expert career counselor and resume analyst. Analyze the following student's resume and academic information:
        
        STUDENT INFORMATION:
        Name: {data["student_info"]["name"]}
        Email: {data["student_info"]["email"]}
        Student ID: {data["student_info"]["student_id"]}
        Department: {data["student_info"]["department"]}
        Year: {data["student_info"]["year"]}
        Semester: {data["student_info"]["semester"]}
        Section: {data["student_info"]["section"]}
        
        ACADEMIC STATISTICS:
        Total Submissions: {data["academic_stats"]["total_submissions"]}
        Graded Submissions: {data["academic_stats"]["graded_submissions"]}
        Completion Rate: {data["academic_stats"]["completion_rate"]}%
        
        RESUME CONTENT:
        {resume_text}
        
        Please provide a comprehensive analysis including:
        
        1. SWOT ANALYSIS:
           - Strengths: What are the student's strongest skills and qualifications?
           - Weaknesses: What areas could be improved in the resume?
           - Opportunities: What career paths or opportunities should the student pursue?
           - Threats: What challenges might the student face in their job search?
        
        2. ATS SCORE (out of 100):
           - Provide a numerical score for how well the resume would perform in Applicant Tracking Systems
           - Explain the factors affecting this score
           - Suggest specific improvements to increase ATS compatibility
        
        3. RESUME QUALITY ASSESSMENT:
           - Format and structure evaluation
           - Content relevance to their field of study
           - Impact of listed achievements
           - Overall professional impression
        
        4. IMPROVEMENT RECOMMENDATIONS:
           - Specific suggestions to enhance the resume
           - Skills to develop based on their academic background
           - Courses or certifications that would complement their profile
        
        5. CAREER PATH RECOMMENDATIONS:
           - Suitable career paths based on their academic performance and resume
           - Industries where they might excel
           - Types of positions to target
        
        Format your response in clear sections with headings and bullet points where appropriate.
        """
    elif analysis_type == "attendance":
        prompt = f"""
        You are an expert academic advisor. Analyze the following student's attendance patterns:
        
        STUDENT INFORMATION:
        Name: {data["student_info"]["name"]}
        Email: {data["student_info"]["email"]}
        Student ID: {data["student_info"]["student_id"]}
        Department: {data["student_info"]["department"]}
        
        ATTENDANCE STATISTICS:
        Overall Attendance Rate: {data["attendance_stats"]["overall_rate"]}%
        Present: {data["attendance_stats"]["present"]} days
        Absent: {data["attendance_stats"]["absent"]} days
        Late: {data["attendance_stats"]["late"]} days
        Excused: {data["attendance_stats"]["excused"]} days
        
        COURSE-WISE ATTENDANCE:
        {json.dumps(data["course_attendance"], indent=2)}
        
        Please provide a comprehensive analysis including:
        1. Overall attendance pattern assessment
        2. Identification of courses with attendance issues
        3. Trends in attendance (e.g., particular days or times with lower attendance)
        4. Impact of attendance on academic performance
        5. Specific recommendations to improve attendance
        6. Strategies for better time management
        
        Format your response in clear sections with headings and bullet points where appropriate.
        """
    elif analysis_type == "exams":
        prompt = f"""
        You are an expert academic advisor. Analyze the following student's exam performance:
        
        STUDENT INFORMATION:
        Name: {data["student_info"]["name"]}
        Email: {data["student_info"]["email"]}
        Student ID: {data["student_info"]["student_id"]}
        Department: {data["student_info"]["department"]}
        
        EXAM RESULTS:
        {json.dumps(data["exam_results"], indent=2)}
        
        SUBJECT PERFORMANCE:
        {json.dumps(data["subject_performance"], indent=2)}
        
        Please provide a comprehensive analysis including:
        1. Overall performance assessment
        2. Identification of strengths and weaknesses by subject
        3. Performance trends over time
        4. Comparison with class averages where available
        5. Specific study strategies for improvement in weaker subjects
        6. Recommendations for maintaining performance in stronger subjects
        7. Test-taking strategies that might help improve scores
        
        Format your response in clear sections with headings and bullet points where appropriate.
        """
    elif analysis_type == "certificates":
        prompt = f"""
        You are an expert career counselor. Analyze the following student's certificate portfolio:
        
        STUDENT INFORMATION:
        Name: {data["student_info"]["name"]}
        Email: {data["student_info"]["email"]}
        Student ID: {data["student_info"]["student_id"]}
        Department: {data["student_info"]["department"]}
        
        CERTIFICATES:
        {json.dumps(data["certificates"], indent=2)}
        
        Please provide a comprehensive analysis including:
        1. Overall assessment of the certificate portfolio
        2. Relevance of certificates to the student's field of study
        3. Skills demonstrated through these certificates
        4. Gaps in the portfolio that could be addressed
        5. Recommendations for additional certificates that would enhance employability
        6. How to effectively showcase these certificates on a resume and in interviews
        7. Potential career paths these certificates support
        
        Format your response in clear sections with headings and bullet points where appropriate.
        """
    elif analysis_type == "profile":
        prompt = f"""
        You are an expert academic and career advisor. Analyze the following student's complete profile:
        
        STUDENT INFORMATION:
        Name: {data["student_info"]["name"]}
        Email: {data["student_info"]["email"]}
        Student ID: {data["student_info"]["student_id"]}
        Department: {data["student_info"]["department"]}
        Year: {data["student_info"]["year"]}
        Semester: {data["student_info"]["semester"]}
        Section: {data["student_info"]["section"]}
        
        ACADEMIC PERFORMANCE:
        {json.dumps(data["academic_performance"], indent=2)}
        
        ATTENDANCE:
        {json.dumps(data["attendance"], indent=2)}
        
        COURSE PERFORMANCE:
        {json.dumps(data["course_performance"], indent=2)}
        
        CERTIFICATES:
        {json.dumps(data["certificates"], indent=2) if "certificates" in data else "No certificates available"}
        
        Please provide a comprehensive analysis including:
        1. Overall academic profile assessment
        2. Strengths and areas for improvement
        3. Correlation between attendance and academic performance
        4. Course-specific insights and recommendations
        5. Career readiness assessment
        6. Personalized academic improvement plan
        7. Recommended extracurricular activities and skill development
        8. Potential career paths based on current performance and interests
        
        Format your response in clear sections with headings and bullet points where appropriate.
        """
    else:
        return f"Error: Unknown analysis type '{analysis_type}'"
    
    # Generate response from Gemini
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_message = f"Error generating analysis: {str(e)}"
        st.error(error_message)
        return error_message

def show_ai_analysis_button(data, analysis_type):
    """
    Display a button to trigger AI analysis and show results.
    
    Args:
        data (dict): The data to analyze
        analysis_type (str): Type of analysis to perform
    """
    # Create a unique key for this analysis button
    button_key = f"analyze_{analysis_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create a container for the analysis
    analysis_container = st.container()
    
    with analysis_container:
        # Show analysis button
        if st.button("Analyze with AI", key=button_key):
            with st.spinner("Generating AI analysis..."):
                # Call Gemini API
                analysis_result = analyze_with_gemini(data, analysis_type)
                
                # Display results
                if analysis_result.startswith("Error:"):
                    st.error(analysis_result)
                else:
                    st.markdown("## AI Analysis Results")
                    st.markdown(analysis_result)
                    
                    # Add option to download as PDF if needed
                    if st.button("Download Analysis as PDF"):
                        try:
                            from reportlab.lib import colors
                            from reportlab.lib.pagesizes import letter
                            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                            from reportlab.lib.units import inch
                            
                            # Create PDF file path
                            pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "analysis")
                            os.makedirs(pdf_dir, exist_ok=True)
                            
                            pdf_file_path = os.path.join(pdf_dir, f"{analysis_type}_analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
                            
                            # Create PDF document
                            doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
                            styles = getSampleStyleSheet()
                            
                            # Create content elements
                            elements = []
                            
                            # Add title
                            title_style = styles["Heading1"]
                            elements.append(Paragraph(f"AI Analysis: {analysis_type.capitalize()}", title_style))
                            elements.append(Spacer(1, 0.25*inch))
                            
                            # Add student info
                            elements.append(Paragraph(f"<b>{data['student_info']['name']}</b>", styles["Heading2"]))
                            elements.append(Spacer(1, 0.1*inch))
                            
                            info_style = styles["Normal"]
                            elements.append(Paragraph(f"<b>Email:</b> {data['student_info']['email']}", info_style))
                            elements.append(Paragraph(f"<b>Student ID:</b> {data['student_info']['student_id']}", info_style))
                            elements.append(Paragraph(f"<b>Department:</b> {data['student_info']['department']}", info_style))
                            elements.append(Spacer(1, 0.25*inch))
                            
                            # Add analysis content
                            elements.append(Paragraph("<b>Analysis Results</b>", styles["Heading3"]))
                            elements.append(Spacer(1, 0.1*inch))
                            
                            # Split the analysis by lines and add as paragraphs
                            for line in analysis_result.split('\n'):
                                if line.strip():
                                    # Check if it's a heading
                                    if line.strip().startswith('#'):
                                        heading_level = line.count('#')
                                        heading_text = line.strip('#').strip()
                                        if heading_level <= 2:
                                            elements.append(Paragraph(f"<b>{heading_text}</b>", styles["Heading2"]))
                                        else:
                                            elements.append(Paragraph(f"<b>{heading_text}</b>", styles["Heading3"]))
                                    else:
                                        elements.append(Paragraph(line, styles["Normal"]))
                                    elements.append(Spacer(1, 0.05*inch))
                            
                            # Add footer
                            elements.append(Spacer(1, 0.5*inch))
                            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Italic"]))
                            
                            # Build PDF
                            doc.build(elements)
                            
                            # Provide download link
                            with open(pdf_file_path, "rb") as f:
                                st.download_button(
                                    label="Download PDF",
                                    data=f,
                                    file_name=os.path.basename(pdf_file_path),
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
                            st.info("To generate PDF reports, please install reportlab. Run: pip install reportlab")

def check_gemini_api_availability():
    """
    Check if the Gemini API is available and the model exists.
    
    Returns:
        tuple: (is_available, message)
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        return False, "API key is not set"
    
    try:
        # Make a simple request to check if the API is available
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return False, f"API returned status code {response.status_code}: {response.text}"
        
        # Check if the model exists
        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]
        
        # Check for both model names (with and without prefix)
        target_models = ["gemini-2.0-flash", "models/gemini-2.0-flash"]
        model_exists = any(model in model_names for model in target_models)
        
        if not model_exists:
            available_models = ", ".join(model_names[:5])
            return False, f"Model 'gemini-2.0-flash' not found. Available models: {available_models}..."
        
        return True, "API is available and model exists"
    except Exception as e:
        return False, f"Error checking API availability: {str(e)}"

def analyze_resume_with_gemini(resume_path):
    """
    Analyze a resume using Google's Gemini 2.0 Flash API.
    
    Args:
        resume_path (str): Path to the resume PDF file
        
    Returns:
        dict: Analysis results including ATS score and improvement suggestions
    """
    # API key for Gemini
    api_key = "AIzaSyAisOs1gZstorFU109cha8ry14H-AirnWI"
    
    # Extract text from PDF
    try:
        with open(resume_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            resume_text = ""
            for page in pdf_reader.pages:
                resume_text += page.extract_text()
            
            if not resume_text.strip():
                return {"error": "No text could be extracted from the PDF. The resume might be image-based or protected."}
            
            # Log the first 100 characters of extracted text for debugging
            st.write(f"Extracted text (first 100 chars): {resume_text[:100]}...")
    except Exception as e:
        return {"error": f"Failed to extract text from PDF: {str(e)}"}
    
    # Prepare the prompt for Gemini
    prompt = f"""
    You are an expert resume reviewer and ATS (Applicant Tracking System) specialist.
    Please analyze the following resume and provide:
    
    1. An ATS compatibility score (0-100)
    2. Strengths of the resume
    3. Weaknesses that need improvement
    4. Specific suggestions to improve the resume
    5. Keywords that are present and relevant
    6. Important keywords that are missing
    
    Format your response as JSON with the following structure:
    {{
        "ats_score": number,
        "strengths": [list of strengths],
        "weaknesses": [list of weaknesses],
        "improvement_suggestions": [list of specific suggestions],
        "present_keywords": [list of relevant keywords present],
        "missing_keywords": [list of important keywords missing]
    }}
    
    Here is the resume text:
    {resume_text}
    """
    
    # Try using the google.generativeai library first
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            result_text = response.text
            
            # Extract the JSON part from the response
            try:
                # Find JSON in the response (it might be wrapped in ```json ... ``` or just plain JSON)
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    json_str = result_text.split("```")[1].strip()
                else:
                    json_str = result_text.strip()
                
                # Parse the JSON
                analysis_result = json.loads(json_str)
                return analysis_result
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse JSON from API response: {e}")
                st.write("Raw response:", result_text)
                
                # Fallback: Create a structured response manually
                return {
                    "ats_score": 50,
                    "strengths": ["Could not parse API response. Here's the raw text:", result_text[:200] + "..."],
                    "weaknesses": ["API response parsing failed"],
                    "improvement_suggestions": ["Please try again later"],
                    "present_keywords": [],
                    "missing_keywords": []
                }
        else:
            st.error("Empty or invalid response from Gemini API")
            return {"error": "Empty or invalid response from Gemini API"}
            
    except Exception as e:
        st.error(f"Error using google.generativeai library: {str(e)}")
        # Continue to fallback method
    
    # Fallback: Use direct REST API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        
        # Log response status and headers for debugging
        st.write(f"API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            st.error(f"API Error: {response.text}")
            return {"error": f"API returned status code {response.status_code}: {response.text}"}
        
        response_json = response.json()
        
        # Log the structure of the response for debugging
        st.write("Response structure:", list(response_json.keys()))
        
        # Extract the text from the response
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            content = response_json["candidates"][0]["content"]
            if "parts" in content and len(content["parts"]) > 0:
                result_text = content["parts"][0]["text"]
                
                # Extract the JSON part from the response
                try:
                    # Find JSON in the response (it might be wrapped in ```json ... ``` or just plain JSON)
                    if "```json" in result_text:
                        json_str = result_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in result_text:
                        json_str = result_text.split("```")[1].strip()
                    else:
                        json_str = result_text.strip()
                    
                    # Parse the JSON
                    analysis_result = json.loads(json_str)
                    return analysis_result
                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse JSON from API response: {e}")
                    st.write("Raw response:", result_text)
                    
                    # Create a structured response manually
                    return {
                        "ats_score": 50,
                        "strengths": ["Could not parse API response. Here's the raw text:", result_text[:200] + "..."],
                        "weaknesses": ["API response parsing failed"],
                        "improvement_suggestions": ["Please try again later"],
                        "present_keywords": [],
                        "missing_keywords": []
                    }
            else:
                st.error("No parts found in content")
                st.write("Response content:", content)
        else:
            st.error("No candidates found in response")
            st.write("Response JSON:", response_json)
        
        return {"error": "Failed to get proper response from Gemini API. See logs for details."}
    
    except Exception as e:
        st.error(f"API request failed: {str(e)}")
        return {"error": f"API request failed: {str(e)}"}

def show_resume_analysis_section(resume_path):
    """
    Show the resume analysis section with ATS score and improvement suggestions.
    
    Args:
        resume_path (str): Path to the resume PDF file
    """
    st.markdown("## Resume AI Analysis")
    st.markdown("Get an AI-powered analysis of your resume to improve your chances of passing ATS systems.")
    
    if not os.path.exists(resume_path):
        st.warning("Please upload a resume first before requesting analysis.")
        return
    
    # Display file information
    try:
        file_size = os.path.getsize(resume_path) / 1024  # Size in KB
        st.info(f"Resume file: {os.path.basename(resume_path)} ({file_size:.1f} KB)")
    except Exception as e:
        st.error(f"Error accessing file: {str(e)}")
    
    # Add option to use test mode with sample data
    use_test_mode = st.checkbox("Use test mode (for debugging)", value=False)
    
    if st.button("Analyze My Resume", key="analyze_resume_button"):
        with st.spinner("Analyzing your resume... This may take a moment."):
            if use_test_mode:
                # Use sample data for testing
                analysis_result = {
                    "ats_score": 75,
                    "strengths": [
                        "Clear organization and structure",
                        "Quantifiable achievements",
                        "Relevant technical skills highlighted"
                    ],
                    "weaknesses": [
                        "Missing some industry-specific keywords",
                        "Objective statement could be more targeted"
                    ],
                    "improvement_suggestions": [
                        "Add more industry-specific keywords relevant to your target role",
                        "Replace objective with a professional summary",
                        "Include more metrics and quantifiable results"
                    ],
                    "present_keywords": [
                        "project management",
                        "team leadership",
                        "data analysis"
                    ],
                    "missing_keywords": [
                        "agile methodology",
                        "strategic planning",
                        "stakeholder management"
                    ]
                }
                st.success("Analysis completed in test mode!")
            else:
                # Create a placeholder for debug information
                debug_expander = st.expander("Debug Information (expand if analysis fails)", expanded=False)
                
                with debug_expander:
                    st.write("Starting analysis...")
                
                # Perform actual analysis
                analysis_result = analyze_resume_with_gemini(resume_path)
                
                # Check for errors
                if "error" in analysis_result:
                    error_msg = analysis_result["error"]
                    st.error(f"Analysis failed: {error_msg}")
                    
                    with debug_expander:
                        st.error("Analysis failed with error:")
                        st.code(error_msg)
                        
                        # Suggest solutions
                        st.markdown("### Possible solutions:")
                        st.markdown("1. Check if your resume PDF is text-based and not just images")
                        st.markdown("2. Try uploading a simpler version of your resume")
                        st.markdown("3. Ensure your internet connection is stable")
                        st.markdown("4. Try using test mode to see how the feature works")
                        st.markdown("5. The API key might have reached its quota or expired")
                    
                    return
            
            # Display ATS Score with a gauge
            ats_score = analysis_result.get("ats_score", 0)
            
            # Create score color and emoji based on score
            if ats_score >= 80:
                score_color = "green"
                score_emoji = "🌟"
            elif ats_score >= 60:
                score_color = "orange"
                score_emoji = "⭐"
            else:
                score_color = "red"
                score_emoji = "⚠️"
                
            # Display score with color and emoji
            st.markdown(f"<h3 style='color: {score_color};'>{score_emoji} ATS Compatibility Score: {ats_score}/100</h3>", unsafe_allow_html=True)
            
            # Create a progress bar for the ATS score
            st.progress(ats_score/100)
            
            # Add score interpretation
            if ats_score >= 80:
                st.success("Excellent! Your resume is well-optimized for ATS systems.")
            elif ats_score >= 60:
                st.warning("Good, but there's room for improvement in your resume's ATS compatibility.")
            else:
                st.error("Your resume needs significant improvements to pass ATS systems effectively.")
            
            # Display strengths
            st.markdown("### Strengths")
            strengths = analysis_result.get("strengths", [])
            if strengths:
                for strength in strengths:
                    st.markdown(f"✅ {strength}")
            else:
                st.info("No specific strengths identified.")
            
            # Display weaknesses
            st.markdown("### Areas for Improvement")
            weaknesses = analysis_result.get("weaknesses", [])
            if weaknesses:
                for weakness in weaknesses:
                    st.markdown(f"⚠️ {weakness}")
            else:
                st.info("No specific weaknesses identified.")
            
            # Display improvement suggestions
            st.markdown("### Specific Suggestions")
            suggestions = analysis_result.get("improvement_suggestions", [])
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    st.markdown(f"{i}. {suggestion}")
            else:
                st.info("No specific suggestions available.")
            
            # Display keywords
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Present Keywords")
                present_keywords = analysis_result.get("present_keywords", [])
                if present_keywords:
                    for keyword in present_keywords:
                        st.markdown(f"- {keyword}")
                else:
                    st.info("No specific keywords identified.")
            
            with col2:
                st.markdown("### Missing Keywords")
                missing_keywords = analysis_result.get("missing_keywords", [])
                if missing_keywords:
                    for keyword in missing_keywords:
                        st.markdown(f"- {keyword}")
                else:
                    st.info("No missing keywords identified.")
                    
            # Add a section with general resume tips
            with st.expander("General Resume Tips", expanded=False):
                st.markdown("""
                ### General Resume Tips
                
                1. **Keep it concise**: Limit your resume to 1-2 pages
                2. **Use a clean, professional format**: Ensure consistent formatting throughout
                3. **Tailor for each job**: Customize your resume for each position you apply for
                4. **Focus on achievements**: Use metrics and numbers to quantify your accomplishments
                5. **Use action verbs**: Start bullet points with strong action verbs
                6. **Proofread carefully**: Eliminate spelling and grammar errors
                7. **Include relevant keywords**: Incorporate keywords from the job description
                8. **Use a professional email**: Avoid unprofessional email addresses
                9. **Update regularly**: Keep your resume current with your latest experience
                10. **Save as PDF**: Submit your resume as a PDF to preserve formatting
                """)
                
            # Add download option for the analysis
            st.markdown("### Save Your Analysis")
            if st.button("Generate Analysis Report"):
                # Create a text report
                report = f"""
                # Resume ATS Analysis Report
                
                ## ATS Compatibility Score: {ats_score}/100
                
                ## Strengths:
                {chr(10).join(['- ' + s for s in strengths])}
                
                ## Areas for Improvement:
                {chr(10).join(['- ' + w for w in weaknesses])}
                
                ## Specific Suggestions:
                {chr(10).join([f'{i+1}. {s}' for i, s in enumerate(suggestions)])}
                
                ## Present Keywords:
                {chr(10).join(['- ' + k for k in present_keywords])}
                
                ## Missing Keywords:
                {chr(10).join(['- ' + k for k in missing_keywords])}
                
                ## Analysis Date:
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                # Provide download button for the report
                st.download_button(
                    label="Download Analysis Report",
                    data=report,
                    file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                ) 