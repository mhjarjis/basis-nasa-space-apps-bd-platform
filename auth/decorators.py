#"""
#NSAC Competition Management System - Authentication Decorators

#This module provides decorators for enforcing authentication and authorization
#requirements on route handlers.
#"""

from utils.response import redirect, text
from utils.request import get_current_user

def login_required(handler):
#   """
#   Decorator that requires the user to be logged in.

#   Redirects to /login if not authenticated.

#   Args:
#       handler (callable): The route handler function.

#   Returns:
#       callable: The wrapped handler function.
#   """
    def wrapped(req):
        user = get_current_user(req)
        if not user:
            return redirect("/login")
        req["user"] = user
        return handler(req)
    return wrapped

def role_required(*roles):
#   """
#   Decorator that requires the user to have one of the specified roles.

#   Redirects to /login if not authenticated, or returns 403 if unauthorized.

#   Args:
#       *roles: Variable number of role strings that are allowed.

#   Returns:
#       callable: The decorator function.
#   """
    def deco(handler):
        def wrapped(req):
            user = req.get("user") or get_current_user(req)
            if not user:
                return redirect("/login")
            if user["role"] not in roles:
                return text("Forbidden", status="403 Forbidden")
            req["user"] = user
            return handler(req)
        return wrapped
    return deco
