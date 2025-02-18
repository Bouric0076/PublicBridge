from django.core.exceptions import PermissionDenied
from functools import wraps

def government_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "GovernmentAdmin":
            raise PermissionDenied  # Returns a 403 Forbidden error
        return view_func(request, *args, **kwargs)
    return _wrapped_view
