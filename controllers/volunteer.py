#   """
#   NSAC Competition Management System - Volunteer Controller

#   This module handles volunteer-specific functionality including dashboard access
#   and viewing assigned tasks and room information.
#   """

import json
from auth.decorators import login_required, role_required
from utils.response import response, render_partial, render_with_layout, render_html, redirect
from utils.form import get_form
from db.database import query_all, query_one, execute

JUDGE_EXTRA_HEAD = """
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

def _judge_base(user, page_title: str):
    return {
        "title": "Volunteer | NASA Space Apps BD",
        "extra_head": JUDGE_EXTRA_HEAD,
        "page_title": page_title,
        "judge_name": user.get("name", "Volunteer"),
        "judge_role_label": "Volunteer",
        "judge_avatar_url": f"https://ui-avatars.com/api/?name={user.get('name', 'Volunteer')}&background=2563EB&color=fff",
        "nav_dashboard_active": "",
        "nav_inactive": "text-slate-500 hover:bg-slate-50 hover:text-blue-600",
    }

def _judge_set_active(ctx, active: str):
    if active == "dashboard":
        ctx["nav_dashboard_active"] = "active"

def _render_judge(req, page_title: str, active: str, page_tpl: str, page_ctx: dict):
    user = req["user"]
    base = _judge_base(user, page_title)
    _judge_set_active(base, active)

    content_html = render_partial(page_tpl, page_ctx)
    judge_full = render_with_layout("volunteer/layout.html", content_html, base)

    final_html = render_html(
        judge_full,
        title=base.get("title", "Volunteer"),
        extra_head=base.get("extra_head", ""),
    )
    return response(final_html.encode("utf-8"))

def _safe_json(val, default):
    try:
        return json.loads(val) if val else default
    except Exception:
        return default

def _options(min_value: int, selected: int):
    # dropdown 1-20, but if already marked => min_value = previous score
    html = ""
    for v in range(min_value, 21):
        sel = "selected" if v == selected else ""
        html += f'<option value="{v}" {sel}>{v}</option>'
    return html

@login_required
@role_required("volunteer")
def volunteer_dashboard(req):
    judge_id = req["user"]["id"]

    # Teams assigned to judge via room_user -> project_room -> projects -> participant_applications
    teams = query_all("""
        SELECT
            pa.id AS registration_id,
            p.id AS project_id,
            pa.data_json,
            ms.id AS marked_id
        FROM room_user ru
        JOIN project_room pr ON pr.room_id = ru.room_id
        JOIN projects p ON p.id = pr.projects_id
        JOIN participant_applications pa ON pa.user_id = p.participant_id
        LEFT JOIN make_scores ms
            ON ms.user_id = ru.user_id AND ms.registration_id = pa.id
        WHERE ru.user_id = %s
        GROUP BY pa.id, p.id, pa.data_json, ms.id
        ORDER BY pa.id DESC
    """, [judge_id])

    rows = ""
    for t in teams:
        data = _safe_json(t.get("data_json"), {})
        team_label = str(t["registration_id"])  # as you requested: show only id

        rows += f"""
        <tr class="border-b border-slate-50">
          <td class="py-5 pl-4 font-bold">{team_label}</td>
          <td class="py-5">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase bg-green-50 text-green-600">
              Qualified team
            </span>
          </td>
          <td class="py-5 pr-4 text-right">
            <a class="text-blue-600 font-black text-xs hover:underline"
               href="/volunteer/view?id={t['registration_id']}">
              View
            </a>
          </td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='3' class='py-10 pl-4 text-slate-400'>No assigned teams found.</td></tr>"

    msg = (req["query"].get("msg") or "").strip()

    return _render_judge(
        req,
        "Assigned Teams",
        "dashboard",
        "volunteer/dashboard.html",
        {
            "rows": rows,
            "msg": msg,
            "msg_box_class": "" if msg else "hidden",
        },
    )

@login_required
@role_required("volunteer")
def volunteer_view(req):
    judge_id = req["user"]["id"]
    reg_id = req["query"].get("id")
    if not reg_id:
        return redirect("/volunteer/dashboard")

    # Ensure this registration_id is actually assigned to this judge
    allowed = query_one("""
        SELECT pa.id
        FROM room_user ru
        JOIN project_room pr ON pr.room_id = ru.room_id
        JOIN projects p ON p.id = pr.projects_id
        JOIN participant_applications pa ON pa.user_id = p.participant_id
        WHERE ru.user_id=%s AND pa.id=%s
        LIMIT 1
    """, [judge_id, reg_id])
    if not allowed:
        return redirect("/volunteer/dashboard?msg=Not allowed")

    pa = query_one("SELECT id, data_json FROM participant_applications WHERE id=%s", [reg_id])
    if not pa:
        return redirect("/volunteer/dashboard?msg=Not found")
    app_data = _safe_json(pa.get("data_json"), {})

    # Project (by participant_id=user_id)
    p = query_one("""
        SELECT id, participant_id, title, description, team_members_json
        FROM projects
        WHERE participant_id = (SELECT user_id FROM participant_applications WHERE id=%s)
    """, [reg_id])

    project_title = p.get("title") if p else "—"
    project_desc = p.get("description") if p else "—"
    meta = {}
    members_json = {}
    if p:
        members_json = _safe_json(p.get("team_members_json"), {})
        meta = members_json.get("project_meta", {}) or {}

    category = meta.get("category", "—")
    video_link = meta.get("video_link", "")
    github_link = meta.get("github_link", "")
    team_url = meta.get("team_url", "")

    # Existing score
    score = query_one("""
        SELECT * FROM make_scores
        WHERE user_id=%s AND registration_id=%s
    """, [judge_id, reg_id])

    def prev(field, default=1):
        return int(score.get(field)) if score and score.get(field) else default

    # If already scored, min value must be the previously saved score
    min_influence = prev("influence", 1)
    min_creativity = prev("creativity", 1)
    min_validity = prev("validity", 1)
    min_relevance = prev("relevance", 1)
    min_presentation = prev("presentation", 1)

    page_ctx = {
        "registration_id": str(reg_id),
        "team_name": app_data.get("team_name", "—"),
        "project_title": project_title,
        "project_category": category,
        "project_description": project_desc,

        "video_link": video_link or "#",
        "github_link": github_link or "#",
        "team_url": team_url or "#",

        "is_marked_checked": "checked" if score else "",
        "confirm_checked": "checked" if score else "",

        "opt_influence": _options(min_influence, prev("influence", min_influence)),
        "opt_creativity": _options(min_creativity, prev("creativity", min_creativity)),
        "opt_validity": _options(min_validity, prev("validity", min_validity)),
        "opt_relevance": _options(min_relevance, prev("relevance", min_relevance)),
        "opt_presentation": _options(min_presentation, prev("presentation", min_presentation)),
    }

    return _render_judge(
        req,
        f"Score Team #{reg_id}",
        "dashboard",
        "volunteer/view.html",
        page_ctx,
    )