#   """
#   NSAC Competition Management System - Main Application Module

#   This module defines the core WSGI application for the NSAC Competition Management System.
#   It handles routing, static file serving, and request processing.
#   """

import os
from routes import ROUTES
from utils.request import parse_query, parse_cookies
from utils.response import text

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

def match_route(method, path):
#   """
#   Match the HTTP method and path against defined routes.

#   Args:
#       method (str): The HTTP method (e.g., 'GET', 'POST').
#       path (str): The request path.

#   Returns:
#       callable or None: The handler function if a match is found, otherwise None.
#   """
    for m, p, handler in ROUTES:
        if m == method and p == path:
            return handler
    return None

def serve_static(path):
#   """
#   Serve static files from the static directory.
#   
#   Args:
#       path (str): The request path starting with '/static/'.
#   
#   Returns:
#       tuple: (status, headers, body) for the response.
#   """
    rel = path.replace("/static/", "", 1)
    file_path = os.path.join(STATIC_DIR, rel)
    if not os.path.isfile(file_path):
        return text("Not Found", status="404 Not Found")

    # Determine content-type based on file extension
    ctype = "text/plain"
    if file_path.endswith(".css"):
        ctype = "text/css"
    elif file_path.endswith(".js"):
        ctype = "application/javascript"

    with open(file_path, "rb") as f:
        body = f.read()
    return "200 OK", [("Content-Type", ctype)], [body]

def application(environ, start_response):
#   """
#   WSGI application entry point.

#   Processes the request, matches routes, and returns the response.

#   Args:
#       environ (dict): WSGI environment dictionary.
#       start_response (callable): WSGI start_response callable.

#   Returns:
#       iterable: The response body.
#   """
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    if path.startswith("/static/"):
        status, headers, body = serve_static(path)
        start_response(status, headers)
        return body

    handler = match_route(method, path)
    if not handler:
        status, headers, body = text("Not Found", status="404 Not Found")
        start_response(status, headers)
        return body

    req = {
        "environ": environ,
        "method": method,
        "path": path,
        "query": parse_query(environ),
        "cookies": parse_cookies(environ),
    }

    status, headers, body = handler(req)
    start_response(status, headers)
    return body
