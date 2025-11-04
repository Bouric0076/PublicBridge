from django.db import models
from django.contrib.auth import get_user_model
from reports.models import Report
from ministries.models import Ministry
from users.models import GovernmentAdmin

User = get_user_model()

class DashboardMetric(models.Model):
    """Store dashboard metrics and statistics for caching purposes."""
    
    METRIC_TYPES = [
        ('total_reports', 'Total Reports'),
        ('pending_reports', 'Pending Reports'),
        ('resolved_reports', 'Resolved Reports'),
        ('active_ministries', 'Active Ministries'),
        ('active_users', 'Active Users'),
        ('reports_by_category', 'Reports by Category'),
        ('reports_by_priority', 'Reports by Priority'),
        ('avg_resolution_time', 'Average Resolution Time'),
    ]
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    value = models.JSONField(default=dict)  # Store complex data like counts, percentages, etc.
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-calculated_at']
        
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.calculated_at}"


class DashboardWidget(models.Model):
    """Configurable dashboard widgets for different user roles."""
    
    WIDGET_TYPES = [
        ('stats_card', 'Statistics Card'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('map', 'Map View'),
        ('timeline', 'Timeline'),
        ('activity_feed', 'Activity Feed'),
    ]
    
    USER_ROLES = [
        ('government_admin', 'Government Admin'),
        ('ministry', 'Ministry'),
        ('citizen', 'Citizen'),
        ('all', 'All Users'),
    ]
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='all')
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)  # Store widget configuration (filters, display options, etc.)
    
    class Meta:
        ordering = ['role', 'position']
        
    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class DashboardAlert(models.Model):
    """System alerts and notifications for dashboard users."""
    
    ALERT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES, default='info')
    is_active = models.BooleanField(default=True)
    show_to_all = models.BooleanField(default=False)
    target_roles = models.JSONField(default=list)  # List of roles to show alert to
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class SystemHealth(models.Model):
    """Monitor system health and performance metrics."""
    
    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('degraded', 'Degraded Performance'),
        ('partial_outage', 'Partial Outage'),
        ('major_outage', 'Major Outage'),
    ]
    
    component = models.CharField(max_length=100, unique=True)  # e.g., 'database', 'file_upload', 'email_service'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    last_check = models.DateTimeField(auto_now=True)
    details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['component']
        
    def __str__(self):
        return f"{self.component}: {self.get_status_display()}"


class DashboardActivity(models.Model):
    """Track dashboard activities for audit and user activity feeds."""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('report_view', 'Report Viewed'),
        ('report_update', 'Report Updated'),
        ('report_assign', 'Report Assigned'),
        ('ministry_approve', 'Ministry Approved'),
        ('ministry_reject', 'Ministry Rejected'),
        ('alert_dismiss', 'Alert Dismissed'),
        ('export_data', 'Data Exported'),
        ('widget_configure', 'Widget Configured'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ministry = models.ForeignKey(Ministry, on_delete=models.CASCADE, null=True, blank=True)
    government_admin = models.ForeignKey(GovernmentAdmin, on_delete=models.CASCADE, null=True, blank=True)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict)  # Store additional data like IP address, user agent, etc.
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Dashboard Activities'
        
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.timestamp}"
        
    @property
    def actor(self):
        """Return the actor (user/ministry/gov admin) who performed the activity."""
        return self.user or self.ministry or self.government_admin
