#   """
#   NSAC Competition Management System - Response Utilities

#   This module provides utilities for generating HTTP responses, including
#   HTML rendering, redirects, and template processing for the web application.
#   """

import os

def response(body: bytes, status="200 OK", headers=None):
#   """
#   Create a basic HTTP response tuple.

#   Args:
#       body (bytes): The response body content.
#       status (str): HTTP status line (default: "200 OK").
#       headers (list): List of (name, value) header tuples.

#   Returns:
#       tuple: (status, headers, body_list) for WSGI.
#   """
    headers = headers or []
    headers = [("Content-Type", "text/html; charset=utf-8")] + headers
    return status, headers, [body]

def text(msg: str, status="200 OK", headers=None):
#   """
#   Create a text response.

#   Args:
#       msg (str): The text message to send.
#       status (str): HTTP status line.
#       headers (list): Additional headers.

#   Returns:
#       tuple: HTTP response tuple.
#   """
    return response(msg.encode("utf-8"), status=status, headers=headers)

def redirect(location: str):
    return "302 Found", [("Location", location)], [b""]

def set_cookie(headers, key, value, path="/", http_only=True):
    cookie = f"{key}={value}; Path={path}"
    if http_only:
        cookie += "; HttpOnly"
    headers.append(("Set-Cookie", cookie))

def clear_cookie(headers, key, path="/"):
    headers.append(("Set-Cookie", f"{key}=; Path={path}; Max-Age=0"))

def _templates_dir():
    return os.path.join(os.path.dirname(__file__), "..", "templates")

def _load_template(name: str) -> str:
    """
    Loads a template from /templates.
    Supports nested paths like 'admin/layout.html' or 'admin/application/index.html'
    """
    base_dir = _templates_dir()
    path = os.path.join(base_dir, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _apply_context(html: str, context: dict) -> str:
    """
    Replace placeholders in both formats: {{ key }} and {{key}}
    """
    for k, v in (context or {}).items():
        v = "" if v is None else str(v)
        html = html.replace("{{ " + k + " }}", v)
        html = html.replace("{{" + k + "}}", v)
    return html

def render_page(body_template: str, context: dict):
    """
    Render a normal page using the global templates/layout.html
    """
    body_html = _load_template(body_template)
    body_html = _apply_context(body_html, context)

    layout = _load_template("layout.html")
    page = layout.replace("{{ body }}", body_html)
    page = page.replace("{{ title }}", str((context or {}).get("title", "Hackathon Portal")))
    page = page.replace("{{ extra_head }}", str((context or {}).get("extra_head", "")))
    return page

def render_partial(template_name: str, context: dict) -> str:
    """
    Render a template WITHOUT wrapping it with templates/layout.html.
    Useful for admin content pages like:
      - admin/dashboard.html
      - admin/application/index.html
    """
    html = _load_template(template_name)
    return _apply_context(html, context)

def render_with_layout(layout_template: str, content_html: str, context: dict) -> str:
    """
    Render a custom layout (like admin/layout.html) and inject content into {{ content }}.
    """
    ctx = dict(context or {})
    ctx["content"] = content_html
    layout_html = _load_template(layout_template)
    return _apply_context(layout_html, ctx)

def render_html(body_html: str, title: str = "Hackathon Portal", extra_head: str = "") -> str:
    """
    Wrap raw HTML inside templates/layout.html (global layout).
    """
    layout = _load_template("layout.html")
    page = layout.replace("{{ body }}", body_html)
    page = page.replace("{{ title }}", str(title))
    page = page.replace("{{ extra_head }}", str(extra_head))
    return page
