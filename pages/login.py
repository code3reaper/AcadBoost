import streamlit as st
from utils.auth import authenticate
from utils.ui import show_header, show_login_form, show_notification

def show_login_page():
    """Show the login page."""
    show_header("Welcome to College Management System", "Please login to continue")
    
    # Create columns for layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                <h2 style='text-align: center;'>Login</h2>
            """, 
            unsafe_allow_html=True
        )
        
        # Login form
        email, password = show_login_form()
        
        if email and password:
            user = authenticate(email, password)
            
            if user:
                # Store user in session state
                st.session_state.user = user
                st.session_state.email = email
                st.session_state.page = "dashboard"
                
                # Show success message
                show_notification(f"Welcome, {user.get('name', 'User')}!", "success")
                
                # Rerun to update UI
                st.rerun()
            else:
                show_notification("Invalid email or password. Please try again.", "error")
        
        st.markdown(
            """
            <div style='text-align: center; margin-top: 20px;'>
                <p>Default login credentials:</p>
                <ul style='list-style-type: none; padding: 0;'>
                    <li><strong>Admin:</strong> admin@college.edu / admin123</li>
                    <li><strong>Teacher:</strong> teacher@college.edu / teacher123</li>
                    <li><strong>Student:</strong> student@college.edu / student123</li>
                </ul>
            </div>
            </div>
            """, 
            unsafe_allow_html=True
        ) 