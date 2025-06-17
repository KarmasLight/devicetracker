import os
import sys

# Add your app's directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import your Flask app
from app import app as application  # noqa

# Initialize the database
with application.app_context():
    from app import init_db
    init_db()
