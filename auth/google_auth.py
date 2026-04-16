# auth/google_auth.py
import os
from flask import Blueprint, redirect, url_for, flash, request, jsonify, current_app
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user

# Importing User and db from models.py
from models import User, db

# Create the Google Blueprint
# Ensure GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET are set in your .env
google_blueprint = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],  # Request basic user info
    redirect_to="google.google_callback", # Explicit callback route within this blueprint
)

@google_blueprint.route("/google_login")
def google_login():
    """
    Initiates the Google OAuth login process.
    Redirects to Google's authorization page if the user is not authenticated.
    """
    if not current_user.is_authenticated:
        # This redirects to the Google authorization URL provided by Flask-Dance
        return redirect(url_for("google.login"))
    return redirect(url_for("profile")) # Redirect to user profile if already logged in


@google_blueprint.route("/auth/google_callback")
def google_callback():
    """
    Handles the authorization callback from Google.
    Exchanges the authorization code for an access token and retrieves user information.
    """
    if not google.authorized:
        flash("Google authorization failed. Please try again.", "error")
        return redirect(url_for("email_auth.login")) # Redirect to your app's general login page

    try:
        # Get user info from Google's OpenID Connect UserInfo endpoint
        # The 'google' object from Flask-Dance is an OAuthSession object
        resp = google.get("/oauth2/v2/userinfo")

        if not resp.ok:
            flash("Failed to retrieve user data from Google.", "error")
            current_app.logger.error(f"Google API error: {resp.status_code} - {resp.text}")
            return redirect(url_for("email_auth.login"))

        user_info = resp.json()
        
        # Validate that required fields were received from Google
        if not all(k in user_info for k in ['id', 'email']):
            flash("Incomplete data received from Google.", "error")
            current_app.logger.error(f"Incomplete Google user data: {user_info}")
            return redirect(url_for("email_auth.login"))

        # Find or create the user in your database
        user = User.query.filter_by(google_id=user_info['id']).first()
        if not user:
            # Check if user with this email already exists
            user_by_email = User.query.filter_by(email=user_info['email']).first() if 'email' in user_info else None
            if user_by_email:
                user_by_email.google_id = user_info['id']
                user_by_email.avatar = user_info.get('picture', user_by_email.avatar)
                user = user_by_email
                db.session.commit()
            else:
                base_username = user_info.get('name', user_info['email'].split('@')[0])
                unique_username = base_username
                counter = 1
                while User.query.filter_by(username=unique_username).first():
                    unique_username = f"{base_username}{counter}"
                    counter += 1
                    
                user = User(
                    email=user_info['email'],
                    username=unique_username,
                    google_id=user_info['id'],
                    avatar=user_info.get('picture')
                )
                user.password_hash = None
                
                db.session.add(user)
                db.session.commit()
        else:
            # Update existing user details (DO NOT blindly update username if it can throw IntegrityError)
            user.avatar = user_info.get('picture', user.avatar) 
            db.session.commit()

        # Log the user in with Flask-Login
        login_user(user)
        flash("Successfully logged in with Google!", "success")
        return redirect(url_for("profile")) # Redirect to a protected user profile page

    except Exception as e:
        current_app.logger.error(f"Google authentication callback error: {str(e)}", exc_info=True)
        flash("An error occurred during authentication. Please try again.", "error")
        return redirect(url_for("email_auth.login"))
