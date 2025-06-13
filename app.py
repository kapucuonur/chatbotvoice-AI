from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_migrate import Migrate # Import Flask-Migrate
from models import db, User # Import db and User from models.py
from auth import all_blueprints # Import blueprints from the auth folder
import os
import re
import json
import random
from groq import Groq
from dotenv import load_dotenv

app = Flask(__name__)
# Secret key is crucial for session security
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
load_dotenv() # Loads environment variables from .env file

# Groq API settings
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("WARNING: GROQ_API_KEY environment variable is not set. Groq API features might be unavailable.")
    groq_client = None # Set client to None if API key is missing
else:
    groq_client = Groq(api_key=groq_api_key)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suppresses unnecessary warnings
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db) # Initialize Flask-Migrate with your app and db object

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'email_auth.login' # Page to redirect to if user is not logged in (from email_auth blueprint)

# User loading function (for Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register all OAuth blueprints (like Facebook and Google)
for blueprint in all_blueprints:
    app.register_blueprint(blueprint)

# Create database tables (within application context)
# This part creates tables only if run for the first time.
# If you are using Flask-Migrate, you typically use migrate commands instead of db.create_all().
with app.app_context():
    # You can use db.create_all() for initial setup or if you need to create tables.
    # However, once you start using migrations, it's safer to comment out this line.
    # db.create_all()
    pass


# Load intents.json file
def load_intents():
    """Loads the intents.json file and handles potential errors."""
    try:
        with open('data/intents.json', 'r', encoding='utf-8') as file:
            data = file.read()
            if data.strip().startswith("<!DOCTYPE html>"):
                raise ValueError("Error: An HTML page is being loaded instead of intents.json!")
            return json.loads(data)
    except FileNotFoundError:
        print("Error: intents.json file not found. Please ensure it is in the 'data' folder.")
        return {"intents": []}
    except json.JSONDecodeError:
        print("Error: intents.json is not in a valid JSON format. Check its format.")
        return {"intents": []}

def get_random_response(intent):
    """
    Returns a random response for specific intents, or a fixed one for others.
    """
    if intent["tag"] in ["coding_tips", "junior_developer", "ai", "development", "programming_languages"]:
        return intent["responses"][0]
    if intent["tag"] in ["greeting", "how_are_you", "user_name"]:
        return random.choice(intent["responses"])
    return intent["responses"][0]

def extract_name(user_input):
    """Attempts to extract a name from the user input."""
    match = re.search(r"(?:my name is|i am|i'm|called|call me)\s+(\w+)", user_input, re.IGNORECASE)
    return match.group(1) if match else None

def get_response_from_intents(user_input):
    """Attempts to find a response based on user input within intents.json."""
    intents = load_intents()
    if not intents["intents"]:
        return None # Proceed to Groq if intents cannot be loaded

    for intent in intents["intents"]:
        # Check if user input matches any of the patterns
        if any(re.search(pattern.lower(), user_input.lower()) for pattern in intent["patterns"]):
            return get_random_response(intent) # Apply random/fixed logic with get_random_response

    return None # If not found in intents.json, proceed to Groq API

# Main function to handle user input
def handle_user_input(user_input):
    """Handles user input, responding using intents.json or the Groq API."""
    user_name = session.get('user_name')

    # Check and save user name
    if not user_name:
        extracted_name = extract_name(user_input)
        if extracted_name:
            session['user_name'] = extracted_name
            user_name = extracted_name

    # Try to find a response in intents.json
    response_text = get_response_from_intents(user_input)
    if not response_text: # If not found in intents, use Groq
        if groq_client:
            try:
                groq_response = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": user_input}],
                    model="llama-3.3-70b-versatile",
                )
                response_text = groq_response.choices[0].message.content.strip()
            except Exception as e:
                app.logger.error(f"Groq API error: {e}")
                response_text = "Sorry, I am unable to process your request at the moment. Please try again later."
        else:
            response_text = "Sorry, the AI service is currently unavailable. Please try again later."

    if user_name: # Replace [name] placeholder with actual user name
        response_text = response_text.replace("[name]", user_name)

    return response_text # Return only the text response

# --- Routes ---

@app.route('/')
def home():
    """Renders the home page and initializes/checks query count for unauthenticated users."""
    if not current_user.is_authenticated:
        if 'query_count' not in session:
            session['query_count'] = 0
        
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Processes the chat message from the user, returns a text response, and controls the limit for unauthenticated users.
    """
    if not current_user.is_authenticated:
        session['query_count'] = session.get('query_count', 0) + 1
        if session['query_count'] > 10: # Limit 10 queries
            return jsonify({
                "response": "Sorry, you have exceeded the 10-query limit for unauthenticated users. Please register or log in.",
                "limit_reached": True
            }), 403 # Forbidden

    try:
        user_input = request.json['message']
    except KeyError:
        return jsonify({"response": "Please provide a valid 'message' key in your request."}), 400

    text_response = handle_user_input(user_input)
    
    return jsonify({
        "response": text_response
    })

@app.route('/start', methods=['GET'])
def start():
    """Returns the bot's welcome message when the application starts."""
    welcome_message = "Hello! Welcome to DevChatbot-AI. I'm here to help you with development, programming, and AI. Press the microphone button to start talking!"
    return jsonify({
        "response": welcome_message
    })

@app.route('/profile')
@login_required # Only authenticated users can access
def profile():
    """Renders the user profile page."""
    return render_template('profile.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    """Logs out the user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/data-deletion-instructions')
def data_deletion_instructions():
    """Renders the data deletion instructions page."""
    return render_template('data_deletion_instructions.html')

@app.route('/data-deletion-status')
def data_deletion_status():
    """Renders the data deletion status page."""
    return render_template('data_deletion_status.html')


if __name__ == '__main__':
    # For testing SSL/TLS:
    # context = ('path/to/your/certificate.crt', 'path/to/your/private.key')
    # app.run(host='0.0.0.0', port=5001, debug=True, ssl_context=context)
    app.run(host='0.0.0.0', port=5001, debug=True)
