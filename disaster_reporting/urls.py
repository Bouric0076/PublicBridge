from django.urls import path
from django.views.generic import View

urlpatterns = [
    path("api/reports/", "disaster_reporting.views.DisasterReportListCreateView".as_view(), name="report-list-create"),
    path("api/reports/<int:pk>/", "disaster_reporting.views.DisasterReportDetailView".as_view(), name="report-detail"),
    path("api/reports/<int:pk>/invalid/", "disaster_reporting.views.MarkReportInvalidView".as_view(), name="mark-invalid"),
    path("api/reports/<int:pk>/archive/", "disaster_reporting.views.ArchiveReportView".as_view(), name="archive-report"),
    path("api/agencies/", "disaster_reporting.views.DisasterAgencyListView".as_view(), name="agency-list"),
    path("", "disaster_reporting.views.live_alerts", name="live_alerts"),
]