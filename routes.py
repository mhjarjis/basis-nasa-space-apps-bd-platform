#   """
#   NSAC Competition Management System - Routing Module

#   This module defines all URL routes for the application, mapping HTTP methods and paths
#   to their corresponding controller handlers. Routes are organized by user roles.
#   """

from controllers.public import home,portal_login_get,portal_login_post,portal_register_get,portal_register_post, login_get, login_post, register_get, register_post, logout
from controllers.participant import participant_dashboard, save_team_members, save_project
from controllers.admin import admin_dashboard,admin_applications,admin_application_view,admin_application_edit,admin_application_delete,admin_application_status,admin_applications_export,admin_rooms,admin_room_create,admin_room_edit,admin_room_assign,admin_room_delete,admin_room_unassign, admin_judges_volunteers,admin_jv_toggle_status,admin_jv_delete,admin_results_index,admin_results_process,admin_results_export
from controllers.judge import judge_dashboard, judge_score_view, judge_score_submit
from controllers.volunteer import volunteer_dashboard,volunteer_view

# List of routes as tuples: (HTTP_METHOD, PATH, HANDLER_FUNCTION)
ROUTES = [
    ("GET",  "/", home),
    ("GET",  "/login", login_get),
    ("POST", "/login", login_post),
    ("GET",  "/register", register_get),
    ("POST", "/register", register_post),
    ("GET",  "/logout", logout),

    # Participant Routes
    ("GET",  "/participant/dashboard", participant_dashboard),
    ("POST", "/participant/team-members", save_team_members),
    ("POST", "/participant/project", save_project),

    # Admin Routes
    ("GET", "/portal-login", portal_login_get),
    ("POST", "/portal-login", portal_login_post),
    ("GET",  "/portal-register", portal_register_get),
    ("POST", "/portal-register", portal_register_post),
    ("GET", "/admin/dashboard", admin_dashboard),    
    #applications
    ("GET", "/admin/applications", admin_applications),
    ("GET",  "/admin/applications/view", admin_application_view),
    ("GET",  "/admin/applications/edit", admin_application_edit),
    ("POST", "/admin/applications/edit", admin_application_edit),
    ("GET",  "/admin/applications/delete", admin_application_delete),
    ("POST", "/admin/applications/status", admin_application_status),
    ("GET",  "/admin/applications/export", admin_applications_export),
    #rooms
    ("GET",  "/admin/rooms", admin_rooms),
    ("GET",  "/admin/rooms/create", admin_room_create),
    ("POST", "/admin/rooms/create", admin_room_create),
    ("GET",  "/admin/rooms/edit", admin_room_edit),
    ("POST", "/admin/rooms/edit", admin_room_edit),
    ("GET",  "/admin/rooms/assign", admin_room_assign),
    ("POST", "/admin/rooms/assign", admin_room_assign),
    ("POST", "/admin/rooms/delete", admin_room_delete),
    ("POST", "/admin/rooms/unassign", admin_room_unassign),
    #judges & volunteers
    ("GET",  "/admin/judges-volunteers", admin_judges_volunteers),
    ("POST", "/admin/judges-volunteers/status", admin_jv_toggle_status),
    ("POST", "/admin/judges-volunteers/delete", admin_jv_delete),
    # results
    ("GET",  "/admin/results", admin_results_index),
    ("POST", "/admin/results/process", admin_results_process),
    ("GET",  "/admin/results/export", admin_results_export),

    #Judge Routes
    ("GET",  "/judge/dashboard", judge_dashboard),
    ("GET",  "/judge/score", judge_score_view),
    ("POST", "/judge/score", judge_score_submit),


    # Volunteer Routes
    ("GET",  "/volunteer/dashboard", volunteer_dashboard),
    ("GET",  "/volunteer/view", volunteer_view),

]
