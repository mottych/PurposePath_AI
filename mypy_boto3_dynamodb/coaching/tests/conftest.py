"""Pytest fixtures and dependency overrides for coaching tests.

Provides an in-memory ConversationService so endpoints avoid AWS calls
(DynamoDB, S3, Redis, Bedrock) during tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add the workspace root to Python path for explicit service imports
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))





