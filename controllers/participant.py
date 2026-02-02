#   """
#   NSAC Competition Management System - Participant Controller

#   This module handles participant-specific functionality including dashboard access,
#   team member management, and project information submission.
#   """

import json
from auth.decorators import login_required, role_required
from utils.response import response, render_page, redirect
from utils.request import parse_form
from db.database import query_one, execute

CATEGORY_LIST = [
    "CREATE YOUR OWN CHALLENGE",
    "Animation Celebration of Terra Data!",
    "A World Away: Hunting for Exoplanets with AI",
    "BloomWatch: An Earth Observation Application for Global Flowering Phenology",
    "Build a Space Biology Knowledge Engine",
    "Commercializing Low Earth Orbit(LEO)",
    "Data Pathways to Healthy Cities and Human Settlements",
    "Deep Dive: Immersive Data Stories from Ocean to Sky",
    "Embiggen Your Eyes!",
    "From Earthdata to Action: Cloud Computing for Predicting Safer Skies",
    "International Space Station 25th anniversary Apps",
    "Meteor Madness",
    "NASA Farm Navigators: Using NASA Data Exploration in Agriculture",
    "Sharks from Space",
    "SpaceTrash Hack: Revolutionizing Recycling on Mars",
    "Stellar Stories: Space Weather Through the Eyes of Earthlings",
    "Through the Radar Looking Glass: Revealing Earth Processes",
    "Will It Rain On My Parade?",
    "Your Home in Space: The Habitat Layout Creator",
]

def _category_options(selected: str):
    html = []
    sel = (selected or "").strip()
    html.append('<option value="">Select One</option>')
    for c in CATEGORY_LIST:
        s = ' selected="selected"' if c == sel else ""
        html.append(f'<option value="{c}"{s}>{c}</option>')
    return "\n".join(html)

def _load_application(user_id: int):
    row = query_one(
        "SELECT status, data_json FROM participant_applications WHERE user_id=%s ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    if not row:
        return {"status": "pending", "data": {}}
    data = row["data_json"] or "{}"
    try:
        data = json.loads(data) if isinstance(data, str) else data
    except Exception:
        data = {}
    return {"status": row["status"], "data": data}

def _load_project(user_id: int):
    row = query_one(
        "SELECT id, title, description, team_members_json FROM projects WHERE participant_id=%s",
        (user_id,),
    )
    if not row:
        return None
    # team_members_json will store {"members":[...], "project_meta": {...}}
    members = []
    meta = {}
    raw = row["team_members_json"]
    if raw:
        try:
            obj = json.loads(raw) if isinstance(raw, str) else raw
            members = obj.get("members", []) or []
            meta = obj.get("project_meta", {}) or {}
        except Exception:
            pass
    return {
        "id": row["id"],
        "title": row["title"] or "",
        "description": row["description"] or "",
        "members": members,
        "meta": meta,
    }

@login_required
@role_required("participant")
def participant_dashboard(req):
    user = req["user"]
    q = req.get("query") or {}
    success = q.get("success") or ""
    tab = q.get("tab") or "team"

    app = _load_application(user["id"])
    app_data = app["data"]

    project = _load_project(user["id"]) or {"title": "", "description": "", "members": [], "meta": {}}
    meta = project["meta"]

    members = project["members"] if isinstance(project["members"], list) else []
    members_json = json.dumps(members)

    extra_head = """
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script>
      tailwind.config = { darkMode: 'class' }
      function toggleTheme(){ document.documentElement.classList.toggle('dark'); }
    </script>
    <style>[x-cloak]{display:none!important;}</style>
    """

    html = render_page(
        "participant_dashboard.html",
        {
            "title": "Participant Dashboard",
            "extra_head": extra_head,
            "active_tab": tab,

            "leader_name": user["name"],
            "leader_email": user["email"],

            "team_name": app_data.get("team_name", ""),
            "location": app_data.get("location", ""),
            "university": app_data.get("university", ""),
            "application_status": app["status"],

            "members_json": members_json,
            "members_json_string": members_json.replace('"', "&quot;"),

            "success_msg": "Saved successfully ✅" if success == "members" else "",
            "error_msg": "",

            "project_name": project["title"],
            "description": project["description"],
            "category_options": _category_options(meta.get("category", "")),
            "team_url": meta.get("team_url", ""),
            "data_sources": meta.get("data_sources", ""),
            "video_link": meta.get("video_link", ""),
            "github_link": meta.get("github_link", ""),

            "project_success": "Project saved ✅" if success == "project" else "",
            "project_error": "",
        },
    )
    return response(html.encode("utf-8"))

@login_required
@role_required("participant")
def save_team_members(req):
    user = req["user"]
    data, _ = parse_form(req["environ"])
    members_json = data.get("members_json") or "[]"

    # validate JSON
    try:
        members = json.loads(members_json)
        if not isinstance(members, list):
            raise ValueError("members must be list")
    except Exception:
        return redirect("/participant/dashboard?tab=team")

    # load existing project_meta if exists
    existing = _load_project(user["id"])
    meta = existing["meta"] if existing else {}

    payload = {"members": members, "project_meta": meta}

    if existing:
        execute(
            "UPDATE projects SET team_members_json=%s WHERE participant_id=%s",
            (json.dumps(payload), user["id"]),
        )
    else:
        execute(
            "INSERT INTO projects (participant_id, title, description, team_members_json) VALUES (%s,%s,%s,%s)",
            (user["id"], "", "", json.dumps(payload)),
        )

    return redirect("/participant/dashboard?tab=team&success=members")

@login_required
@role_required("participant")
def save_project(req):
    user = req["user"]
    data, _ = parse_form(req["environ"])

    project_name = (data.get("project_name") or "").strip()
    category = (data.get("category") or "").strip()
    team_url = (data.get("team_url") or "").strip()
    description = (data.get("description") or "").strip()
    data_sources = (data.get("data_sources") or "").strip()
    video_link = (data.get("video_link") or "").strip()
    github_link = (data.get("github_link") or "").strip()

    if not all([project_name, category, team_url, description, data_sources]):
        return redirect("/participant/dashboard?tab=project")

    existing = _load_project(user["id"])
    members = existing["members"] if existing else []
    meta = {
        "category": category,
        "team_url": team_url,
        "data_sources": data_sources,
        "video_link": video_link,
        "github_link": github_link,
        "team_work_score": 5,
        "user_experience_score": 5,
        "is_nasa_data_usage_score": 5,
        "is_challenge_category_score": 1,
        "id_project_link_score": 1,
        "is_nasa_global_team_url_score": 1,
    }
    payload = {"members": members, "project_meta": meta}

    if existing:
        execute(
            "UPDATE projects SET title=%s, description=%s, team_members_json=%s WHERE participant_id=%s",
            (project_name, description, json.dumps(payload), user["id"]),
        )
    else:
        execute(
            "INSERT INTO projects (participant_id, title, description, team_members_json) VALUES (%s,%s,%s,%s)",
            (user["id"], project_name, description, json.dumps(payload)),
        )

    return redirect("/participant/dashboard?tab=project&success=project")
