# auth/email_auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

# Create an email authentication blueprint
email_blueprint = Blueprint('email_auth', __name__, template_folder='templates')

@email_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """Manages the user registration page and its functionality."""
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists_email = User.query.filter_by(email=email).first()
        user_exists_username = User.query.filter_by(username=username).first()

        if user_exists_email:
            flash('This email address is already registered.', 'warning')
            return redirect(url_for('email_auth.register'))
        if user_exists_username:
            flash('This username is already taken.', 'warning')
            return redirect(url_for('email_auth.register'))

        if not username or not email or not password:
            flash('All fields are required.', 'warning')
            return redirect(url_for('email_auth.register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password) # Hash and save the password
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been successfully created! You can now log in.', 'success')
        return redirect(url_for('email_auth.login'))

    return render_template('login.html') # You can use login.html for the registration form too


@email_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Manages the user login page and its functionality."""
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username')
        password = request.form.get('password')
        remember_me = True if request.form.get('remember_me') else False

        # Try to find user by email or username
        user = User.query.filter((User.email == email_or_username) | (User.username == email_or_username)).first()

        if not user or not user.check_password(password):
            flash('Invalid email/username or password.', 'error')
            return redirect(url_for('email_auth.login'))

        login_user(user, remember=remember_me)
        flash('Successfully logged in!', 'success')
        # Redirect to the original page the user intended to go to, or to the profile page
        next_page = request.args.get('next')
        return redirect(next_page or url_for('profile'))

    return render_template('login.html')

@email_blueprint.route('/logout')
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home')) # Assuming 'home' route is defined in the main app.py
