from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet
from .ai_api_views import (
    AIReportListView, AIReportDetailView, AIUserListView, AIUserDetailView,
    process_reports_with_ai, get_ai_dashboard_stats, get_ai_recommendations,
    chatbot_api, advanced_analysis_api, get_ai_capabilities
)

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
    
    # AI API endpoints
    path('api/ai/reports/', AIReportListView.as_view(), name='ai_report_list'),
    path('api/ai/reports/<int:pk>/', AIReportDetailView.as_view(), name='ai_report_detail'),
    path('api/ai/users/', AIUserListView.as_view(), name='ai_user_list'),
    path('api/ai/users/<int:pk>/', AIUserDetailView.as_view(), name='ai_user_detail'),
    path('api/ai/reports/process/', process_reports_with_ai, name='process_reports_with_ai'),
    path('api/ai/dashboard/stats/', get_ai_dashboard_stats, name='ai_dashboard_stats'),
    path('api/ai/recommendations/', get_ai_recommendations, name='ai_recommendations'),
    
    # New Llama-based AI endpoints
    path('api/ai/chatbot/', chatbot_api, name='chatbot_api'),
    path('api/ai/advanced-analysis/', advanced_analysis_api, name='advanced_analysis_api'),
    path('api/ai/capabilities/', get_ai_capabilities, name='get_ai_capabilities'),
]
