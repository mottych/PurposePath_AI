"""Lambda handler bootstrap that sets up Python path for coaching.src imports."""

import sys
from pathlib import Path

# Add parent directory to path to enable coaching.src.* imports
task_root = Path("/var/task")
if str(task_root) not in sys.path:
    sys.path.insert(0, str(task_root))

# Now import the actual handler
from coaching.src.api.main import handler  # noqa: E402, F401

# Re-export for Lambda
__all__ = ["handler"]
