
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import init_db

if __name__ == "__main__":
    print("=== MANUAL DATABASE INITIALIZATION ===")
    init_db()
    print("✅ Initialization complete.")
