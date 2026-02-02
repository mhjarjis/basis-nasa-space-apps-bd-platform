#   """
#   NSAC Competition Management System - Session Management

#   This module handles user session creation, validation, and destruction
#   for maintaining authenticated user state across requests.
#   """

from datetime import datetime, timedelta
import secrets
from db.database import execute, query_one

SESSION_DAYS = 7

def create_session(user_id: int) -> str:
#   """
#   Create a new session for a user.

#   Generates a secure random token and stores it in the database with an expiration.

#   Args:
#       user_id (int): The ID of the user for whom to create the session.

#   Returns:
#       str: The session token.
#   """
    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    execute(
        "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (%s,%s,%s)",
        (user_id, token, expires.strftime("%Y-%m-%d %H:%M:%S"))
    )
    return token

def get_user_by_session(token: str):
#   """
#   Retrieve user information associated with a valid session token.

#   Args:
#       token (str): The session token.

#   Returns:
#       dict or None: User data if session is valid and not expired, None otherwise.
#   """
    row = query_one("""
      SELECT u.id, u.name, u.email, u.role
      FROM sessions s
      JOIN users u ON u.id = s.user_id
      WHERE s.session_token=%s AND s.expires_at > UTC_TIMESTAMP()
    """, (token,))
    return row

def destroy_session(token: str):
#   """
#   Destroy a session by removing it from the database.

#   Args:
#       token (str): The session token to destroy.
#   """
    execute("DELETE FROM sessions WHERE session_token=%s", (token,))
