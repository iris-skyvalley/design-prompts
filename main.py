# Railway entry point - imports from backend/main.py
import sys
import os

# Add the backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.insert(0, backend_dir)

# Import the FastAPI app from backend/main.py
from main import app

# Make sure the app is available for gunicorn
__all__ = ['app']