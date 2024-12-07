from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_report, name='submit_report'),
    path('user_reports/', views.user_reports, name='user_reports'),
    path('submit_userreport/', views.submit_userreport, name='submit_userreport'),
]
