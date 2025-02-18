from django.urls import path
from . import views
from .views import government_admin_login

urlpatterns = [
    path("admin-login/", government_admin_login, name="govadmin_login"),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
]
