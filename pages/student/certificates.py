import streamlit as st
from datetime import datetime
import os

from utils.auth import role_required
from utils.ui import (
    show_header, show_notification, show_data_table,
    format_date, format_datetime
)
from utils.database import (
    get_certificates, submit_certificate, verify_certificate
)

@role_required(["student"])
def show_certificates():
    """Show the certificates page for students."""
    user = st.session_state.user
    email = st.session_state.email
    
    show_header("My Certificates", "Submit and manage your certificates")
    
    # Create tabs for different certificate views
    tab1, tab2 = st.tabs(["My Certificates", "Submit Certificate"])
    
    with tab1:
        show_my_certificates(email)
    
    with tab2:
        show_submit_certificate_form(email)

def show_my_certificates(email):
    """Show certificates for the student."""
    st.markdown("### My Certificates")
    
    # Get student's certificates
    all_certificates = get_certificates()
    
    # Get certificates for this student
    student_certificates = all_certificates.get(email, [])
    
    if not student_certificates:
        st.info("You have not submitted any certificates yet.")
        return
    
    # Prepare data for table
    certificate_data = []
    
    for certificate in student_certificates:
        certificate_data.append({
            "Certificate ID": certificate.get("certificate_id", ""),
            "Title": certificate.get("title", "No Title"),
            "Issuing Organization": certificate.get("issuing_organization", ""),
            "Issue Date": format_date(certificate.get("issue_date", "")),
            "Verification Status": "Verified" if certificate.get("verified", False) else "Pending",
            "Submission Date": format_datetime(certificate.get("submitted_at", ""))
        })
    
    # Show certificates table
    show_data_table(certificate_data)
    
    # Show verification buttons
    st.markdown("### Certificate Verification")
    st.markdown("Request verification for your certificates:")
    
    for certificate in student_certificates:
        if not certificate.get("verified", False):
            certificate_id = certificate.get("certificate_id", "")
            title = certificate.get("title", "No Title")
            
            if st.button(f"Request Verification for {title}", key=f"verify_{certificate_id}"):
                success, message = verify_certificate(email, certificate_id)
                
                if success:
                    show_notification("Certificate verification requested successfully.", "success")
                else:
                    show_notification(f"Error: {message}", "error")
    
    # Show download buttons
    st.markdown("Download your certificate files:")
    
    for certificate in student_certificates:
        file_path = certificate.get("file_path")
        title = certificate.get("title", "No Title")
        
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"Download {title}",
                    data=file,
                    file_name=os.path.basename(file_path),
                    mime="application/pdf"
                )

def show_submit_certificate_form(email):
    """Show form for submitting a new certificate."""
    st.markdown("### Submit New Certificate")
    
    with st.form("submit_certificate_form"):
        title = st.text_input("Certificate Title")
        issuing_organization = st.text_input("Issuing Organization")
        issue_date = st.date_input("Issue Date")
        
        # File upload
        uploaded_file = st.file_uploader("Upload Certificate (PDF)", type=["pdf"])
        
        submit_button = st.form_submit_button("Submit Certificate")
        
        if submit_button:
            if not title:
                show_notification("Certificate title is required.", "error")
            elif not issuing_organization:
                show_notification("Issuing organization is required.", "error")
            else:
                # Save file if uploaded
                file_path = None
                if uploaded_file:
                    # Create directory if it doesn't exist
                    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "certificates")
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(upload_dir, f"{email}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}")
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                # Submit certificate
                success, message = submit_certificate(
                    email,
                    title,
                    issuing_organization,
                    issue_date.strftime("%Y-%m-%d"),
                    file_path
                )
                
                if success:
                    show_notification("Certificate submitted successfully.", "success")
                    st.rerun()
                else:
                    show_notification(f"Error: {message}", "error") 