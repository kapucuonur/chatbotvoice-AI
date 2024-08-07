# auth/__init__.py
from .facebook_auth import facebook_blueprint
from .email_auth import email_blueprint
from .google_auth import google_blueprint # Import the new Google blueprint

# Collect all authentication blueprints here
all_blueprints = [
    facebook_blueprint,
    email_blueprint,
    google_blueprint, # Add Google blueprint here
]
