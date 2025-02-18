from django.urls import path
from . import views
from .views import view_pending_ministries, approve_ministry, view_reports, assign_report, govadmin_dashboard, \
    manage_ministries, assign_report_list

urlpatterns = [

    path("dashboard/", govadmin_dashboard, name="govadmin_dashboard"),
    path("pending/", view_pending_ministries, name="view-pending-ministries"),
    path("approve/<uuid:ministry_id>/", approve_ministry, name="approve-ministry"),

    path("reports/", view_reports, name="view-reports"),

    path("assign/", assign_report_list, name="assign_reports"),
    path("assign/<uuid:report_id>/", assign_report, name="assign-report"),

    path("manage-ministries/", manage_ministries, name="manage_ministries"),
]
