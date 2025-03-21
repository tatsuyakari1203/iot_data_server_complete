import os
from flask import flash, redirect, url_for, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get admin credentials from .env file
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

# Simple user class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':  # We only have one admin user
        return User(1, ADMIN_USERNAME)
    return None

# Set up login manager
def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'warning'

# Verify user credentials
def verify_credentials(username, password):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True
    return False
