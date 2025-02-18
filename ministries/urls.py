from django.urls import path
from .views import (
    register_ministry,
    success_view,
    ministry_dashboard,
    update_report_status,
    assigned_reports,
    resolved_reports,
    report_details, login_ministry, logout_ministry,
)

urlpatterns = [
    path("register/", register_ministry, name="register-ministry"),
    path("success/", success_view, name="success"),
    path("login/", login_ministry, name="ministry-login"),
    path("logout/", logout_ministry, name="ministry-logout"),
    path("dashboard/", ministry_dashboard, name="ministry-dashboard"),
    path("assigned-reports/", assigned_reports, name="assigned-reports"),
    path("resolved-reports/", resolved_reports, name="resolved-reports"),
    path("report/<uuid:report_id>/", report_details, name="report-details"),
    path("update/<uuid:report_id>/", update_report_status, name="update-report-status"),
]
