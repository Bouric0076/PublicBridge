
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('health-check/', views.health_check, name='health_check'),

]
