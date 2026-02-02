#   """
#   NSAC Competition Management System - Request Utilities

#   This module provides utilities for parsing HTTP requests, including
#   query parameters, form data, cookies, and user authentication.
#   """

from urllib.parse import parse_qs
import cgi
from auth.security import unsign
from auth.sessions import get_user_by_session

def parse_cookies(environ):
#   """
#   Parse HTTP cookies from the WSGI environ.

#   Args:
#       environ (dict): WSGI environment dictionary.

#   Returns:
#       dict: Dictionary of cookie name-value pairs.
#   """
    raw = environ.get("HTTP_COOKIE", "")
    cookies = {}
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            cookies[k] = v
    return cookies

def parse_query(environ):
    return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(environ.get("QUERY_STRING", "")).items()}

def parse_form(environ):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method not in ("POST", "PUT", "PATCH"):
        return {}, None

    content_type = environ.get("CONTENT_TYPE", "")
    if content_type.startswith("multipart/form-data"):
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
        data = {}
        file_item = None
        for key in fs.keys():
            item = fs[key]
            if getattr(item, "filename", None):
                file_item = item
        else:#  
                data[key] = item.value
        return data, file_item

    try:
        size = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        size = 0
    body = environ["wsgi.input"].read(size).decode("utf-8", errors="ignore")
    data = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(body).items()}
    return data, None

def get_current_user(req):
    cookies = req.get("cookies") or {}
    signed = cookies.get("session")
    if not signed:
        return None
    token = unsign(signed)
    if not token:
        return None
    return get_user_by_session(token)
