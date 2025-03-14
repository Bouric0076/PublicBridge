"""
URL configuration for PublicBridge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
# from django.contrib import admin_dashboard


urlpatterns = [
    path('grappelli/', include('grappelli.urls')),

    path( 'admin/', admin.site.urls),

    path( 'administrator/', include('GovernmentAdmin.urls')),
   path('', include('main.urls')),
    path('reports/', include('reports.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('users/', include('users.urls')),  # Users app URLs
    path('forum/', include('forum.urls', namespace='forum')),
    path('geotagging/', include('disaster_reporting.urls')),

    path("ministries/", include("ministries.urls")),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
