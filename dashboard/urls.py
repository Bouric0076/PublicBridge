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
]
