from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet

# Initialize the DefaultRouter and register the viewset
router = DefaultRouter()
router.register(r"reports", ReportViewSet, basename="report")

urlpatterns = [
    path("api/", include(router.urls)),
    path('submit/', views.submit_report, name='submit_report'),
    path('reports/<int:report_id>/', views.report_details, name='report_details'),
    path('reports/', views.user_reports, name='user_reports'),
    path('submit_anonymous_report/', views.submit_anonymous_report, name='submit_anonymous_report'),
    path('report/edit/<int:report_id>/', views.edit_report, name='edit_report'),
    path('report/delete/<int:report_id>/', views.delete_report, name='delete_report'),
]
