"""Backend application package.

Ensures the repository root is importable so `import ml...` resolves when the
server is launched via the `uvicorn` console script (which, unlike `python -m`,
does not add the working directory to sys.path).
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
