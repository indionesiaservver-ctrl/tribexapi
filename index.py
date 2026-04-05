import os
import sys
# Ensure the current directory is in sys.path for IDE and runtime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
except ImportError:
    import app
    app = app.app