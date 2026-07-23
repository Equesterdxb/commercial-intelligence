"""Pytest configuration."""

import os
from pathlib import Path

# Load environment variables for tests
from dotenv import load_dotenv

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
