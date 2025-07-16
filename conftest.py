import sys
import os
from pathlib import Path

# Add the project root to Python path so imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add backend directory to path as well for direct imports
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path)) 