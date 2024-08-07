# auth/facebook_auth.py
import base64
import hmac
import hashlib
import json
import os
from flask import Blueprint, redirect, url_for, session, flash, request, jsonify, current_app, render_template
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_login import login_user, current_user, logout_user, login_required

# Importing User and db from models.py
from models import User, db

# Create the Facebook Blueprint
facebook_blueprint = make_facebook_blueprint(
    client_id=os.getenv("FACEBOOK_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET"),
    scope=["email", "public_profile"],  # Request email and basic profile info
    redirect_url=os.getenv("FACEBOOK_OAUTH_REDIRECT_URI"),
    redirect_to="auth.facebook_callback",  # Explicit callback route
)

# Define routes specific to this blueprint
@facebook_blueprint.route("/facebook_login")
def facebook_login():
    """
    Initiates the Facebook OAuth login process.
    Redirects to Facebook's authorization page if the user is not authenticated.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("facebook.login")) # This is Flask-Dance's internal route
    return redirect(url_for("profile")) # Redirect to user profile if already logged in


@facebook_blueprint.route("/auth/facebook_callback")
def facebook_callback():
    """
    Handles the authorization callback from Facebook.
    Exchanges the authorization code for an access token and retrieves user information.
    """
    if not facebook.authorized:
        flash("Facebook authorization failed.", "error")
        return redirect(url_for("email_auth.login")) # Redirect to your app's general login page


    try:
        # Get user info with error handling
        resp = facebook.get("/me?fields=id,name,email,picture.type(large)")
        if not resp.ok:
            flash("Failed to retrieve user data from Facebook.", "error")
            current_app.logger.error(f"Facebook API error: {resp.status_code} - {resp.text}")
            return redirect(url_for("email_auth.login"))

        user_info = resp.json()
        
        # Validate that required fields were received from Facebook
        if not all(k in user_info for k in ['id', 'name', 'email']):
            flash("Incomplete data received from Facebook.", "error")
            current_app.logger.error(f"Incomplete Facebook user data: {user_info}")
            return redirect(url_for("email_auth.login"))

        # Find or create the user in your database
        user = User.query.filter_by(facebook_id=user_info['id']).first()
        if not user:
            # For users logging in with Facebook, set a default password hash
            # (You can leave this field empty or add more complex logic if needed)
            user = User(
                email=user_info['email'],
                username=user_info['name'],
                facebook_id=user_info['id'],
                avatar=user_info.get('picture', {}).get('data', {}).get('url')
            )
            # If `password_hash` is nullable=False, you must assign a value.
            # user.set_password(str(os.urandom(16))) # A random password hash
            user.password_hash = None # We can leave it null if nullable
            
            db.session.add(user)
            db.session.commit()
        else:
            # Update existing user details if necessary
            user.email = user_info['email']
            user.username = user_info['name']
            user.avatar = user_info.get('picture', {}).get('data', {}).get('url')
            db.session.commit()

        # Log the user in with Flask-Login
        login_user(user)
        flash("Successfully logged in with Facebook!", "success")
        return redirect(url_for("profile")) # Redirect to a protected user profile page

    except Exception as e:
        current_app.logger.error(f"Facebook authentication callback error: {str(e)}", exc_info=True)
        flash("An error occurred during authentication. Please try again.", "error")
        return redirect(url_for("email_auth.login"))


# --- Data Deletion Features ---

def parse_signed_request(signed_request, app_secret):
    """
    Parses and verifies a Facebook signed_request.
    Returns the decoded data if valid, otherwise None.
    """
    try:
        encoded_sig, payload = signed_request.split('.', 1)

        # Decode the data
        sig = base64.urlsafe_b64decode(encoded_sig + "==")
        data = base64.urlsafe_b64decode(payload + "==").decode('utf-8')
        data = json.loads(data)

        # Check algorithm and signature
        if data.get('algorithm') == 'HMAC-SHA256':
            h = hmac.new(app_secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256)
            if h.digest() == sig:
                return data
        return None
    except Exception as e:
        current_app.logger.error(f"Error parsing signed request: {e}")
        return None


@facebook_blueprint.route('/auth/facebook/data-deletion-callback', methods=['POST'])
def facebook_data_deletion_callback():
    """
    Handles POST requests from Facebook when a user removes your app from their Facebook settings.
    This endpoint will receive a signed_request containing the Facebook user ID.
    Your application should then delete the corresponding user data.
    """
    try:
        signed_request = request.form.get('signed_request')
        if not signed_request:
            current_app.logger.warning("Facebook data deletion callback: Missing signed_request")
            return jsonify({"status": "error", "message": "Missing signed_request"}), 400

        app_secret = current_app.config['FACEBOOK_OAUTH_CLIENT_SECRET']
        data = parse_signed_request(signed_request, app_secret)

        if not data:
            current_app.logger.error("Facebook data deletion callback: Invalid signed_request")
            return jsonify({"status": "error", "message": "Invalid signed_request"}), 403

        user_facebook_id = data.get('user_id')
        if not user_facebook_id:
            current_app.logger.warning("Facebook data deletion callback: User ID not found in signed request")
            return jsonify({"status": "error", "message": "User ID not found in signed request"}), 400

        # Find the user in your database using their Facebook ID
        user_to_delete = User.query.filter_by(facebook_id=user_facebook_id).first()

        if user_to_delete:
            # --- IMPLEMENT YOUR DATA DELETION LOGIC HERE ---
            # This is the critical part: Delete the user and all associated data.
            # Example: Delete the User object from the database
            db.session.delete(user_to_delete)
            db.session.commit()
            current_app.logger.info(f"Successfully processed data deletion for Facebook ID: {user_facebook_id}.")

            # For real applications, you might also need to delete:
            # - User-generated content (e.g., chat messages, posts)
            # - User preferences, settings
            # - Any other PII (Personally Identifiable Information) linked to this user.
            # Consider if you need to perform soft deletes (marking as deleted) or full hard deletes.

            # Facebook expects a JSON response including a confirmation URL
            # and a confirmation_code. The confirmation code is something you generate
            # to allow the user to check the status of their deletion request.
            # For this example, we'll use a placeholder. In a real app, you'd store
            # this code and link it to the deletion event.
            response_data = {
                "url": url_for('data_deletion_status', _external=True), # A URL for users to check deletion status
                "confirmation_code": f"DEVCHAT_DEL_{user_facebook_id[:8]}_{os.urandom(4).hex()}" # A unique code
            }
            return jsonify(response_data), 200
        else:
            current_app.logger.warning(f"Facebook data deletion callback: User with Facebook ID {user_facebook_id} not found in DB.")
            # Even if user not found, acknowledge to Facebook that you've processed the request.
            # This prevents Facebook from repeatedly sending the request.
            return jsonify({
                "url": url_for('data_deletion_status', _external=True),
                "confirmation_code": "NOT_FOUND" # Or a similar indicator
            }), 200

    except Exception as e:
        current_app.logger.error(f"Facebook data deletion callback error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error during data deletion callback"}), 500
