"""
Base settings to build other settings files upon.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# test_direct_payment_provider/
APPS_DIR = BASE_DIR / "test_direct_payment_provider"
env = environ.Env()
