#   """
#   NSAC Competition Management System - Configuration Module

#   This module contains all configuration settings for the application,
#   including database, server, upload, session, and security settings.
#   All settings can be overridden using environment variables.
#   """

import os
from pathlib import Path

# =========================
# BASE PATH
# =========================
BASE_DIR = Path(__file__).resolve().parent


# =========================
# APPLICATION SETTINGS
# =========================
# IMPORTANT: Change this secret key before deploying to production
APP_SECRET = os.environ.get(
    "APP_SECRET",
    "dev-secret-change-this-to-a-long-random-string"
)

DEBUG = os.environ.get("DEBUG", "1") == "1"


# =========================
# DATABASE (LARAGON MYSQL)
# =========================
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),  # NEVER use "localhost"
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),  # Laragon default = empty
    "database": os.environ.get("DB_NAME", "hackathon_db"),
    "charset": "utf8mb4",
    "autocommit": True,
}


# =========================
# SERVER
# =========================
BASE_URL = os.environ.get(
    "BASE_URL",
    "http://127.0.0.1:8000"
)


# =========================
# UPLOADS
# =========================
UPLOAD_DIR = BASE_DIR / "uploads" / "submissions"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max upload size: 20 MB
MAX_UPLOAD_SIZE = 20 * 1024 * 1024


# =========================
# SESSION SETTINGS
# =========================
SESSION_COOKIE_NAME = "session"
SESSION_EXPIRE_DAYS = 7


# =========================
# SECURITY
# =========================
PASSWORD_HASH_ITERATIONS = 120_000


# =========================
# DEADLINE KEYS (SITE CONFIG)
# =========================
REGISTRATION_DEADLINE_KEY = "registration_deadline"
PROJECT_INFO_DEADLINE_KEY = "project_info_deadline"
SUBMISSION_DEADLINE_KEY = "submission_deadline"
