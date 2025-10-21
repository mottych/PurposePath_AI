"""Test configuration for coaching service with explicit imports."""

import os
import sys
from pathlib import Path
from typing import Any

# Set service identifier
os.environ.setdefault("PURPOSEPATH_SERVICE", "coaching")

# Calculate paths
SERVICE_DIR = Path(__file__).parent
SRC_DIR = SERVICE_DIR / "src"
REPO_ROOT = SERVICE_DIR.parent
SHARED_DIR = REPO_ROOT / "shared"

# Add the workspace root to Python path for explicit service imports
root_str = str(REPO_ROOT)
while root_str in sys.path:
    sys.path.remove(root_str)
sys.path.insert(0, root_str)

# Ensure shared modules are available
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

# Add service directory to path
service_str = str(SERVICE_DIR)
while service_str in sys.path:
    sys.path.remove(service_str)
sys.path.insert(1, service_str)


def _module_under_path(mod: Any, base: Path) -> bool:
    file_path = getattr(mod, "__file__", None)
    if not file_path:
        return False
    try:
        return Path(file_path).resolve().is_relative_to(base)
    except AttributeError:
        return str(Path(file_path).resolve()).startswith(str(base.resolve()))


for name, mod in list(sys.modules.items()):
    if name == "shared":
        continue
    if name.startswith("shared.") and not _module_under_path(mod, SHARED_DIR):
        sys.modules.pop(name, None)

if "shared" in sys.modules and not _module_under_path(sys.modules["shared"], SHARED_DIR):
    del sys.modules["shared"]
    __import__("shared")
elif "shared" not in sys.modules:
    __import__("shared")
