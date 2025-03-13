from django.urls import path
from .views import (
    DisasterReportListCreateView, DisasterReportDetailView,
    MarkReportInvalidView, ArchiveReportView, DisasterAgencyListView, live_alerts
)

urlpatterns = [
    path("api/reports/", DisasterReportListCreateView.as_view(), name="report-list-create"),
    path("api/reports/<int:pk>/", DisasterReportDetailView.as_view(), name="report-detail"),
    path("api/reports/<int:pk>/invalid/", MarkReportInvalidView.as_view(), name="mark-invalid"),
    path("api/reports/<int:pk>/archive/", ArchiveReportView.as_view(), name="archive-report"),
    path("api/agencies/", DisasterAgencyListView.as_view(), name="agency-list"),
     path("", live_alerts, name="live_alerts"),
]
