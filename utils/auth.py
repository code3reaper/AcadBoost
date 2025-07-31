import json
import os
import hashlib
import streamlit as st
from datetime import datetime, timedelta

# File paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_users():
    """Initialize default users if they don't exist."""
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin@college.edu": {
                "password": hash_password("admin123"),
                "role": "admin",
                "name": "Admin User",
                "created_at": datetime.now().isoformat()
            },
            "teacher@college.edu": {
                "password": hash_password("teacher123"),
                "role": "teacher",
                "name": "Demo Teacher",
                "department": "Computer Science",
                "created_at": datetime.now().isoformat()
            },
            "student@college.edu": {
                "password": hash_password("student123"),
                "role": "student",
                "name": "Demo Student",
                "student_id": "S12345",
                "department": "Computer Science",
                "year": 2,
                "created_at": datetime.now().isoformat()
            }
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=4)

def get_users():
    """Get all users from the database."""
    if not os.path.exists(USERS_FILE):
        init_users()
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users to the database."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def authenticate(email, password):
    """Authenticate a user."""
    users = get_users()
    if email in users and users[email]["password"] == hash_password(password):
        return users[email]
    return None

def is_authenticated():
    """Check if a user is authenticated."""
    return "user" in st.session_state and st.session_state.user is not None

def login_required(func):
    """Decorator to require login for a page."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("Please login to access this page.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def role_required(roles):
    """Decorator to require specific role(s) for a page."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                st.warning("Please login to access this page.")
                st.stop()
            
            if st.session_state.user["role"] not in roles:
                st.error("You don't have permission to access this page.")
                st.stop()
                
            return func(*args, **kwargs)
        return wrapper
    return decorator

def logout():
    """Log out the current user."""
    if "user" in st.session_state:
        del st.session_state.user
    if "authentication_status" in st.session_state:
        del st.session_state.authentication_status

def create_user(email, password, role, **kwargs):
    """Create a new user."""
    users = get_users()
    
    if email in users:
        return False, "Email already exists"
    
    users[email] = {
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
        **kwargs
    }
    
    save_users(users)
    return True, "User created successfully"

def get_user_by_email(email):
    """Get a user by email."""
    users = get_users()
    return users.get(email, None)

def update_user(email, **kwargs):
    """Update a user's information."""
    users = get_users()
    
    if email not in users:
        return False, "User not found"
    
    # Don't update password if not provided
    if "password" in kwargs and kwargs["password"]:
        kwargs["password"] = hash_password(kwargs["password"])
    else:
        kwargs.pop("password", None)
    
    users[email].update(kwargs)
    save_users(users)
    
    # Update session state if the current user is being updated
    if is_authenticated() and st.session_state.user.get("email") == email:
        st.session_state.user = users[email]
        
    return True, "User updated successfully"

def delete_user(email):
    """Delete a user."""
    users = get_users()
    
    if email not in users:
        return False, "User not found"
    
    del users[email]
    save_users(users)
    return True, "User deleted successfully"

def get_current_user():
    """
    Get the currently logged-in user from the session state.
    
    Returns:
        dict: The current user's data or None if not logged in
    """
    if is_authenticated():
        return st.session_state.user
    return None

def get_user_data(email):
    """
    Get a user's data by email, excluding sensitive information like password.
    
    Args:
        email (str): The user's email
        
    Returns:
        dict: The user's data without sensitive fields or None if not found
    """
    user = get_user_by_email(email)
    if user:
        # Create a copy of the user data without the password
        user_data = user.copy()
        user_data.pop("password", None)
        return user_data
    return None

# Initialize default users
init_users() 