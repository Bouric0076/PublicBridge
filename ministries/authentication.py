"""
Custom authentication backend for Ministry users.
This provides a unified authentication system that works alongside Django's default authentication.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Ministry

class MinistryAuthBackend(BaseBackend):
    """
    Custom authentication backend for Ministry users.
    Allows Ministry users to authenticate using email and password.
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Authenticate a ministry user using email and password.
        """
        if email is None or password is None:
            return None
        
        try:
            ministry = Ministry.objects.get(email=email)
            if ministry.check_password(password):
                return ministry
        except Ministry.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        """
        Retrieve a ministry user by ID.
        """
        try:
            return Ministry.objects.get(pk=user_id)
        except Ministry.DoesNotExist:
            return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Ministry users have specific permissions.
        """
        if not isinstance(user_obj, Ministry):
            return False
        
        # Ministry users can manage their own reports
        if perm == "ministries.can_manage_reports":
            return True
        
        return False