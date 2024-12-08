from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_report, name='submit_report'),
    path('reports/<int:report_id>/', views.report_details, name='report_details'),
    path('reports/', views.user_reports, name='user_reports'),
    path('submit_userreport/', views.submit_userreport, name='submit_userreport'),
    path('report/edit/<int:report_id>/', views.edit_report, name='edit_report'),
    path('report/delete/<int:report_id>/', views.delete_report, name='delete_report'),
]
