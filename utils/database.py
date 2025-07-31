import json
import os
import pandas as pd
from datetime import datetime

# File paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "assignments.json")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions.json")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")
CERTIFICATES_FILE = os.path.join(DATA_DIR, "certificates.json")
ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, "announcements.json")
EXAMS_FILE = os.path.join(DATA_DIR, "exams.json")
SUBJECTS_FILE = os.path.join(DATA_DIR, "subjects.json")
EXAM_RESULTS_FILE = os.path.join(DATA_DIR, "exam_results.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def init_data_files():
    """Initialize all data files with default structure if they don't exist."""
    default_files = {
        COURSES_FILE: {},
        ATTENDANCE_FILE: {},
        ASSIGNMENTS_FILE: {},
        SUBMISSIONS_FILE: {},
        PROJECTS_FILE: {},
        CERTIFICATES_FILE: {},
        ANNOUNCEMENTS_FILE: [],
        EXAMS_FILE: {},
        SUBJECTS_FILE: {},
        EXAM_RESULTS_FILE: {}
    }
    
    for file_path, default_data in default_files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)

def load_data(file_path):
    """Load data from a JSON file."""
    if not os.path.exists(file_path):
        # Create the file with empty data
        with open(file_path, 'w') as f:
            if file_path == ANNOUNCEMENTS_FILE:
                json.dump([], f, indent=4)
            else:
                json.dump({}, f, indent=4)
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Course Management
def get_courses():
    """Get all courses."""
    return load_data(COURSES_FILE)

def add_course(course_id, course_name, department, teacher_email, description="", credits=3):
    """Add a new course."""
    courses = get_courses()
    
    if course_id in courses:
        return False, "Course ID already exists"
    
    courses[course_id] = {
        "course_name": course_name,
        "department": department,
        "teacher_email": teacher_email,
        "description": description,
        "credits": credits,
        "created_at": datetime.now().isoformat()
    }
    
    save_data(COURSES_FILE, courses)
    return True, "Course added successfully"

def update_course(course_id, **kwargs):
    """Update a course."""
    courses = get_courses()
    
    if course_id not in courses:
        return False, "Course not found"
    
    courses[course_id].update(kwargs)
    save_data(COURSES_FILE, courses)
    return True, "Course updated successfully"

def delete_course(course_id):
    """Delete a course."""
    courses = get_courses()
    
    if course_id not in courses:
        return False, "Course not found"
    
    del courses[course_id]
    save_data(COURSES_FILE, courses)
    return True, "Course deleted successfully"

def get_teacher_courses(teacher_email):
    """Get all courses taught by a teacher."""
    courses = get_courses()
    return {k: v for k, v in courses.items() if v.get("teacher_email") == teacher_email}

# Attendance Management
def get_attendance():
    """Get all attendance records."""
    return load_data(ATTENDANCE_FILE)

def mark_attendance(course_id, date, student_email, status):
    """Mark attendance for a student."""
    attendance = get_attendance()
    
    if course_id not in attendance:
        attendance[course_id] = {}
    
    if date not in attendance[course_id]:
        attendance[course_id][date] = {}
    
    attendance[course_id][date][student_email] = {
        "status": status,
        "marked_at": datetime.now().isoformat()
    }
    
    save_data(ATTENDANCE_FILE, attendance)
    return True, "Attendance marked successfully"

def get_student_attendance(student_email):
    """Get attendance records for a student."""
    attendance = get_attendance()
    result = {}
    
    for course_id, dates in attendance.items():
        result[course_id] = {}
        for date, students in dates.items():
            if student_email in students:
                result[course_id][date] = students[student_email]
    
    return result

def get_course_attendance(course_id):
    """Get attendance records for a course."""
    attendance = get_attendance()
    return attendance.get(course_id, {})

# Assignment Management
def get_assignments():
    """Get all assignments."""
    return load_data(ASSIGNMENTS_FILE)

def create_assignment(course_id, title, description, due_date, max_points=100):
    """Create a new assignment."""
    assignments = get_assignments()
    
    if course_id not in assignments:
        assignments[course_id] = []
    
    assignment_id = f"{course_id}_{len(assignments[course_id]) + 1}"
    
    assignments[course_id].append({
        "assignment_id": assignment_id,
        "title": title,
        "description": description,
        "due_date": due_date,
        "max_points": max_points,
        "created_at": datetime.now().isoformat()
    })
    
    save_data(ASSIGNMENTS_FILE, assignments)
    return True, "Assignment created successfully", assignment_id

def update_assignment(course_id, assignment_id, **kwargs):
    """Update an assignment."""
    assignments = get_assignments()
    
    if course_id not in assignments:
        return False, "Course not found"
    
    for i, assignment in enumerate(assignments[course_id]):
        if assignment["assignment_id"] == assignment_id:
            assignments[course_id][i].update(kwargs)
            save_data(ASSIGNMENTS_FILE, assignments)
            return True, "Assignment updated successfully"
    
    return False, "Assignment not found"

def delete_assignment(course_id, assignment_id):
    """Delete an assignment."""
    assignments = get_assignments()
    
    if course_id not in assignments:
        return False, "Course not found"
    
    for i, assignment in enumerate(assignments[course_id]):
        if assignment["assignment_id"] == assignment_id:
            del assignments[course_id][i]
            save_data(ASSIGNMENTS_FILE, assignments)
            return True, "Assignment deleted successfully"
    
    return False, "Assignment not found"

def get_course_assignments(course_id):
    """Get all assignments for a course."""
    assignments = get_assignments()
    return assignments.get(course_id, [])

# Submission Management
def get_submissions():
    """Get all submissions."""
    return load_data(SUBMISSIONS_FILE)

def submit_assignment(assignment_id, student_email, submission_text, file_path=None):
    """Submit an assignment."""
    submissions = get_submissions()
    
    if assignment_id not in submissions:
        submissions[assignment_id] = []
    
    # Check if student has already submitted
    for submission in submissions[assignment_id]:
        if submission["student_email"] == student_email:
            return False, "You have already submitted this assignment"
    
    submissions[assignment_id].append({
        "student_email": student_email,
        "submission_text": submission_text,
        "file_path": file_path,
        "submitted_at": datetime.now().isoformat(),
        "grade": None,
        "feedback": None
    })
    
    save_data(SUBMISSIONS_FILE, submissions)
    return True, "Assignment submitted successfully"

def grade_submission(assignment_id, student_email, grade, feedback=None):
    """Grade a submission."""
    submissions = get_submissions()
    
    if assignment_id not in submissions:
        return False, "Assignment not found"
    
    for i, submission in enumerate(submissions[assignment_id]):
        if submission["student_email"] == student_email:
            submissions[assignment_id][i]["grade"] = grade
            submissions[assignment_id][i]["feedback"] = feedback
            submissions[assignment_id][i]["graded_at"] = datetime.now().isoformat()
            
            save_data(SUBMISSIONS_FILE, submissions)
            return True, "Submission graded successfully"
    
    return False, "Submission not found"

def get_student_submissions(student_email):
    """Get all submissions for a student."""
    submissions = get_submissions()
    result = []
    
    for assignment_id, assignment_submissions in submissions.items():
        for submission in assignment_submissions:
            if submission["student_email"] == student_email:
                # Add assignment_id to the submission object
                submission_copy = submission.copy()
                submission_copy["assignment_id"] = assignment_id
                result.append(submission_copy)
    
    return result

def get_assignment_submissions(assignment_id):
    """Get all submissions for an assignment."""
    submissions = get_submissions()
    return submissions.get(assignment_id, [])

# Project Management
def get_projects():
    """Get all projects."""
    return load_data(PROJECTS_FILE)

def create_project(course_id, title, description, due_date, max_points=100, group_project=False):
    """Create a new project."""
    projects = get_projects()
    
    if course_id not in projects:
        projects[course_id] = []
    
    project_id = f"{course_id}_project_{len(projects[course_id]) + 1}"
    
    projects[course_id].append({
        "project_id": project_id,
        "title": title,
        "description": description,
        "due_date": due_date,
        "max_points": max_points,
        "group_project": group_project,
        "created_at": datetime.now().isoformat()
    })
    
    save_data(PROJECTS_FILE, projects)
    return True, "Project created successfully", project_id

def submit_project(project_id, student_email, submission_text, file_path=None, group_members=None):
    """Submit a project."""
    submissions = get_submissions()
    
    if project_id not in submissions:
        submissions[project_id] = []
    
    # Check if student has already submitted
    for submission in submissions[project_id]:
        if submission["student_email"] == student_email:
            return False, "You have already submitted this project"
    
    submissions[project_id].append({
        "student_email": student_email,
        "submission_text": submission_text,
        "file_path": file_path,
        "group_members": group_members,
        "submitted_at": datetime.now().isoformat(),
        "grade": None,
        "feedback": None
    })
    
    save_data(SUBMISSIONS_FILE, submissions)
    return True, "Project submitted successfully"

# Certificate Management
def get_certificates():
    """Get all certificates."""
    return load_data(CERTIFICATES_FILE)

def submit_certificate(student_email, title, issuing_organization, issue_date, file_path=None):
    """Submit a certificate."""
    certificates = get_certificates()
    
    if student_email not in certificates:
        certificates[student_email] = []
    
    certificate_id = f"{student_email}_{len(certificates[student_email]) + 1}"
    
    certificates[student_email].append({
        "certificate_id": certificate_id,
        "title": title,
        "issuing_organization": issuing_organization,
        "issue_date": issue_date,
        "file_path": file_path,
        "submitted_at": datetime.now().isoformat(),
        "verified": False
    })
    
    save_data(CERTIFICATES_FILE, certificates)
    return True, "Certificate submitted successfully"

def verify_certificate(student_email, certificate_id):
    """Verify a certificate."""
    certificates = get_certificates()
    
    if student_email not in certificates:
        return False, "Student not found"
    
    for i, certificate in enumerate(certificates[student_email]):
        if certificate["certificate_id"] == certificate_id:
            certificates[student_email][i]["verified"] = True
            certificates[student_email][i]["verified_at"] = datetime.now().isoformat()
            
            save_data(CERTIFICATES_FILE, certificates)
            return True, "Certificate verified successfully"
    
    return False, "Certificate not found"

def get_student_certificates(student_email):
    """
    Get certificates for a specific student.
    
    Args:
        student_email (str): The student's email
        
    Returns:
        list: List of certificate objects for the student
    """
    certificates = load_data("certificates.json")
    
    # Filter certificates for this student
    student_certificates = []
    
    for cert_id, cert in certificates.items():
        if cert.get("student_email") == student_email:
            # Add certificate ID to the certificate object
            cert_copy = cert.copy()
            cert_copy["certificate_id"] = cert_id
            student_certificates.append(cert_copy)
    
    return student_certificates

# Announcement Management
def get_announcements():
    """Get all announcements."""
    return load_data(ANNOUNCEMENTS_FILE)

def create_announcement(title, content, author_email, target_roles=None, target_departments=None, target_emails=None):
    """Create a new announcement.
    
    Args:
        title (str): The announcement title
        content (str): The announcement content
        author_email (str): Email of the author
        target_roles (list, optional): List of roles that should see this announcement
        target_departments (list, optional): List of departments that should see this announcement
        target_emails (list, optional): List of specific user emails that should see this announcement
    
    Returns:
        tuple: (success, message)
    """
    announcements = get_announcements()
    
    announcement_id = len(announcements) + 1
    
    announcements.append({
        "announcement_id": announcement_id,
        "title": title,
        "content": content,
        "author_email": author_email,
        "target_roles": target_roles,
        "target_departments": target_departments,
        "target_emails": target_emails,
        "created_at": datetime.now().isoformat()
    })
    
    save_data(ANNOUNCEMENTS_FILE, announcements)
    return True, "Announcement created successfully"

def delete_announcement(announcement_id):
    """Delete an announcement."""
    announcements = get_announcements()
    
    for i, announcement in enumerate(announcements):
        if announcement["announcement_id"] == announcement_id:
            del announcements[i]
            save_data(ANNOUNCEMENTS_FILE, announcements)
            return True, "Announcement deleted successfully"
    
    return False, "Announcement not found"

def get_filtered_announcements(role=None, department=None, email=None):
    """Get announcements filtered by role, department, and email.
    
    Args:
        role (str, optional): User role to filter by
        department (str, optional): Department to filter by
        email (str, optional): User email to filter by
    
    Returns:
        list: Filtered announcements
    """
    announcements = get_announcements()
    
    filtered = []
    for announcement in announcements:
        target_roles = announcement.get("target_roles", [])
        target_departments = announcement.get("target_departments", [])
        target_emails = announcement.get("target_emails", [])
        
        # Include if:
        # 1. No specific targets (announcement for everyone), OR
        # 2. User's role matches target roles, OR
        # 3. User's department matches target departments, OR
        # 4. User's email matches target emails
        if (not target_roles and not target_departments and not target_emails) or \
           (role and target_roles and role in target_roles) or \
           (department and target_departments and department in target_departments) or \
           (email and target_emails and email in target_emails):
            filtered.append(announcement)
    
    return filtered

def remove_student_from_course(course_id, student_email):
    """Remove a student from a course by removing their attendance records."""
    # Get attendance records
    attendance = get_attendance()
    
    if course_id not in attendance:
        return False, "Course not found"
    
    # Remove student from all attendance dates
    removed = False
    for date in attendance[course_id]:
        if student_email in attendance[course_id][date]:
            del attendance[course_id][date][student_email]
            removed = True
    
    # Save updated attendance
    if removed:
        save_data(ATTENDANCE_FILE, attendance)
        
        # Also remove student's submissions for this course
        submissions = get_submissions()
        
        # Get assignments and projects for this course
        assignments = get_assignments().get(course_id, [])
        projects = get_projects().get(course_id, [])
        
        # Check assignments
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id")
            if assignment_id in submissions:
                submissions[assignment_id] = [
                    s for s in submissions[assignment_id] 
                    if s.get("student_email") != student_email
                ]
        
        # Check projects
        for project in projects:
            project_id = project.get("project_id")
            if project_id in submissions:
                submissions[project_id] = [
                    s for s in submissions[project_id] 
                    if s.get("student_email") != student_email
                ]
        
        # Save updated submissions
        save_data(SUBMISSIONS_FILE, submissions)
        
        return True, f"Student {student_email} removed from course {course_id}"
    
    return False, f"Student {student_email} not found in course {course_id}"

# Exam Functions
def get_subjects():
    """Get all subjects."""
    return load_data(SUBJECTS_FILE)

def get_subject(subject_id):
    """Get a specific subject by ID."""
    subjects = get_subjects()
    return subjects.get(subject_id)

def add_subject(subject_name, semester, department=None):
    """Add a new subject."""
    subjects = get_subjects()
    
    # Generate a unique subject ID
    subject_id = f"subject_{len(subjects) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create subject
    subjects[subject_id] = {
        "subject_id": subject_id,
        "subject_name": subject_name,
        "semester": semester,
        "department": department
    }
    
    # Save subjects
    save_data(SUBJECTS_FILE, subjects)
    
    return subject_id

def update_subject(subject_id, subject_name=None, semester=None, department=None):
    """Update a subject."""
    subjects = get_subjects()
    
    if subject_id not in subjects:
        return False
    
    if subject_name:
        subjects[subject_id]["subject_name"] = subject_name
    
    if semester:
        subjects[subject_id]["semester"] = semester
    
    if department:
        subjects[subject_id]["department"] = department
    
    # Save subjects
    save_data(SUBJECTS_FILE, subjects)
    
    return True

def delete_subject(subject_id):
    """Delete a subject."""
    subjects = get_subjects()
    
    if subject_id not in subjects:
        return False
    
    # Delete subject
    del subjects[subject_id]
    
    # Save subjects
    save_data(SUBJECTS_FILE, subjects)
    
    return True

def get_exams():
    """Get all exams."""
    return load_data(EXAMS_FILE)

def get_exam(exam_id):
    """Get a specific exam by ID."""
    exams = get_exams()
    return exams.get(exam_id)

def add_exam(exam_name, exam_type, semester, date, max_marks=100):
    """Add a new exam.
    
    Args:
        exam_name: Name of the exam
        exam_type: Type of exam (e.g., "Mid Sem 1", "Mid Sem 2", "End Sem")
        semester: Semester for which the exam is conducted
        date: Date of the exam
        max_marks: Maximum marks for the exam
    
    Returns:
        exam_id: ID of the created exam
    """
    exams = get_exams()
    
    # Generate a unique exam ID
    exam_id = f"exam_{len(exams) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create exam
    exams[exam_id] = {
        "exam_id": exam_id,
        "exam_name": exam_name,
        "exam_type": exam_type,
        "semester": semester,
        "date": date,
        "max_marks": max_marks,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save exams
    save_data(EXAMS_FILE, exams)
    
    return exam_id

def update_exam(exam_id, exam_name=None, exam_type=None, semester=None, date=None, max_marks=None):
    """Update an exam."""
    exams = get_exams()
    
    if exam_id not in exams:
        return False
    
    if exam_name:
        exams[exam_id]["exam_name"] = exam_name
    
    if exam_type:
        exams[exam_id]["exam_type"] = exam_type
    
    if semester:
        exams[exam_id]["semester"] = semester
    
    if date:
        exams[exam_id]["date"] = date
    
    if max_marks:
        exams[exam_id]["max_marks"] = max_marks
    
    # Save exams
    save_data(EXAMS_FILE, exams)
    
    return True

def delete_exam(exam_id):
    """Delete an exam."""
    exams = get_exams()
    
    if exam_id not in exams:
        return False
    
    # Delete exam
    del exams[exam_id]
    
    # Save exams
    save_data(EXAMS_FILE, exams)
    
    # Delete all results for this exam
    delete_exam_results(exam_id)
    
    return True

def get_exam_results():
    """Get all exam results."""
    return load_data(EXAM_RESULTS_FILE)

def get_student_exam_results(student_email):
    """Get exam results for a specific student."""
    results = get_exam_results()
    student_results = {}
    
    for exam_id, exam_data in results.items():
        if student_email in exam_data:
            if exam_id not in student_results:
                student_results[exam_id] = {}
            
            student_results[exam_id] = exam_data[student_email]
    
    return student_results

def get_exam_results_by_exam(exam_id):
    """Get results for a specific exam."""
    results = get_exam_results()
    return results.get(exam_id, {})

def add_exam_result(exam_id, student_email, subject_id, marks, remarks=None):
    """Add or update an exam result for a student.
    
    Args:
        exam_id: ID of the exam
        student_email: Email of the student
        subject_id: ID of the subject
        marks: Marks obtained by the student
        remarks: Optional remarks
    
    Returns:
        bool: True if successful, False otherwise
    """
    results = get_exam_results()
    
    # Initialize exam if not exists
    if exam_id not in results:
        results[exam_id] = {}
    
    # Initialize student if not exists
    if student_email not in results[exam_id]:
        results[exam_id][student_email] = {}
    
    # Add result
    results[exam_id][student_email][subject_id] = {
        "marks": marks,
        "remarks": remarks,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save results
    save_data(EXAM_RESULTS_FILE, results)
    
    return True

def delete_exam_result(exam_id, student_email, subject_id):
    """Delete an exam result."""
    results = get_exam_results()
    
    if exam_id not in results:
        return False
    
    if student_email not in results[exam_id]:
        return False
    
    if subject_id not in results[exam_id][student_email]:
        return False
    
    # Delete result
    del results[exam_id][student_email][subject_id]
    
    # Clean up empty structures
    if not results[exam_id][student_email]:
        del results[exam_id][student_email]
    
    if not results[exam_id]:
        del results[exam_id]
    
    # Save results
    save_data(EXAM_RESULTS_FILE, results)
    
    return True

def delete_exam_results(exam_id):
    """Delete all results for an exam."""
    results = get_exam_results()
    
    if exam_id not in results:
        return False
    
    # Delete all results for this exam
    del results[exam_id]
    
    # Save results
    save_data(EXAM_RESULTS_FILE, results)
    
    return True

# Initialize all data files
init_data_files() 