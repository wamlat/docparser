from flask import Flask
from flask_cors import CORS
import os

# Try to load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    # Look for .env file in the backend directory (one level up from app)
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(dotenv_path):
        print(f"Loading environment variables from {dotenv_path}")
        load_dotenv(dotenv_path)
    else:
        print("No .env file found, using system environment variables")
except ImportError:
    print("python-dotenv not installed, using system environment variables")

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})  # Enhanced CORS settings

from app import routes 