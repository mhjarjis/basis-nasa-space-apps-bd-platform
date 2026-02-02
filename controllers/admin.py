#   """
#   NSAC Competition Management System - Admin Controller

#   This module handles all administrative functions including user management,
#   application processing, room assignments, judge/volunteer management,
#   and results processing for the competition system.
#   """

import json
import math
from auth.decorators import login_required, role_required
from utils.response import response, render_partial, render_with_layout, render_html,text, redirect
from utils.form import get_form
from db.database import query_one, query_all, execute
from auth.decorators import login_required, role_required

ADMIN_EXTRA_HEAD = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
  .sidebar-link.active {
    background-color: #2563eb;
    color: white;
    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
  }
</style>
"""

def _admin_base(user, page_title: str):
#   """
#   Create the base context dictionary for admin pages.

#   Args:
#       user (dict): The current user information.
#       page_title (str): The title for the current page.

#   Returns:
#       dict: Base context with user info, navigation states, and page metadata.
#   """
    avatar_name = (user.get("name") or "Admin").replace(" ", "+")
    return {
        "title": "Admin | NASA Space Apps BD",
        "extra_head": ADMIN_EXTRA_HEAD,

        "admin_name": user.get("name", "Admin"),
        "admin_role_label": "Super Admin",
        "admin_avatar_url": f"https://ui-avatars.com/api/?name={avatar_name}&background=0D8ABC&color=fff",

        "page_title": page_title,

        "nav_dashboard_active": "",
        "nav_applications_active": "",
        "nav_rooms_active": "",
        "nav_jv_active": "",
        "nav_control_active": "",
        "nav_results_active": "",
        "nav_inactive": "text-slate-500 hover:bg-slate-50 hover:text-blue-600",
    }

def _set_active(ctx, active: str):
#   """
#   Set the active navigation item in the admin context.

#   Args:
#       ctx (dict): The context dictionary to modify.
#       active (str): The active navigation section ('dashboard', 'applications', 'rooms', 'jv', 'result').
#   """
    if active == "dashboard":
        ctx["nav_dashboard_active"] = "active"
    elif active == "applications":
        ctx["nav_applications_active"] = "active"
    elif active == "rooms":
        ctx["nav_rooms_active"] = "active"
    elif active == "jv":
        ctx["nav_jv_active"] = "active"
    elif active == "result":
        ctx["nav_results_active"] = "active"

def _render_admin(req, page_title: str, active: str, page_tpl: str, page_ctx: dict):
#   """
#   Render an admin page with proper layout hierarchy.

#   Renders the page through: content page -> admin/layout.html -> global templates/layout.html

#   Args:
#       req (dict): The request object containing user info.
#       page_title (str): The title for the page.
#       active (str): The active navigation section.
#       page_tpl (str): The template file for the page content.
#       page_ctx (dict): Context variables for the page template.

#   Returns:
#       tuple: (status, headers, body) for the HTTP response.
#   """
    user = req["user"]
    base = _admin_base(user, page_title)
    _set_active(base, active)

    # 1) render content-only page (inside templates/admin/..)
    content_html = render_partial(page_tpl, page_ctx)

    # 2) inject into admin/layout.html (sidebar/menu)
    admin_full = render_with_layout("admin/layout.html", content_html, base)

    # 3) wrap into global layout.html (loads Tailwind + head assets)
    final_html = render_html(
        admin_full,
        title=base.get("title", "Admin"),
        extra_head=base.get("extra_head", "")
    )

    return response(final_html.encode("utf-8"))

@login_required
@role_required("admin")
def admin_dashboard(req):
#   """
#   Display the admin dashboard with key performance indicators and recent applications.

#   Calculates KPIs for total teams, room occupancy, active judges/volunteers,
#   submissions, and completion rate. Also shows recent participant applications.

#   Args:
#       req (dict): The request object.

#   Returns:
#       tuple: HTTP response from _render_admin.
#   """
    # ---------------------------
    # KPI: Total Teams
    # ---------------------------
    # Count unique participant applications (latest state doesn't matter for count)
    total_teams_row = query_one("SELECT COUNT(*) AS c FROM participant_applications")
    total_teams = int((total_teams_row or {}).get("c") or 0)

    # ---------------------------
    # KPI: Rooms Occupied
    # ---------------------------
    rooms_total_row = query_one("SELECT COUNT(*) AS c FROM room")
    rooms_total = int((rooms_total_row or {}).get("c") or 0)

    rooms_occupied_row = query_one("""
        SELECT COUNT(DISTINCT room_id) AS c
        FROM project_room
    """)
    rooms_occupied = int((rooms_occupied_row or {}).get("c") or 0)

    rooms_percent = 0
    if rooms_total > 0:
        rooms_percent = int(round((rooms_occupied / rooms_total) * 100))

    # ---------------------------
    # KPI: Active Judges (and Volunteer note)
    # ---------------------------
    judges_row = query_one("SELECT COUNT(*) AS c FROM users WHERE role='judge' AND status='active'")
    active_judges = int((judges_row or {}).get("c") or 0)

    volunteers_row = query_one("SELECT COUNT(*) AS c FROM users WHERE role='volunteer' AND status='active'")
    active_volunteers = int((volunteers_row or {}).get("c") or 0)

    # ---------------------------
    # KPI: Submissions (and completion rate note)
    # ---------------------------
    submissions_row = query_one("SELECT COUNT(*) AS c FROM projects where  not (title IS NULL OR title = '')")
    submissions = int((submissions_row or {}).get("c") or 0)

    completion_rate = 0
    if total_teams > 0:
        completion_rate = int(round((submissions / total_teams) * 100))

    # ---------------------------
    # Recent Applications
    # ---------------------------
    apps = query_all("""
        SELECT pa.id, pa.status, pa.data_json, pa.created_at,
               u.name AS leader_name, u.email AS leader_email
        FROM participant_applications pa
        JOIN users u ON u.id = pa.user_id
        ORDER BY pa.created_at DESC
        LIMIT 8
    """)

    def safe_json(val):
        if not val:
            return {}
        try:
            return json.loads(val) if isinstance(val, str) else (val or {})
        except Exception:
            return {}

    def badge_html(status):
        s = (status or "").lower()
        if s == "approved":
            return '<span class="px-3 py-1 bg-green-50 text-green-600 rounded-full text-[10px] font-black uppercase">Approved</span>'
        if s == "rejected":
            return '<span class="px-3 py-1 bg-red-50 text-red-600 rounded-full text-[10px] font-black uppercase">Rejected</span>'
        return '<span class="px-3 py-1 bg-orange-50 text-orange-600 rounded-full text-[10px] font-black uppercase">Pending</span>'

    recent_rows_list = []
    for row in apps:
        data = safe_json(row.get("data_json"))
        team_name = data.get("team_name", "—")
        location = data.get("location", "—")
        university = data.get("university", "—")
        leader = data.get("leader_name") or row.get("leader_name") or "—"
        status = row.get("status", "pending")

        recent_rows_list.append(f"""
        <tr class="border-b border-slate-50">
            <td class="py-5 font-bold">{team_name}</td>
            <td class="py-5">{location}, {university}</td>
            <td class="py-5">{leader}</td>
            <td class="py-5">{badge_html(status)}</td>
        </tr>
        """)

    recent_rows = "\n".join(recent_rows_list) if recent_rows_list else """
    <tr>
      <td class="py-6 text-slate-400" colspan="5">No applications found.</td>
    </tr>
    """

    # Notes (you can change the text anytime)
    kpi_total_teams_note = f"{total_teams} registered teams"
    kpi_active_judges_note = f"{active_volunteers} active volunteers"
    kpi_submissions_note = f"{completion_rate}% completion rate"

    page_ctx = {
        "kpi_total_teams": str(total_teams),
        "kpi_total_teams_note": kpi_total_teams_note,

        "kpi_rooms": f"{rooms_occupied}/{rooms_total}",
        "kpi_rooms_percent": str(rooms_percent),

        "kpi_active_judges": str(active_judges),
        "kpi_active_judges_note": kpi_active_judges_note,

        "kpi_submissions": str(submissions),
        "kpi_submissions_note": kpi_submissions_note,

        "recent_rows": recent_rows,
    }

    return _render_admin(req, "Overview Summary", "dashboard", "admin/dashboard.html", page_ctx)

@login_required
@role_required("admin")
def admin_applications(req):
    q = req["query"]
    search = q.get("q", "").strip()
    status = q.get("status", "").strip()
    page = int(q.get("page", "1") or 1)
    per_page = 10
    offset = (page - 1) * per_page

    where = "WHERE 1=1"
    params = []

    if status:
        where += " AND status=%s"
        params.append(status)

    if search:
        where += " AND data_json LIKE %s"
        params.append(f"%{search}%")

    total_row = query_one(
        f"SELECT COUNT(*) AS c FROM participant_applications {where}",
        params,
    )
    total = int(total_row["c"])
    total_pages = max(1, math.ceil(total / per_page))

    rows = query_all(
        f"""
        SELECT id, status, data_json
        FROM participant_applications
        {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        params + [per_page, offset],
    )

    def badge(s):
        return {
            "approved": "bg-green-50 text-green-600",
            "rejected": "bg-red-50 text-red-600",
            "pending": "bg-orange-50 text-orange-600",
        }.get(s, "bg-slate-50 text-slate-600")

    table_rows = []
    for r in rows:
        d = json.loads(r["data_json"])
        table_rows.append(f"""
        <tr class="border-b border-slate-50">
            <td class="pl-4 py-4 font-bold">{d.get("team_name","—")}</td>
            <td class="py-4">{d.get("location","—")}</td>
            <td class="py-4">{d.get("university","—")}</td>
            <td class="text-center py-4">
                <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase {badge(r['status'])}">
                    {r['status']}
                </span>
            </td>
            <td class="pr-4 py-4 text-center space-x-3 whitespace-nowrap">

              <!-- View -->
              <a href="/admin/applications/view?id={r['id']}"
                class="text-slate-400 hover:text-blue-600 font-bold">
                <i class="fa fa-eye" aria-hidden="true"></i>
              </a>

              <!-- Edit -->
              <a href="/admin/applications/edit?id={r['id']}"
                class="text-slate-400 hover:text-orange-600 font-bold">
                <i class="fa fa-pencil-square" aria-hidden="true"></i>
              </a>

              <!-- Delete -->
              <a href="/admin/applications/delete?id={r['id']}"
                onclick="return confirm('Delete this application?')"
                class="text-slate-400 hover:text-red-600 font-bold">
                <i class="fa fa-trash" aria-hidden="true"></i>
              </a>

                {action_buttons(r['id'], r['status'])}

            </td>

        </tr>
        """)

    pagination_text = f"Showing {(offset+1)} to {min(offset+per_page, total)} of {total} Entries"

    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)

    page_ctx = {
        "rows": "\n".join(table_rows) or "<tr><td colspan='5'>No data</td></tr>",
        "search": search,
        "status": status,
        "pagination_text": pagination_text,
        "prev_page": prev_page,
        "next_page": next_page,
        "page": page,
    }

    return _render_admin(
        req,
        "All Applications",
        "applications",
        "admin/application/index.html",
        page_ctx,
    )

def action_buttons(app_id, status):
    buttons = []

    if status == "pending":
        buttons.append(f"""
        <form method="post" action="/admin/applications/status" class="inline">
          <input type="hidden" name="id" value="{app_id}">
          <input type="hidden" name="status" value="approved">
          <button type="submit"
            class="text-green-600 hover:text-green-800 font-black"
            title="Approve">
            <i class="fa fa-check-circle"></i>
          </button>
        </form>
        """)

        buttons.append(f"""
        <form method="post" action="/admin/applications/status" class="inline">
          <input type="hidden" name="id" value="{app_id}">
          <input type="hidden" name="status" value="rejected">
          <button type="submit"
            class="text-red-600 hover:text-red-800 font-black"
            title="Reject">
            <i class="fa fa-times-circle"></i>
          </button>
        </form>
        """)

    elif status == "approved":
        buttons.append(f"""
        <form method="post" action="/admin/applications/status" class="inline">
          <input type="hidden" name="id" value="{app_id}">
          <input type="hidden" name="status" value="rejected">
          <button type="submit"
            class="text-red-600 hover:text-red-800 font-black"
            title="Reject">
            <i class="fa fa-times-circle"></i>
          </button>
        </form>
        """)

    elif status == "rejected":
        buttons.append(f"""
        <form method="post" action="/admin/applications/status" class="inline">
          <input type="hidden" name="id" value="{app_id}">
          <input type="hidden" name="status" value="approved">
          <button type="submit"
            class="text-green-600 hover:text-green-800 font-black"
            title="Approve">
            <i class="fa fa-check-circle"></i>
          </button>
        </form>
        """)

    return "\n".join(buttons)


@login_required
@role_required("admin")
def admin_application_view(req):
    app_id = req["query"].get("id")
    if not app_id:
        return redirect("/admin/applications")

    # 1) Load application
    app = query_one(
        "SELECT id, user_id, status, data_json FROM participant_applications WHERE id=%s",
        [app_id],
    )
    if not app:
        return redirect("/admin/applications")

    # Parse application JSON
    try:
        app_data = json.loads(app["data_json"] or "{}")
    except Exception:
        app_data = {}

    # 2) Load project for this participant (participant_id = user_id)
    project = query_one(
        "SELECT title, description, team_members_json FROM projects WHERE participant_id=%s",
        [app["user_id"]],
    )

    project_title = "—"
    project_description = "—"
    project_meta = {}
    members = []
    data_sources = "—"

    if project:
        project_title = project.get("title") or "—"
        project_description = project.get("description") or "—"

        try:
            tm = json.loads(project.get("team_members_json") or "{}")
        except Exception:
            tm = {}

        members = tm.get("members", []) or []
        project_meta = tm.get("project_meta", {}) or {}
        data_sources = project_meta.get("data_sources") or "—"

    # Build roster HTML from members list
    roster_html = ""
    for m in members:
        roster_html += f"""
        <div class="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
            <span class="text-sm font-bold text-slate-700">
                {m.get('name','—')}<br>
                <i class="fa-solid fa-envelope text-slate-300 w-5"></i> {m.get('email','—')}<br>
                <i class="fa-solid fa-phone text-slate-300 w-5"></i> {m.get('phone','—')}
            </span>
            <span class="text-[9px] font-black text-slate-400 uppercase">{(m.get('gender') or 'member')}</span>
        </div>
        """
    if not roster_html:
        roster_html = "<div class='text-sm text-slate-400'>No members added yet.</div>"

    # Status button logic
    status = (app.get("status") or "pending").lower()
    show_approve = status != "approved"
    show_reject = status != "rejected"

    page_ctx = {
        "app_id": str(app["id"]),
        "team_name": app_data.get("team_name", "—"),
        "location": app_data.get("location", "—"),
        "university": app_data.get("university", "—"),
        "leader_name": app_data.get("leader_name", "—"),
        "leader_email": app_data.get("leader_email", "—"),
        "leader_mobile": app_data.get("leader_mobile", "—"),

        "roster_html": roster_html,

        "project_title": project_title,
        "project_category": project_meta.get("category", "—"),
        "project_description": project_description,

        "team_url": project_meta.get("team_url", "#"),
        "video_link": project_meta.get("video_link", "#"),
        "github_link": project_meta.get("github_link", "#"),
        "data_sources": data_sources,

        # show/hide buttons
        "approve_btn_class": "" if show_approve else "hidden",
        "reject_btn_class": "" if show_reject else "hidden",
    }

    return _render_admin(
        req,
        "Application Details",
        "applications",
        "admin/application/view.html",  # <-- your template path
        page_ctx,
    )


@login_required
@role_required("admin")
def admin_application_edit(req):
    app_id = req["query"].get("id")
    if not app_id:
        return redirect("/admin/applications")

    # Load application
    app = query_one(
        "SELECT id, user_id, status, data_json FROM participant_applications WHERE id=%s",
        [app_id],
    )
    if not app:
        return redirect("/admin/applications")

    # Load project (participant_id = user_id)
    project = query_one(
        "SELECT participant_id, title, description, team_members_json FROM projects WHERE participant_id=%s",
        [app["user_id"]],
    )

    # Parse JSON safely
    def safe_json(s, default):
        if not s:
            return default
        try:
            return json.loads(s) if isinstance(s, str) else s
        except Exception:
            return default

    app_data = safe_json(app.get("data_json"), {})

    tm = safe_json(project.get("team_members_json") if project else None, {})
    members = tm.get("members", []) or []
    project_meta = tm.get("project_meta", {}) or {}

    error = ""

    # POST: Save changes
    if req["method"] == "POST":
        form, _ = get_form(req)

        # Application fields
        team_name = (form.get("team_name") or "").strip()
        location = (form.get("location") or "").strip()
        university = (form.get("university") or "").strip()
        leader_name = (form.get("leader_name") or "").strip()
        leader_email = (form.get("leader_email") or "").strip()
        leader_mobile = (form.get("leader_mobile") or "").strip()
        status = (form.get("status") or "pending").strip().lower()

        # Project fields
        project_title = (form.get("project_title") or "").strip()
        project_description = (form.get("project_description") or "").strip()

        category = (form.get("category") or "").strip()
        team_url = (form.get("team_url") or "").strip()
        video_link = (form.get("video_link") or "").strip()
        github_link = (form.get("github_link") or "").strip()
        data_sources = (form.get("data_sources") or "").strip()

        # Members JSON (optional)
        members_json_raw = (form.get("members_json") or "").strip()
        new_members = members  # default keep existing

        if members_json_raw:
            try:
                parsed = json.loads(members_json_raw)
                if not isinstance(parsed, list):
                    raise ValueError("Members JSON must be a list.")
                new_members = parsed
            except Exception as e:
                error = f"Invalid Members JSON: {str(e)}"

        # Basic validation (keep it minimal)
        if not error:
            if not team_name or not location or not university or not leader_name or not leader_email or not leader_mobile:
                error = "Please fill all required application fields."
            elif status not in ("pending", "approved", "rejected"):
                error = "Invalid status value."

        # Save if OK
        if not error:
            updated_app_data = {
                "location": location,
                "team_name": team_name,
                "university": university,
                "leader_name": leader_name,
                "leader_email": leader_email,
                "leader_mobile": leader_mobile,
            }

            execute(
                "UPDATE participant_applications SET status=%s, data_json=%s WHERE id=%s",
                [status, json.dumps(updated_app_data), app_id],
            )

            updated_meta = {
                "category": category,
                "team_url": team_url,
                "video_link": video_link,
                "github_link": github_link,
                "data_sources": data_sources,
            }

            updated_team_members_json = {
                "members": new_members,
                "project_meta": updated_meta,
            }

            # Upsert project
            if project:
                execute(
                    """
                    UPDATE projects
                    SET title=%s, description=%s, team_members_json=%s
                    WHERE participant_id=%s
                    """,
                    [
                        project_title,
                        project_description,
                        json.dumps(updated_team_members_json),
                        app["user_id"],
                    ],
                )
            else:
                execute(
                    """
                    INSERT INTO projects (participant_id, title, description, team_members_json)
                    VALUES (%s,%s,%s,%s)
                    """,
                    [
                        app["user_id"],
                        project_title,
                        project_description,
                        json.dumps(updated_team_members_json),
                    ],
                )

            return redirect(f"/admin/applications/view?id={app_id}")

        # If error, keep form values on page
        app_data = {
            "location": location,
            "team_name": team_name,
            "university": university,
            "leader_name": leader_name,
            "leader_email": leader_email,
            "leader_mobile": leader_mobile,
        }
        app["status"] = status

        project = project or {}
        project["title"] = project_title
        project["description"] = project_description
        project_meta = {
            "category": category,
            "team_url": team_url,
            "video_link": video_link,
            "github_link": github_link,
            "data_sources": data_sources,
        }
        members = new_members

    # Prepare textarea JSON
    members_json_pretty = json.dumps(members, indent=2)

    # Render edit page
    page_ctx = {
        "app_id": str(app_id),

        "error": error,
        "error_box_class": "" if error else "hidden",

        "team_name": app_data.get("team_name", ""),
        "location": app_data.get("location", ""),
        "university": app_data.get("university", ""),
        "leader_name": app_data.get("leader_name", ""),
        "leader_email": app_data.get("leader_email", ""),
        "leader_mobile": app_data.get("leader_mobile", ""),

        "status_pending_selected": "selected" if (app.get("status") == "pending") else "",
        "status_approved_selected": "selected" if (app.get("status") == "approved") else "",
        "status_rejected_selected": "selected" if (app.get("status") == "rejected") else "",

        "project_title": (project.get("title") if project else "") or "",
        "project_description": (project.get("description") if project else "") or "",

        "category": project_meta.get("category", ""),
        "team_url": project_meta.get("team_url", ""),
        "video_link": project_meta.get("video_link", ""),
        "github_link": project_meta.get("github_link", ""),
        "data_sources": project_meta.get("data_sources", ""),

        "members_json": members_json_pretty,
    }

    return _render_admin(
        req,
        "Edit Application",
        "applications",
        "admin/application/edit.html",
        page_ctx,
    )


@login_required
@role_required("admin")
def admin_application_delete(req):
    app_id = req["query"]["id"]
    execute("DELETE FROM participant_applications WHERE id=%s", [app_id])
    return redirect("/admin/applications")

@login_required
@role_required("admin")
def admin_application_status(req):
    form, _ = get_form(req)

    app_id = form.get("id")
    status = form.get("status")

    if not app_id or status not in ("approved", "rejected", "pending"):
        return redirect("/admin/applications")

    execute(
        "UPDATE participant_applications SET status=%s WHERE id=%s",
        [status, app_id],
    )

    return redirect("/admin/applications")


@login_required
@role_required("admin")
def admin_applications_export(req):
    rows = query_all(
        "SELECT data_json, status FROM participant_applications ORDER BY created_at DESC"
    )

    lines = ["Team Name,Location,University,Status"]
    for r in rows:
        d = json.loads(r["data_json"])
        lines.append(
            f"{d.get('team_name','')},{d.get('location','')},{d.get('university','')},{r['status']}"
        )

    csv = "\n".join(lines)
    headers = [
        ("Content-Type", "text/csv"),
        ("Content-Disposition", "attachment; filename=applications.csv"),
    ]
    return "200 OK", headers, [csv.encode("utf-8")]


@login_required
@role_required("admin")
def admin_rooms(req):
    rooms = query_all("""
        SELECT
            r.id,
            r.name,
            r.status,
            SUM(CASE WHEN u.role='judge' THEN 1 ELSE 0 END) AS judge_count,
            SUM(CASE WHEN u.role='volunteer' THEN 1 ELSE 0 END) AS volunteer_count,
            COUNT(DISTINCT pr.projects_id) AS team_count
        FROM room r
        LEFT JOIN room_user ru ON ru.room_id = r.id
        LEFT JOIN users u ON u.id = ru.user_id
        LEFT JOIN project_room pr ON pr.room_id = r.id
        GROUP BY r.id
        ORDER BY r.id DESC
    """)

    rows_html = ""
    for r in rooms:
        rows_html += f"""
        <tr class="border-b border-slate-50">
          <td class="py-5 pl-4 font-bold">{r['name']}</td>
          <td class="py-5">{int(r['judge_count'] or 0)}</td>
          <td class="py-5">{int(r['volunteer_count'] or 0)}</td>
          <td class="py-5">{int(r['team_count'] or 0)}</td>
          <td class="py-5 pr-4 text-right space-x-3">
            <a href="/admin/rooms/assign?id={r['id']}" class="text-blue-600 font-bold text-xs hover:underline">Assign Teams</a>
            <a href="/admin/rooms/edit?id={r['id']}" class="text-orange-600 font-bold text-xs hover:underline">Edit</a>

            <form method="post" action="/admin/rooms/delete" class="inline"
                  onsubmit="return confirm('Delete this room and all related data?');">
              <input type="hidden" name="id" value="{r['id']}">
              <button class="text-red-600 font-bold text-xs hover:underline" type="submit">Delete</button>
            </form>
          </td>
        </tr>
        """

    if not rows_html:
        rows_html = """
        <tr><td class="py-8 text-slate-400 pl-4" colspan="5">No rooms found.</td></tr>
        """

    return _render_admin(
        req,
        "Location / Room",
        "rooms",
        "admin/room/index.html",
        {
            "rows": rows_html
        }
    )

@login_required
@role_required("admin")
def admin_room_create(req):
    error = ""

    judges = query_all("SELECT id, name, email FROM users WHERE role='judge' AND status='active' ORDER BY name")
    volunteers = query_all("SELECT id, name, email FROM users WHERE role='volunteer' AND status='active' ORDER BY name")

    if req["method"] == "POST":
        form, _ = get_form(req)

        name = (form.get("name") or "").strip()
        judge_ids = form.get("judge_ids") or []
        volunteer_ids = form.get("volunteer_ids") or []

        # parse_qs can return string or list
        if isinstance(judge_ids, str):
            judge_ids = [judge_ids]
        if isinstance(volunteer_ids, str):
            volunteer_ids = [volunteer_ids]

        if not name:
            error = "Room name is required."

        if not error:
            execute("INSERT INTO room (name, status) VALUES (%s, 'active')", [name])
            new_room = query_one("SELECT id FROM room ORDER BY id DESC LIMIT 1")
            room_id = new_room["id"]

            # insert room_user
            for uid in judge_ids + volunteer_ids:
                execute("INSERT IGNORE INTO room_user (user_id, room_id) VALUES (%s, %s)", [uid, room_id])

            # After create -> go to assign teams
            return redirect(f"/admin/rooms/assign?id={room_id}")

    # build checkbox lists
    judge_html = ""
    for u in judges:
        judge_html += f"""
        <label class="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-100">
          <input type="checkbox" name="judge_ids" value="{u['id']}" class="rounded">
          <div>
            <div class="text-sm font-bold text-slate-800">{u['name']}</div>
            <div class="text-xs text-slate-400">{u['email']}</div>
          </div>
        </label>
        """

    volunteer_html = ""
    for u in volunteers:
        volunteer_html += f"""
        <label class="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-100">
          <input type="checkbox" name="volunteer_ids" value="{u['id']}" class="rounded">
          <div>
            <div class="text-sm font-bold text-slate-800">{u['name']}</div>
            <div class="text-xs text-slate-400">{u['email']}</div>
          </div>
        </label>
        """

    return _render_admin(
        req,
        "Create Room",
        "rooms",
        "admin/room/create.html",
        {
            "error": error,
            "error_box_class": "" if error else "hidden",
            "judge_list": judge_html or "<div class='text-sm text-slate-400'>No active judges.</div>",
            "volunteer_list": volunteer_html or "<div class='text-sm text-slate-400'>No active volunteers.</div>",
            "name": "",
        }
    )

@login_required
@role_required("admin")
def admin_room_edit(req):
    room_id = req["query"].get("id")
    if not room_id:
        return redirect("/admin/rooms")

    room = query_one("SELECT id, name FROM room WHERE id=%s", [room_id])
    if not room:
        return redirect("/admin/rooms")

    assigned = query_all("SELECT user_id FROM room_user WHERE room_id=%s", [room_id])
    assigned_ids = set([str(x["user_id"]) for x in assigned])

    judges = query_all("SELECT id, name, email FROM users WHERE role='judge' AND status='active' ORDER BY name")
    volunteers = query_all("SELECT id, name, email FROM users WHERE role='volunteer' AND status='active' ORDER BY name")

    error = ""

    if req["method"] == "POST":
        form, _ = get_form(req)
        name = (form.get("name") or "").strip()

        judge_ids = form.get("judge_ids") or []
        volunteer_ids = form.get("volunteer_ids") or []

        if isinstance(judge_ids, str):
            judge_ids = [judge_ids]
        if isinstance(volunteer_ids, str):
            volunteer_ids = [volunteer_ids]

        if not name:
            error = "Room name is required."

        if not error:
            execute("UPDATE room SET name=%s WHERE id=%s", [name, room_id])

            # reset room_user for this room, then insert selected
            execute("DELETE FROM room_user WHERE room_id=%s", [room_id])
            for uid in judge_ids + volunteer_ids:
                execute("INSERT IGNORE INTO room_user (user_id, room_id) VALUES (%s, %s)", [uid, room_id])

            return redirect("/admin/rooms")

    # build checkbox lists with checked state
    judge_html = ""
    for u in judges:
        checked = "checked" if str(u["id"]) in assigned_ids else ""
        judge_html += f"""
        <label class="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-100">
          <input type="checkbox" name="judge_ids" value="{u['id']}" class="rounded" {checked}>
          <div>
            <div class="text-sm font-bold text-slate-800">{u['name']}</div>
            <div class="text-xs text-slate-400">{u['email']}</div>
          </div>
        </label>
        """

    volunteer_html = ""
    for u in volunteers:
        checked = "checked" if str(u["id"]) in assigned_ids else ""
        volunteer_html += f"""
        <label class="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-100">
          <input type="checkbox" name="volunteer_ids" value="{u['id']}" class="rounded" {checked}>
          <div>
            <div class="text-sm font-bold text-slate-800">{u['name']}</div>
            <div class="text-xs text-slate-400">{u['email']}</div>
          </div>
        </label>
        """

    return _render_admin(
        req,
        "Edit Room",
        "rooms",
        "admin/room/edit.html",
        {
            "room_id": str(room_id),
            "name": room["name"],
            "error": error,
            "error_box_class": "" if error else "hidden",
            "judge_list": judge_html or "<div class='text-sm text-slate-400'>No active judges.</div>",
            "volunteer_list": volunteer_html or "<div class='text-sm text-slate-400'>No active volunteers.</div>",
        }
    )

@login_required
@role_required("admin")
def admin_room_assign(req):
    room_id = req["query"].get("id")
    if not room_id:
        return redirect("/admin/rooms")

    room = query_one("SELECT id, name FROM room WHERE id=%s", [room_id])
    if not room:
        return redirect("/admin/rooms")

    # POST: assign selected projects
    if req["method"] == "POST":
        form, _ = get_form(req)
        project_ids = form.get("project_ids") or []
        if isinstance(project_ids, str):
            project_ids = [project_ids]

        for pid in project_ids:
            execute(
                "INSERT IGNORE INTO project_room (projects_id, room_id) VALUES (%s, %s)",
                [pid, room_id],
            )

        return redirect(f"/admin/rooms/assign?id={room_id}")

    # ✅ Assigned teams in this room
    assigned = query_all("""
        SELECT
            p.id AS project_id,
            p.title,
            pa.data_json
        FROM project_room pr
        JOIN projects p ON p.id = pr.projects_id
        JOIN participant_applications pa ON pa.user_id = p.participant_id
        WHERE pr.room_id = %s
        ORDER BY pr.id DESC
    """, [room_id])

    assigned_rows = ""
    for t in assigned:
        try:
            d = json.loads(t["data_json"] or "{}")
        except Exception:
            d = {}

        assigned_rows += f"""
        <div class="flex items-center justify-between p-4 bg-white rounded-2xl border border-slate-100">
          <div>
            <div class="font-black text-slate-900">{d.get('team_name','—')}</div>
            <div class="text-xs text-slate-500 mt-1">{t.get('title','—')}</div>
          </div>

          <form method="post" action="/admin/rooms/unassign"
                onsubmit="return confirm('Remove this team from the room?');">
            <input type="hidden" name="room_id" value="{room_id}">
            <input type="hidden" name="project_id" value="{t['project_id']}">
            <button type="submit"
              class="text-red-600 font-bold text-xs hover:underline">
              Remove
            </button>
          </form>
        </div>
        """

    if not assigned_rows:
        assigned_rows = "<div class='text-sm text-slate-400'>No teams assigned to this room yet.</div>"

    # ✅ Available approved + unassigned teams
    available = query_all("""
        SELECT
            p.id AS project_id,
            p.title,
            pa.data_json
        FROM participant_applications pa
        JOIN projects p ON p.participant_id = pa.user_id
        LEFT JOIN project_room pr ON pr.projects_id = p.id
        WHERE pa.status='approved'
          AND pr.id IS NULL
        ORDER BY p.id DESC
    """)

    available_rows = ""
    for t in available:
        try:
            d = json.loads(t["data_json"] or "{}")
        except Exception:
            d = {}

        available_rows += f"""
        <label class="flex items-start gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-100">
          <input type="checkbox" name="project_ids" value="{t['project_id']}" class="mt-1 rounded">
          <div class="flex-1">
            <div class="font-black text-slate-900">{d.get('team_name','—')}</div>
            <div class="text-xs text-slate-500 mt-1">{t.get('title','—')}</div>
          </div>
        </label>
        """

    if not available_rows:
        available_rows = "<div class='text-sm text-slate-400'>No approved unassigned teams available.</div>"

    return _render_admin(
        req,
        f"Assign Teams • {room['name']}",
        "rooms",
        "admin/room/assign.html",
        {
            "room_id": str(room_id),
            "room_name": room["name"],
            "assigned_rows": assigned_rows,
            "available_rows": available_rows,
        }
    )

@login_required
@role_required("admin")
def admin_room_delete(req):
    form, _ = get_form(req)
    room_id = form.get("id")
    if not room_id:
        return redirect("/admin/rooms")

    # delete related data first
    execute("DELETE FROM project_room WHERE room_id=%s", [room_id])
    execute("DELETE FROM room_user WHERE room_id=%s", [room_id])
    execute("DELETE FROM room WHERE id=%s", [room_id])

    return redirect("/admin/rooms")

@login_required
@role_required("admin")
def admin_room_unassign(req):
    form, _ = get_form(req)
    room_id = form.get("room_id")
    project_id = form.get("project_id")

    if room_id and project_id:
        execute(
            "DELETE FROM project_room WHERE room_id=%s AND projects_id=%s",
            [room_id, project_id],
        )

    return redirect(f"/admin/rooms/assign?id={room_id}")

@login_required
@role_required("admin")
def admin_judges_volunteers(req):
    role = (req["query"].get("role") or "").strip()   # judge / volunteer / ""
    status = (req["query"].get("status") or "").strip()  # active / inactive / ""
    q = (req["query"].get("q") or "").strip()

    where = "WHERE role IN ('judge','volunteer')"
    params = []

    if role in ("judge", "volunteer"):
        where += " AND role=%s"
        params.append(role)

    if status in ("active", "inactive"):
        where += " AND status=%s"
        params.append(status)

    if q:
        where += " AND (name LIKE %s OR email LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    users = query_all(
        f"""
        SELECT id, name, designation, organization, phone, email, role, status, created_at
        FROM users
        {where}
        ORDER BY created_at DESC
        """,
        params,
    )

    def badge_role(r):
        return "bg-blue-50 text-blue-600" if r == "judge" else "bg-purple-50 text-purple-600"

    def badge_status(s):
        return "bg-green-50 text-green-600" if s == "active" else "bg-slate-100 text-slate-600"

    rows = ""
    for u in users:
        toggle_to = "inactive" if u["status"] == "active" else "active"
        toggle_label = "Deactivate" if u["status"] == "active" else "Activate"
        toggle_color = "text-orange-600" if u["status"] == "active" else "text-green-600"

        rows += f"""
        <tr class="border-b border-slate-50">
          <td class="py-5 pl-4 font-bold text-slate-900">
            {u['name']}<br>
            <small class="text-xs text-slate-400">{u['designation'] or ''} , {u['organization'] or ''}</small>
          </td>
          <td class="py-5 text-slate-600">
            {u['email']}<br>
            <small class="text-xs text-slate-400">{u['phone'] or ''}</small>
          </td>
          <td class="py-5">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase {badge_role(u['role'])}">
              {u['role']}
            </span>
          </td>
          <td class="py-5">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase {badge_status(u['status'])}">
              {u['status']}
            </span>
          </td>
          <td class="py-5 pr-4 text-right space-x-3">

            <form method="post" action="/admin/judges-volunteers/status" class="inline">
              <input type="hidden" name="id" value="{u['id']}">
              <input type="hidden" name="status" value="{toggle_to}">
              <button type="submit" class="{toggle_color} font-black text-xs hover:underline">
                {toggle_label}
              </button>
            </form>

            <form method="post" action="/admin/judges-volunteers/delete" class="inline"
                  onsubmit="return confirm('Delete this user? This cannot be undone.');">
              <input type="hidden" name="id" value="{u['id']}">
              <button type="submit" class="text-red-600 font-black text-xs hover:underline">
                <i class="fa fa-trash" aria-hidden="true"></i>
              </button>
            </form>

          </td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='5' class='py-10 pl-4 text-slate-400'>No users found.</td></tr>"

    return _render_admin(
        req,
        "Judge & Volunteer",
        "jv",
        "admin/judges_volunteers/index.html",
        {
            "rows": rows,
            "q": q,
            "role_judge_selected": "selected" if role == "judge" else "",
            "role_volunteer_selected": "selected" if role == "volunteer" else "",
            "status_active_selected": "selected" if status == "active" else "",
            "status_inactive_selected": "selected" if status == "inactive" else "",
        },
    )


@login_required
@role_required("admin")
def admin_jv_toggle_status(req):
    form, _ = get_form(req)
    user_id = form.get("id")
    new_status = (form.get("status") or "").strip()

    if user_id and new_status in ("active", "inactive"):
        execute("UPDATE users SET status=%s WHERE id=%s AND role IN ('judge','volunteer')", [new_status, user_id])

    return redirect("/admin/judges-volunteers")


@login_required
@role_required("admin")
def admin_jv_delete(req):
    form, _ = get_form(req)
    user_id = form.get("id")

    if user_id:
        # users deletion will cascade sessions/evaluations due to FK in your schema
        execute("DELETE FROM users WHERE id=%s AND role IN ('judge','volunteer')", [user_id])

    return redirect("/admin/judges-volunteers")

# ----------------------------
# Helpers
# ----------------------------
def _safe_json(val, default):
    try:
        return json.loads(val) if val else default
    except Exception:
        return default

def _to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)

def _has_female_member(team_members_json: str) -> bool:
    payload = _safe_json(team_members_json, {})
    members = payload.get("members", []) or []
    for m in members:
        if (m.get("gender") or "").lower() == "female":
            return True
    return False


# ----------------------------
# GET /admin/results
# ----------------------------
@login_required
@role_required("admin")
def admin_results_index(req):
    q = req["query"]
    msg = (q.get("msg") or "").strip()

    search = (q.get("q") or "").strip()
    min_score = (q.get("min") or "").strip()
    max_score = (q.get("max") or "").strip()
    scored = (q.get("scored") or "").strip()  # yes / no / ""

    where = "WHERE 1=1"
    params = []

    if scored == "yes":
        where += " AND pa.final_score IS NOT NULL"
    elif scored == "no":
        where += " AND pa.final_score IS NULL"

    if min_score:
        where += " AND pa.final_score >= %s"
        params.append(min_score)

    if max_score:
        where += " AND pa.final_score <= %s"
        params.append(max_score)

    if search:
        # search inside JSON text (simple + works with your schema)
        where += " AND pa.data_json LIKE %s"
        params.append(f"%{search}%")

    rows = query_all(f"""
        SELECT pa.id, pa.final_score, pa.data_json
        FROM participant_applications pa
        {where}
        ORDER BY (pa.final_score IS NULL), pa.final_score DESC, pa.id DESC
        LIMIT 300
    """, params)

    table_rows = ""
    for r in rows:
        data = _safe_json(r.get("data_json"), {})
        team = data.get("team_name", "—")
        leader_name = data.get("leader_name", "—")
        leader_email = data.get("leader_email", "—")
        leader_mobile = data.get("leader_mobile", "—")
        location = data.get("location", "—")
        university = data.get("university", "—")

        score = r.get("final_score")
        score_text = "—" if score is None else str(score)

        table_rows += f"""
        <tr class="border-b border-slate-50">
          <td class="py-5 pl-4 font-bold">{r['id']}</td>
          <td class="py-5">
            <div class="font-black text-slate-900">{team}</div>
            <div class="text-xs text-slate-500 mt-1">{location} • {university}</div>
          </td>
          <td class="py-5">
            <div class="font-bold text-slate-800">{leader_name}</div>
            <div class="text-xs text-slate-500 mt-1">{leader_email}</div>
            <div class="text-xs text-slate-500">{leader_mobile}</div>
          </td>
          <td class="py-5 font-black text-slate-900">{score_text}</td>
        </tr>
        """

    if not table_rows:
        table_rows = "<tr><td colspan='4' class='py-10 pl-4 text-slate-400'>No results found.</td></tr>"

    # keep selected states
    scored_yes_selected = "selected" if scored == "yes" else ""
    scored_no_selected = "selected" if scored == "no" else ""

    return _render_admin(
        req,
        "Result Evaluation",
        "result", 
        "admin/result/index.html",
        {
            "msg": msg,
            "msg_box_class": "" if msg else "hidden",

            "rows": table_rows,

            # filter values
            "q": search,
            "min": min_score,
            "max": max_score,
            "scored_yes_selected": scored_yes_selected,
            "scored_no_selected": scored_no_selected,
        }
    )

# ----------------------------
# POST /admin/results/process
# ----------------------------
@login_required
@role_required("admin")
def admin_results_process(req):
    # Button press => calculate in real time
    form, _ = get_form(req)

    # ----------------------------
    # STEP 1: Normalize per judge
    # ----------------------------
    # For each judge, compute max for each segment and scale to 20.
    max_rows = query_all("""
        SELECT
          user_id,
          MAX(influence) AS max_influence,
          MAX(creativity) AS max_creativity,
          MAX(validity) AS max_validity,
          MAX(relevance) AS max_relevance,
          MAX(presentation) AS max_presentation
        FROM make_scores
        GROUP BY user_id
    """)

    for m in max_rows:
        uid = m["user_id"]
        r_inf = 20.0 / float(m["max_influence"]) if m["max_influence"] and float(m["max_influence"]) > 0 else 0.0
        r_cre = 20.0 / float(m["max_creativity"]) if m["max_creativity"] and float(m["max_creativity"]) > 0 else 0.0
        r_val = 20.0 / float(m["max_validity"]) if m["max_validity"] and float(m["max_validity"]) > 0 else 0.0
        r_rel = 20.0 / float(m["max_relevance"]) if m["max_relevance"] and float(m["max_relevance"]) > 0 else 0.0
        r_pre = 20.0 / float(m["max_presentation"]) if m["max_presentation"] and float(m["max_presentation"]) > 0 else 0.0

        # update all marks for this judge in one query
        execute("""
            UPDATE make_scores
            SET
              round_influence    = influence    * %s,
              round_creativity   = creativity   * %s,
              round_validity     = validity     * %s,
              round_relevance    = relevance    * %s,
              round_presentation = presentation * %s
            WHERE user_id = %s
        """, [r_inf, r_cre, r_val, r_rel, r_pre, uid])

    # ----------------------------
    # STEP 2: Compute team final_score
    # ----------------------------
    # Get average normalized marks per registration
    avg_rows = query_all("""
        SELECT
          registration_id,
          AVG(round_influence)    AS avg_influence,
          AVG(round_creativity)   AS avg_creativity,
          AVG(round_validity)     AS avg_validity,
          AVG(round_relevance)    AS avg_relevance,
          AVG(round_presentation) AS avg_presentation,
          COUNT(*) AS judge_count
        FROM make_scores
        GROUP BY registration_id
    """)
    avg_map = {str(r["registration_id"]): r for r in avg_rows}

    # Iterate all registrations (participant_applications)
    regs = query_all("SELECT id, user_id, status FROM participant_applications")

    updated = 0
    cleared = 0

    for reg in regs:
        reg_id = str(reg["id"])
        avg = avg_map.get(reg_id)

        # If no marks => final_score = NULL
        if not avg or int(avg.get("judge_count") or 0) <= 0:
            execute("UPDATE participant_applications SET final_score=NULL WHERE id=%s", [reg["id"]])
            cleared += 1
            continue

        # base = sum of averages
        final_score = (
            _to_float(avg.get("avg_influence")) +
            _to_float(avg.get("avg_creativity")) +
            _to_float(avg.get("avg_validity")) +
            _to_float(avg.get("avg_relevance")) +
            _to_float(avg.get("avg_presentation"))
        )

        # Add extra project_meta scores from projects.team_members_json
        proj = query_one("""
            SELECT team_members_json
            FROM projects
            WHERE participant_id=%s
        """, [reg["user_id"]])

        team_members_json = proj.get("team_members_json") if proj else None
        payload = _safe_json(team_members_json, {})
        meta = (payload.get("project_meta") or {}) if isinstance(payload, dict) else {}

        final_score += _to_float(meta.get("team_work_score"), 0)
        final_score += _to_float(meta.get("user_experience_score"), 0)
        final_score += _to_float(meta.get("is_nasa_data_usage_score"), 0)
        final_score += _to_float(meta.get("is_challenge_category_score"), 0)
        final_score += _to_float(meta.get("id_project_link_score"), 0)
        final_score += _to_float(meta.get("is_nasa_global_team_url_score"), 0)

        # 5% bonus if any female member exists
        if team_members_json and _has_female_member(team_members_json):
            final_score += (final_score * 5.0) / 100.0

        final_score = round(final_score, 2)

        execute("UPDATE participant_applications SET final_score=%s WHERE id=%s", [final_score, reg["id"]])
        updated += 1

    return redirect(f"/admin/results?msg=Final scores processed. Updated={updated}, Cleared={cleared}")


@login_required
@role_required("admin")
def admin_results_export(req):
    q = req["query"]

    search = (q.get("q") or "").strip()
    min_score = (q.get("min") or "").strip()
    max_score = (q.get("max") or "").strip()
    scored = (q.get("scored") or "").strip()

    where = "WHERE 1=1"
    params = []

    if scored == "yes":
        where += " AND pa.final_score IS NOT NULL"
    elif scored == "no":
        where += " AND pa.final_score IS NULL"

    if min_score:
        where += " AND pa.final_score >= %s"
        params.append(min_score)

    if max_score:
        where += " AND pa.final_score <= %s"
        params.append(max_score)

    if search:
        where += " AND pa.data_json LIKE %s"
        params.append(f"%{search}%")

    rows = query_all(f"""
        SELECT pa.id, pa.final_score, pa.data_json
        FROM participant_applications pa
        {where}
        ORDER BY pa.id DESC
    """, params)

    def safe_json(val):
        try:
            return json.loads(val) if val else {}
        except Exception:
            return {}

    def csv_escape(s):
        s = "" if s is None else str(s)
        s = s.replace('"', '""')
        return f'"{s}"'

    header = [
        "registration_id", "final_score",
        "team_name", "location", "university",
        "leader_name", "leader_email", "leader_mobile"
    ]
    lines = [",".join(header)]

    for r in rows:
        data = safe_json(r.get("data_json"))
        line = [
            csv_escape(r.get("id")),
            csv_escape(r.get("final_score") if r.get("final_score") is not None else ""),
            csv_escape(data.get("team_name", "")),
            csv_escape(data.get("location", "")),
            csv_escape(data.get("university", "")),
            csv_escape(data.get("leader_name", "")),
            csv_escape(data.get("leader_email", "")),
            csv_escape(data.get("leader_mobile", "")),
        ]
        lines.append(",".join(line))

    csv_data = "\n".join(lines)
    headers = [
        ("Content-Type", "text/csv; charset=utf-8"),
        ("Content-Disposition", "attachment; filename=final_results.csv"),
    ]
    return "200 OK", headers, [csv_data.encode("utf-8")]