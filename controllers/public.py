#   """
#   NSAC Competition Management System - Public Controller

#   This module handles public-facing routes including home page, user authentication,
#   registration, and logout functionality for all user types.
#   """

import json
from db.database import query_one, execute
from auth.security import hash_password, verify_password, sign
from auth.sessions import create_session, destroy_session
from utils.response import (
    response,
    redirect,
    render_page,
    set_cookie,
    clear_cookie,
)
from utils.request import parse_form, parse_cookies
from utils.form import get_form


# =========================
# HOME
# =========================
def home(req):
    extra_head = """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script>
      tailwind.config = { darkMode: 'class' }
      function toggleTheme() { document.documentElement.classList.toggle('dark'); }
    </script>
    <style>
      body { transition: background-color .5s, color .5s; }
      .hero-gradient {
        background: radial-gradient(circle at top right, rgba(37, 99, 235, 0.1), transparent);
      }
      .dark .hero-gradient {
        background: radial-gradient(circle at top right, rgba(30, 58, 138, 0.3), transparent);
      }
    </style>
    """

    html = render_page(
        "home.html",
        {
            "title": "NASA Space Apps Challenge | Bangladesh 2026",
            "extra_head": extra_head,
        },
    )
    return response(html.encode("utf-8"))


# =========================
# LOGIN
# =========================
def _login_extra_head():
    return """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
      .glass {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3);
      }
      body {
        background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
        background-attachment: fixed;
      }
      .bg-blob {
        filter: blur(80px);
        z-index: -1;
      }
    </style>
    """

def login_get(req):
    html = render_page(
        "login.html",
        {
            "title": "Login | NASA Space Apps BD",
            "extra_head": _login_extra_head(),
            "error": "",
            "error_box_class": "hidden",
        },
    )
    return response(html.encode("utf-8"))

def login_post(req):
    data, _ = parse_form(req["environ"])
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = query_one(
        "SELECT * FROM users WHERE email=%s AND status='active'",
        (email,),
    )

    if not user or not verify_password(password, user["password_hash"]):
        html = render_page(
            "login.html",
            {
                "title": "Login | NASA Space Apps BD",
                "extra_head": _login_extra_head(),
                "error": "Invalid email or password",
                "error_box_class": "",  # show box
            },
        )
        return response(html.encode("utf-8"), status="401 Unauthorized")

    token = create_session(user["id"])
    headers = []
    set_cookie(headers, "session", sign(token))

    role = user["role"]
    if role == "admin":
        return "302 Found", headers + [("Location", "/admin/dashboard")], [b""]
    if role == "judge":
        return "302 Found", headers + [("Location", "/judge/dashboard")], [b""]
    if role == "volunteer":
        return "302 Found", headers + [("Location", "/volunteer/dashboard")], [b""]
    return "302 Found", headers + [("Location", "/participant/dashboard")], [b""]



# =========================
# REGISTER (FULL PROCESS)
# =========================
def register_get(req):
    html = render_page(
        "register.html",
        {
            "title": "Participant Registration",
            "error": "",
            "error_box_class": "hidden"
        },
    )
    return response(html.encode("utf-8"))


def register_post(req):
    data, _ = parse_form(req["environ"])

    team_name = (data.get("team_name") or "").strip()
    location = (data.get("location") or "").strip()
    university = (data.get("university") or "").strip()
    leader_name = (data.get("leader_name") or "").strip()
    leader_mobile = (data.get("leader_mobile") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validation
    if not all(
        [
            team_name,
            location,
            university,
            leader_name,
            leader_mobile,
            email,
            password,
        ]
    ):
        html = render_page(
            "register.html",
            {
                "title": "Participant Registration",
                "error": "All fields are required.",
                "error_box_class": ""
            },
        )
        return response(html.encode("utf-8"), status="400 Bad Request")

    if len(password) < 6:
        html = render_page(
            "register.html",
            {
                "title": "Participant Registration",
                "error": "Password must be at least 6 characters.",
            },
        )
        return response(html.encode("utf-8"), status="400 Bad Request")

    exists = query_one("SELECT id FROM users WHERE email=%s", (email,))
    if exists:
        html = render_page(
            "register.html",
            {
                "title": "Participant Registration",
                "error": "This email is already registered.",
            },
        )
        return response(html.encode("utf-8"), status="409 Conflict")

    # 1) Create participant user
    user_id = execute(
        "INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'participant')",
        (leader_name, email, hash_password(password)),
    )

    # 2) Create participant application (pending)
    application_data = {
        "team_name": team_name,
        "location": location,
        "university": university,
        "leader_name": leader_name,
        "leader_mobile": leader_mobile,
        "leader_email": email,
    }

    execute(
        "INSERT INTO participant_applications (user_id, data_json, status) VALUES (%s,%s,'pending')",
        (user_id, json.dumps(application_data)),
    )

    return redirect("/login")

def portal_login_get(req):
    html = render_page(
        "admin/auth/login.html",
        {
            "title": "Login | NASA Space Apps BD",
            "extra_head": _login_extra_head(),
            "error": "",
            "error_box_class": "hidden",
        },
    )
    return response(html.encode("utf-8"))

def portal_login_post(req):
    data, _ = parse_form(req["environ"])
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = query_one(
        "SELECT * FROM users WHERE email=%s AND status='active'",
        (email,),
    )

    if not user or not verify_password(password, user["password_hash"]):
        html = render_page(
            "login.html",
            {
                "title": "Login | NASA Space Apps BD",
                "extra_head": _login_extra_head(),
                "error": "Invalid email or password",
                "error_box_class": "",  # show box
            },
        )
        return response(html.encode("utf-8"), status="401 Unauthorized")

    token = create_session(user["id"])
    headers = []
    set_cookie(headers, "session", sign(token))

    role = user["role"]
    if role == "admin":
        return "302 Found", headers + [("Location", "/admin/dashboard")], [b""]
    if role == "judge":
        return "302 Found", headers + [("Location", "/judge/dashboard")], [b""]
    if role == "volunteer":
        return "302 Found", headers + [("Location", "/volunteer/dashboard")], [b""]
    return "302 Found", headers + [("Location", "/participant/dashboard")], [b""]    

# =========================
# ADMIN REGISTER (FULL PROCESS)
# =========================
def portal_register_get(req):
    html = render_page(
        "admin/auth/register.html",
        {
            "title": "Personnel Registration",
            "error": "",
            "error_box_class": "hidden"
        },
    )
    return response(html.encode("utf-8"))


def portal_register_post(req):
    form, _ = get_form(req)

    # Extracting fields from your Judge/Volunteer form
    name = (form.get("name") or "").strip()
    designation = (form.get("designation") or "").strip()
    organization = (form.get("organization") or "").strip()
    phone = (form.get("phone") or "").strip()
    email = (form.get("email") or "").strip().lower()
    password = form.get("password") or ""
    
    # Mapping 'type' directly to 'role' (judge/volunteer)
    role = (form.get("type") or "volunteer").strip()

    # 1. Validation: Ensure all fields are filled
    if not all([name, designation, organization, phone, email, password, role]):
        html = render_page(
            "admin/auth/register.html",
            {
                "title": "Personnel Registration",
                "error": "All fields are required for verification.",
            },
        )
        return response(html.encode("utf-8"), status="400 Bad Request")

    # 2. Password Length Check
    if len(password) < 6:
        html = render_page(
            "admin/auth/register.html",
            {
                "title": "Personnel Registration",
                "error": "Password must be at least 6 characters.",
            },
        )
        return response(html.encode("utf-8"), status="400 Bad Request")

    # 3. Check if user already exists
    exists = query_one("SELECT id FROM users WHERE email=%s", (email,))
    if exists:
        html = render_page(
            "admin/auth/register.html",
            {
                "title": "Personnel Registration",
                "error": "This email is already registered.",
            },
        )
        return response(html.encode("utf-8"), status="409 Conflict")

    # 4. Insert into users table (Role is assigned here)
    execute(
        "INSERT INTO users (name, designation, organization, phone, email, password_hash, role) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (name, designation, organization, phone, email, hash_password(password), role),
    )
    # 5. Redirect to login page after successful registration
    return redirect("/login")

# =========================
# LOGOUT
# =========================
def logout(req):
    cookies = parse_cookies(req["environ"])
    signed = cookies.get("session")

    if signed:
        from auth.security import unsign

        token = unsign(signed)
        if token:
            destroy_session(token)

    headers = []
    clear_cookie(headers, "session")
    return "302 Found", headers + [("Location", "/")], [b""]
