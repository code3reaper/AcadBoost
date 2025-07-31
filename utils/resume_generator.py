import os
import subprocess
import tempfile
import platform
import streamlit as st
from datetime import datetime
import shutil

def find_pdflatex():
    """
    Find the pdflatex executable on the system.
    
    Returns:
        str: Path to pdflatex executable or just 'pdflatex' if in PATH
    """
    # First check if pdflatex is in PATH
    if shutil.which("pdflatex"):
        return "pdflatex"
    
    # On Windows, check common MiKTeX installation paths
    if platform.system() == "Windows":
        # Check if MiKTeX is in the PATH using where command
        try:
            result = subprocess.run(["where", "pdflatex"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except FileNotFoundError:
            pass
        
        # Check common installation paths
        common_paths = [
            r"C:\Program Files\MiKTeX\miktex\bin\x64",
            r"C:\Program Files (x86)\MiKTeX\miktex\bin",
            r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64".format(os.environ.get("USERNAME", ""))
        ]
        
        for path in common_paths:
            pdflatex_path = os.path.join(path, "pdflatex.exe")
            if os.path.exists(pdflatex_path):
                return pdflatex_path
    
    # On macOS, check common MacTeX installation paths
    elif platform.system() == "Darwin":
        common_paths = [
            "/Library/TeX/texbin/pdflatex",
            "/usr/local/texlive/bin/pdflatex"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    # On Linux, check common TeX Live installation paths
    elif platform.system() == "Linux":
        common_paths = [
            "/usr/bin/pdflatex",
            "/usr/local/bin/pdflatex"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    # If we get here, pdflatex was not found
    return None

def generate_latex_resume(user_data):
    """
    Generate a LaTeX resume based on user data.
    
    Args:
        user_data (dict): Dictionary containing user resume data
        
    Returns:
        str: Path to the generated PDF file, or None if generation failed
    """
    # Find pdflatex executable
    pdflatex_path = find_pdflatex()
    if not pdflatex_path:
        st.error("pdflatex not found. Please install LaTeX (TeX Live or MiKTeX) and make sure it's in your PATH.")
        st.info("You can run the install_dependencies.py script for installation instructions.")
        return None
    
    # Create LaTeX content
    latex_content = create_latex_content(user_data)
    
    # Create temporary directory for LaTeX files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write LaTeX content to file
        tex_file = os.path.join(temp_dir, "resume.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Compile LaTeX to PDF
        try:
            # Run pdflatex command
            compile_command = [pdflatex_path, "-interaction=nonstopmode", "-output-directory", temp_dir, tex_file]
            
            process = subprocess.run(
                compile_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if process.returncode != 0:
                st.error(f"Error compiling LaTeX: {process.stderr}")
                # Show more detailed error information
                log_file = os.path.join(temp_dir, "resume.log")
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        log_content = f.read()
                    st.error(f"LaTeX log file contains errors. Last few lines:\n{log_content[-500:]}")
                return None
            
            # Check if PDF was generated
            pdf_file = os.path.join(temp_dir, "resume.pdf")
            if not os.path.exists(pdf_file):
                st.error("PDF file was not generated.")
                return None
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated", "resumes")
            os.makedirs(output_dir, exist_ok=True)
            
            # Copy PDF to output directory
            output_file = os.path.join(output_dir, f"{user_data['email'].replace('@', '_').replace('.', '_')}_resume.pdf")
            with open(pdf_file, "rb") as src, open(output_file, "wb") as dst:
                dst.write(src.read())
            
            return output_file
        
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            return None

def create_latex_content(user_data):
    """
    Create LaTeX content for the resume.
    
    Args:
        user_data (dict): Dictionary containing user resume data
        
    Returns:
        str: LaTeX content
    """
    # Extract user data
    name = user_data.get("name", "")
    email = user_data.get("email", "")
    phone = user_data.get("phone", "")
    location = user_data.get("location", "")
    website = user_data.get("website", "")
    linkedin = user_data.get("linkedin", "")
    github = user_data.get("github", "")
    
    # Education
    education = user_data.get("education", [])
    
    # Experience
    experience = user_data.get("experience", [])
    
    # Projects
    projects = user_data.get("projects", [])
    
    # Skills
    skills = user_data.get("skills", {})
    
    # Create LaTeX content
    latex_content = r"""
\documentclass[10pt, letterpaper]{article}

% Packages:
\usepackage[
    ignoreheadfoot,
    top=2 cm,
    bottom=2 cm,
    left=2 cm,
    right=2 cm,
    footskip=1.0 cm,
]{geometry}
\usepackage{titlesec}
\usepackage{tabularx}
\usepackage{array}
\usepackage[dvipsnames]{xcolor}
\definecolor{primaryColor}{RGB}{0, 0, 0}
\usepackage{enumitem}
\usepackage{amsmath}
\usepackage[
    colorlinks=true,
    urlcolor=primaryColor
]{hyperref}
\usepackage{calc}
\usepackage{changepage}
\usepackage{paracol}
\usepackage{ifthen}
\usepackage{needspace}
\usepackage{iftex}

% Ensure that generate pdf is machine readable/ATS parsable:
\ifPDFTeX
    \input{glyphtounicode}
    \pdfgentounicode=1
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage{lmodern}
\fi

\usepackage{charter}

% Some settings:
\raggedright
\AtBeginEnvironment{adjustwidth}{\partopsep0pt}
\pagestyle{empty}
\setcounter{secnumdepth}{0}
\setlength{\parindent}{0pt}
\setlength{\topskip}{0pt}
\setlength{\columnsep}{0.15cm}
\pagenumbering{gobble}

\titleformat{\section}{\needspace{4\baselineskip}\bfseries\large}{}{0pt}{}[\vspace{1pt}\titlerule]

\titlespacing{\section}{
    -1pt
}{
    0.3 cm
}{
    0.2 cm
}

\renewcommand\labelitemi{$\vcenter{\hbox{\small$\bullet$}}$}
\newenvironment{highlights}{
    \begin{itemize}[
        topsep=0.10 cm,
        parsep=0.10 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=0 cm + 10pt
    ]
}{
    \end{itemize}
}

\newenvironment{highlightsforbulletentries}{
    \begin{itemize}[
        topsep=0.10 cm,
        parsep=0.10 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=10pt
    ]
}{
    \end{itemize}
}

\newenvironment{onecolentry}{
    \begin{adjustwidth}{
        0 cm + 0.00001 cm
    }{
        0 cm + 0.00001 cm
    }
}{
    \end{adjustwidth}
}

\newenvironment{twocolentry}[2][]{
    \onecolentry
    \def\secondColumn{#2}
    \setcolumnwidth{\fill, 4.5 cm}
    \begin{paracol}{2}
}{
    \switchcolumn \raggedleft \secondColumn
    \end{paracol}
    \endonecolentry
}

\newenvironment{header}{
    \setlength{\topsep}{0pt}\par\kern\topsep\centering\linespread{1.5}
}{
    \par\kern\topsep
}

\begin{document}
    \newcommand{\AND}{\unskip
        \cleaders\copy\ANDbox\hskip\wd\ANDbox
        \ignorespaces
    }
    \newsavebox\ANDbox
    \sbox\ANDbox{$|$}

    \begin{header}
        \fontsize{25 pt}{25 pt}\selectfont """ + name + r"""

        \vspace{5 pt}

        \normalsize
"""
    
    # Add contact information
    contact_items = []
    if location:
        contact_items.append(rf"\mbox{{{location}}}")
    if email:
        contact_items.append(rf"\mbox{{\href{{mailto:{email}}}{{{email}}}}}")
    if phone:
        contact_items.append(rf"\mbox{{\href{{tel:{phone}}}{{{phone}}}}}")
    if website:
        contact_items.append(rf"\mbox{{\href{{https://{website}}}{{{website}}}}}")
    if linkedin:
        contact_items.append(rf"\mbox{{\href{{https://linkedin.com/in/{linkedin}}}{{linkedin.com/in/{linkedin}}}}}")
    if github:
        contact_items.append(rf"\mbox{{\href{{https://github.com/{github}}}{{github.com/{github}}}}}")
    
    # Join contact items with separator
    if contact_items:
        latex_content += "        " + contact_items[0]
        for item in contact_items[1:]:
            latex_content += "%\n        \\kern 5.0 pt%\n        \\AND%\n        \\kern 5.0 pt%\n        " + item
    
    latex_content += r"""
    \end{header}

    \vspace{5 pt - 0.3 cm}
"""
    
    # Education section
    if education:
        latex_content += r"""
    \section{Education}
"""
        for edu in education:
            period = edu.get("period", "")
            institution = edu.get("institution", "")
            degree = edu.get("degree", "")
            gpa = edu.get("gpa", "")
            coursework = edu.get("coursework", "")
            
            latex_content += r"""
        \begin{twocolentry}{
            """ + period + r"""
        }
            \textbf{""" + institution + r"""}, """ + degree + r"""\end{twocolentry}
"""
            
            if gpa or coursework:
                latex_content += r"""
        \vspace{0.10 cm}
        \begin{onecolentry}
            \begin{highlights}
"""
                if gpa:
                    latex_content += r"""                \item GPA: """ + gpa + "\n"
                if coursework:
                    latex_content += r"""                \item \textbf{Coursework:} """ + coursework + "\n"
                
                latex_content += r"""            \end{highlights}
        \end{onecolentry}
"""
            
            latex_content += "\n"
    
    # Experience section
    if experience:
        latex_content += r"""
    \section{Experience}
"""
        for exp in experience:
            period = exp.get("period", "")
            title = exp.get("title", "")
            company = exp.get("company", "")
            location = exp.get("location", "")
            highlights = exp.get("highlights", [])
            
            latex_content += r"""
        \begin{twocolentry}{
            """ + period + r"""
        }
            \textbf{""" + title + r"""}, """ + company + (f" -- {location}" if location else "") + r"""\end{twocolentry}
"""
            
            if highlights:
                latex_content += r"""
        \vspace{0.10 cm}
        \begin{onecolentry}
            \begin{highlights}
"""
                for highlight in highlights:
                    latex_content += f"                \\item {highlight}\n"
                
                latex_content += r"""            \end{highlights}
        \end{onecolentry}
"""
            
            latex_content += "\n        \\vspace{0.2 cm}\n"
    
    # Projects section
    if projects:
        latex_content += r"""
    \section{Projects}
"""
        for project in projects:
            link = project.get("link", "")
            title = project.get("title", "")
            highlights = project.get("highlights", [])
            
            latex_content += r"""
        \begin{twocolentry}{
            """ + (f"\\href{{{link}}}{{{link.replace('https://', '')}}}" if link else "") + r"""
        }
            \textbf{""" + title + r"""}\end{twocolentry}
"""
            
            if highlights:
                latex_content += r"""
        \vspace{0.10 cm}
        \begin{onecolentry}
            \begin{highlights}
"""
                for highlight in highlights:
                    latex_content += f"                \\item {highlight}\n"
                
                latex_content += r"""            \end{highlights}
        \end{onecolentry}
"""
            
            latex_content += "\n        \\vspace{0.2 cm}\n"
    
    # Skills section
    if skills:
        latex_content += r"""
    \section{Skills}
"""
        for category, skill_list in skills.items():
            if skill_list:
                latex_content += r"""
        \begin{onecolentry}
            \textbf{""" + category + r""":} """ + ", ".join(skill_list) + r"""
        \end{onecolentry}

        \vspace{0.2 cm}
"""
    
    # End document
    latex_content += r"""
\end{document}
"""
    
    return latex_content

def resume_form():
    """
    Create a form for collecting resume data.
    
    Returns:
        dict: Dictionary containing user resume data
    """
    user_data = {
        "name": st.text_input("Full Name"),
        "email": st.text_input("Email"),
        "phone": st.text_input("Phone Number"),
        "location": st.text_input("Location"),
        "website": st.text_input("Website (optional)"),
        "linkedin": st.text_input("LinkedIn Username (optional)"),
        "github": st.text_input("GitHub Username (optional)"),
        "education": [],
        "experience": [],
        "projects": [],
        "skills": {}
    }
    
    # Education section
    st.subheader("Education")
    num_education = st.number_input("Number of Education Entries", min_value=0, max_value=5, value=1)
    
    for i in range(num_education):
        st.markdown(f"#### Education #{i+1}")
        education = {
            "period": st.text_input(f"Period (e.g., Sept 2020 - May 2024) #{i+1}"),
            "institution": st.text_input(f"Institution #{i+1}"),
            "degree": st.text_input(f"Degree #{i+1}"),
            "gpa": st.text_input(f"GPA (optional) #{i+1}"),
            "coursework": st.text_input(f"Relevant Coursework (optional) #{i+1}")
        }
        user_data["education"].append(education)
    
    # Experience section
    st.subheader("Experience")
    num_experience = st.number_input("Number of Experience Entries", min_value=0, max_value=5, value=1)
    
    for i in range(num_experience):
        st.markdown(f"#### Experience #{i+1}")
        experience = {
            "period": st.text_input(f"Period (e.g., June 2023 - Aug 2023) #{i+1}"),
            "title": st.text_input(f"Job Title #{i+1}"),
            "company": st.text_input(f"Company #{i+1}"),
            "location": st.text_input(f"Location (optional) #{i+1}"),
            "highlights": []
        }
        
        num_highlights = st.number_input(f"Number of Bullet Points for Experience #{i+1}", min_value=0, max_value=5, value=2)
        for j in range(num_highlights):
            highlight = st.text_input(f"Bullet Point #{j+1} for Experience #{i+1}")
            if highlight:
                experience["highlights"].append(highlight)
        
        user_data["experience"].append(experience)
    
    # Projects section
    st.subheader("Projects")
    num_projects = st.number_input("Number of Project Entries", min_value=0, max_value=5, value=1)
    
    for i in range(num_projects):
        st.markdown(f"#### Project #{i+1}")
        project = {
            "title": st.text_input(f"Project Title #{i+1}"),
            "link": st.text_input(f"Project Link (optional) #{i+1}"),
            "highlights": []
        }
        
        num_highlights = st.number_input(f"Number of Bullet Points for Project #{i+1}", min_value=0, max_value=5, value=2)
        for j in range(num_highlights):
            highlight = st.text_input(f"Bullet Point #{j+1} for Project #{i+1}")
            if highlight:
                project["highlights"].append(highlight)
        
        user_data["projects"].append(project)
    
    # Skills section
    st.subheader("Skills")
    num_skill_categories = st.number_input("Number of Skill Categories", min_value=0, max_value=5, value=1)
    
    for i in range(num_skill_categories):
        category = st.text_input(f"Skill Category #{i+1} (e.g., Languages, Technologies)")
        if category:
            skills = st.text_input(f"Skills for {category} (comma-separated)")
            if skills:
                user_data["skills"][category] = [skill.strip() for skill in skills.split(",")]
    
    return user_data 