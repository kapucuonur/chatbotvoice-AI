from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
# Importing password hashing functions from Werkzeug.security
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    User database model.
    Inherits UserMixin from Flask-Login to gain session management capabilities.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True) # Field for password hash
    facebook_id = db.Column(db.String(120), unique=True, nullable=True) # Facebook ID
    google_id = db.Column(db.String(120), unique=True, nullable=True) # Google ID - Added for Google OAuth
    avatar = db.Column(db.String(255), nullable=True) # Profile picture URL

    def __repr__(self):
        return f'<User {self.username}>'

    # Method to set (hash) the password
    # Explicitly using 'pbkdf2:sha256' as the hashing method to avoid 'scrypt' issues
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    # Method to check the password
    def check_password(self, password):
        # Ensure password_hash is not None before attempting to check
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)