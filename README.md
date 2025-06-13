# DevChatbot-AI: Voice & Text Chatbot System

## Screenshots

Here's a glimpse of the DevChatbot-AI in action:

**Main Chat Interface**
![DevChatbot-AI Ana Ekranı](static/img/screenshot.png) <!-- Ensure screenshot.png is in static/img/ -->

![DevChatbot-AI Logo](static/img/logo.png) <!-- Ensure you have a logo.png in static/img/ -->

DevChatbot-AI is a comprehensive Flask-based web application that provides an interactive chatbot experience with both text and voice input/output capabilities. It integrates with Groq for advanced AI responses and includes a robust user authentication system with email/password, Facebook, and Google login options. Unauthenticated users have a limited number of queries before being prompted to register.

---

## Features

- **Text & Voice Interaction:** Users can communicate with the chatbot via typing or speaking.
- **Speech-to-Text (STT):** Utilizes the Web Speech API for transcribing user voice input.
- **Text-to-Speech (TTS):** Bot responses are spoken aloud using the Web Speech API.
- **Voice Control:** Pause and resume voice output during bot responses.
- **AI Integration (Groq):** Leverages the Groq API for intelligent and dynamic chatbot responses.
- **Intent-Based Responses:** Includes pre-defined intents for common queries (e.g., greetings, programming topics).
- **User Authentication:**
  - Email and Password registration/login.
  - OAuth integration for seamless login with **Facebook** and **Google**.
- **Query Limiting for Guests:** Unauthenticated users are limited to 10 queries.
- **Database Management:** Uses Flask-SQLAlchemy with SQLite (for development) and Flask-Migrate for schema evolution.
- **Responsive Design:** Built with Tailwind CSS for a modern and adaptive user interface.
- **Flash Messaging:** Provides user feedback messages (success, error, warning).

---

## Installation

Follow these steps to set up and run the project locally.

### Prerequisites

- Python 3.9+
- `pip` (Python package installer)
- `venv` (Python virtual environment)

### 1. Clone the Repository

```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME
```

(Replace `YOUR_GITHUB_USERNAME` and `YOUR_REPOSITORY_NAME` with your actual GitHub details.)

### 2. Set up Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### 3. Install Dependencies

Install all required Python packages using pip.

```bash
pip install -r requirements.txt
# If you don't have requirements.txt, you can install them manually:
# pip install Flask Flask-SQLAlchemy Flask-Login Flask-Dance Werkzeug python-dotenv groq Flask-Migrate gunicorn
# pip install Flask-Dance[facebook,google] # For OAuth dependencies
# pip install psycopg2-binary # If using PostgreSQL
```

### 4. Environment Variables

Create a `.env` file in the root of your project and add the following environment variables. **Do NOT commit this file to Git!**

```ini
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
SECRET_KEY=YOUR_FLASK_SECRET_KEY_HERE # Generate a strong random key (e.g., import os; os.urandom(24))
GOOGLE_OAUTH_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE
GOOGLE_OAUTH_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET_HERE
# For local development:
GOOGLE_OAUTH_REDIRECT_URI=[http://127.0.0.1:5001/auth/google/callback](http://127.0.0.1:5001/auth/google/callback)

FACEBOOK_OAUTH_CLIENT_ID=YOUR_FACEBOOK_CLIENT_ID_HERE
FACEBOOK_OAUTH_CLIENT_SECRET=YOUR_FACEBOOK_CLIENT_SECRET_HERE
# For local development:
FACEBOOK_OAUTH_REDIRECT_URI=[http://127.0.0.1:5001/auth/facebook/callback](http://127.0.0.1:5001/auth/facebook/callback)

SQLALCHEMY_DATABASE_URI=sqlite:///users.db # Or your PostgreSQL connection string for production
```

### 5. Database Migrations

Set up and apply database migrations to create the necessary tables and columns.

```bash
export FLASK_APP=app.py # On macOS/Linux
# set FLASK_APP=app.py # On Windows

flask db init            # Initialize the migrations folder (run once)
flask db migrate -m "Initial migration with user, facebook_id, google_id" # Generate a migration script
# IMPORTANT: If you get a "Constraint must have a name" error during 'migrate' or 'upgrade',
# manually open the generated migration file in 'migrations/versions/' and change:
# batch_op.create_unique_constraint(None, ['google_id'])
# to:
# batch_op.create_unique_constraint("uq_user_google_id", ['google_id'])
# Then save the file.

flask db upgrade         # Apply the migrations to your database
```

### 6. Prepare `intents.json`

Ensure you have a `data/intents.json` file in your project root with your chatbot's conversational intents. A basic structure looks like this:

```json
{
  "intents": [
    {
      "tag": "greeting",
      "patterns": ["hi", "hello", "hey"],
      "responses": ["Hello!", "Hi there!"]
    },
    {
      "tag": "goodbye",
      "patterns": ["bye", "see you later"],
      "responses": ["Goodbye!", "See you soon!"]
    }
  ]
}
```

---

## Running the Application

### Development Server (for local testing)

```bash
python3 app.py
```

The application will be accessible at `http://127.0.0.1:5001`.

### Production Server (using Gunicorn)

For production deployments, use a WSGI server like Gunicorn.

```bash
gunicorn --workers 1 app:app
```

(Using `--workers 1` helps troubleshoot if you encounter issues with multiple workers. You can increase this for production.)
The application will typically be accessible at `http://127.0.0.1:8000` (Gunicorn's default port).

---

## Deployment to Render.com

1.  **Commit to GitHub:** Ensure your project (excluding `.env` and `.db` files, which should be in `.gitignore`) is pushed to a GitHub repository.
2.  **Create Web Service on Render:**
    - Go to [Render.com](https://render.com/) and create a new Web Service.
    - Connect your GitHub repository.
    - **Build Command:** `pip install -r requirements.txt`
    - **Start Command:** `gunicorn app:app`
    - **Environment Variables:** Add all variables from your `.env` file to Render's environment settings.
    - **Update Redirect URIs:** Crucially, update your Google and Facebook OAuth client configurations (in their respective developer consoles) to include your Render.com application's URL for the redirect URIs (e.g., `https://your-app-name.onrender.com/auth/google/callback`).
    - **Database (PostgreSQL recommended):** For persistent data on Render, create a PostgreSQL database on Render and update `SQLALCHEMY_DATABASE_URI` to use its connection string. You'll need to install `psycopg2-binary` and potentially use Flask-Migrate to transfer your schema.
    ### Live Link https://chatbotvoice-ai.onrender.com/

---

## Project Structure

```
ChatbotVoice-AI/
├── app.py                     # Main Flask application
├── models.py                  # Database models (User etc.)
├── requirements.txt           # Python dependencies list
├── .env                       # Environment variables (Sensitive keys) - NOT pushed to GitHub!
├── .gitignore                 # Files/folders for Git to ignore
├── Procfile                   # (Optional) Command for starting app on platforms like Render
├── data/                      # Folder for JSON files
│   └── intents.json           # Chatbot intents and responses
├── auth/                      # Authentication blueprints folder
│   ├── __init__.py            # Collects blueprints
│   ├── email_auth.py          # Email/password authentication
│   ├── facebook_auth.py       # Facebook OAuth
│   └── google_auth.py         # Google OAuth
├── templates/                 # HTML templates folder
│   ├── index.html             # Main chat page
│   ├── login.html             # Combined Login/Register page
│   ├── profile.html           # User profile page
│   ├── data_deletion_instructions.html # Data deletion instructions
│   └── data_deletion_status.html # Data deletion status
└── static/                    # Static files (CSS, JS, images) folder
    ├── js/                    # JavaScript files
    │   └── chatbot.js         # Chatbot's JavaScript logic
    └── img/                   # Images folder
        └── logo.png           # Application logo
```

---

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

---

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if you have one, otherwise specify your chosen license).
