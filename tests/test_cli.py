from importlib import metadata
import subprocess
import sys


def test_help():
    result = subprocess.run([sys.executable, '-m', 'clip_generator', '--help'], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
