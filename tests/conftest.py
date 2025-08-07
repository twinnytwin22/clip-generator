import os
import sys
from pathlib import Path

# Ensure the src directory is on the path for test imports
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
    # Ensure subprocesses (e.g., invoking ``python -m clip_generator``) can
    # also locate the package without installation.
    env_path = os.environ.get("PYTHONPATH", "")
    paths = [str(SRC)] + ([env_path] if env_path else [])
    os.environ["PYTHONPATH"] = os.pathsep.join(paths)
