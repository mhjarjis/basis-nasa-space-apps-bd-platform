#   """
#   NSAC Competition Management System - Security Utilities

#   This module provides security-related utilities including password hashing,
#   verification, and cryptographic signing for secure data handling.
#   """

import hashlib
import hmac
import secrets
from config import APP_SECRET

def hash_password(password: str) -> str:
#   """
#   Hash a password using PBKDF2 with SHA-256.

#   Generates a random salt and uses 120,000 iterations for security.

#   Args:
#       password (str): The plain text password to hash.

#   Returns:
#       str: The hashed password in the format 'pbkdf2_sha256$salt$hash'.
#   """
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${dk.hex()}"

def verify_password(password: str, stored: str) -> bool:
#   """
#   Verify a password against its stored hash.

#   Args:
#       password (str): The plain text password to verify.
#       stored (str): The stored hash string.

#   Returns:
#       bool: True if the password matches, False otherwise.
#   """
    try:
        algo, salt, hexdigest = stored.split("$", 2)
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
        return hmac.compare_digest(dk.hex(), hexdigest)
    except Exception:
        return False

def sign(value: str) -> str:
#   """
#   Sign a value using HMAC-SHA256 with the application secret.

#   Args:
#       value (str): The value to sign.

#   Returns:
#       str: The signed value in the format 'value.signature'.
#   """
    sig = hmac.new(APP_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{sig}"

def unsign(signed: str) -> str | None:
#   """
#   Verify and extract the original value from a signed string.

#   Args:
#       signed (str): The signed string in the format 'value.signature'.

#   Returns:
#       str or None: The original value if signature is valid, None otherwise.
#   """
    try:
        value, sig = signed.rsplit(".", 1)
        expected = hmac.new(APP_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            return value
        return None
    except Exception:
        return None
