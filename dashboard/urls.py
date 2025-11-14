from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

# Dashboard Overview
    path('dashboard_overview/', views.dashboard_overview, name='dashboard_overview'),

    # Government Admin Views
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('toggle-department/<int:department_id>/', views.toggle_department_status, name='toggle_department_status'),

    # Report Management Views
    path('manage-reports/', views.manage_reports, name='manage_reports'),
    path('assign-report/<int:report_id>/<int:department_id>/', views.assign_report_to_department, name='assign_report_to_department'),
    path('export-reports/', views.export_reports_to_csv, name='export_reports_to_csv'),

    # Citizen and Profile Management Views
    path('manage-citizens/', views.manage_citizens, name='manage_citizens'),

    # Polls and Feedback Views
    path('manage-polls/', views.manage_polls, name='manage_polls'),
    path('manage-feedback/', views.manage_feedback, name='manage_feedback'),

    # Notifications and Messages Views
    path('manage-notifications/', views.manage_notifications, name='manage_notifications'),
    path('manage-messages/', views.manage_messages, name='manage_messages'),

    # Custom Analytics View
    path('analytics/', views.analytics_view, name='analytics_view'),

    # AI-Powered Dashboard URLs
    path('ai-dashboard/', views.ai_dashboard, name='ai_dashboard'),
    path('ai-report-analysis/<int:report_id>/', views.ai_report_analysis, name='ai_report_analysis'),
    path('ai-predictive-insights/', views.ai_predictive_insights, name='ai_predictive_insights'),
    path('ai-chatbot/', views.ai_chatbot_interface, name='ai_chatbot_interface'),
    path('chatbot-api/', views.chatbot_api, name='chatbot_api'),
    
    # Citizen AI Features
    path('citizen-ai-dashboard/', views.citizen_ai_dashboard, name='citizen_ai_dashboard'),
    path('ai-recommendations/', views.citizen_ai_recommendations, name='ai_recommendations'),
    path('ai-chat/', views.ai_chat_page, name='ai_chat_page'),
    path('ai-status/', views.ai_status_api, name='ai_status_api'),
]
