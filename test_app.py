# test_app.py (temproary Flask app for testing Gunicorn)
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, Gunicorn!'

if __name__ == '__main__':
    app.run(debug=True)