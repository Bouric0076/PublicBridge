from django.urls import path, include
from . import views
from .views import view_pending_ministries, approve_ministry, view_reports, assign_report, govadmin_dashboard, \
    manage_ministries, assign_report_list
from .views import disaster_dashboard, admin_dashboard

from rest_framework.routers import DefaultRouter
from .views import DisasterReportViewSet

router = DefaultRouter()
router.register(r'disaster-reports', DisasterReportViewSet)

urlpatterns = [
    path("dashboard/", govadmin_dashboard, name="govadmin_dashboard"),
    path("pending/", view_pending_ministries, name="view-pending-ministries"),
    path("approve/<uuid:ministry_id>/", approve_ministry, name="approve-ministry"),
    path("reports/", view_reports, name="view-reports"),
    path("assign/", assign_report_list, name="assign_reports"),
    path("assign/<uuid:report_id>/", assign_report, name="assign-report"),
    path("manage-ministries/", manage_ministries, name="manage_ministries"),
    path("geotagged-report/", admin_dashboard, name="admin_dashboard"),
    path('api/', include(router.urls)),
]