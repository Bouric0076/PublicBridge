from django.db import models
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import EmailValidator, RegexValidator, URLValidator
from django.utils.translation import gettext_lazy as _

# Consolidated Ministry model that replaces both ministries.Ministry and GovernmentAdmin.Ministry
class Ministry(models.Model):
    """
    Unified Ministry model that consolidates functionality from both original models.
    This model serves as the single source of truth for ministry data.
    """
    
    # Primary identification
    ministry_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=False)
    name = models.CharField(max_length=255, unique=True)
    name_sw = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name (Swahili)")
    
    # Contact information
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message=_("Enter a valid email address."))]
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\+?\d{10,15}$',
            message=_("Enter a valid phone number with country code (e.g., +254712345678).")
        )]
    )
    website = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message=_("Enter a valid website URL."))],
        help_text=_("Optional: Official ministry website")
    )
    
    # Administrative information
    description = models.TextField()
    description_sw = models.TextField(blank=True, null=True, verbose_name="Description (Swahili)")
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Government admin relationship (from GovernmentAdmin.Ministry)
    admin = models.OneToOneField(
        'users.GovernmentAdmin', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="managed_ministry",
        verbose_name=_("Government Admin")
    )
    
    # Authentication (from ministries.Ministry)
    password = models.CharField(max_length=255, blank=True, null=True)  # Store hashed password
    
    # KPI tracking (consolidated from both models)
    kpi_resolved = models.IntegerField(default=0)
    kpi_pending = models.IntegerField(default=0)
    kpi_under_review = models.IntegerField(default=0)
    kpi_rejected = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Ministry")
        verbose_name_plural = _("Ministries")
        ordering = ['name']

    def set_password(self, raw_password):
        """Hash and store the ministry's password."""
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """Check if the entered password matches the stored hash."""
        if not self.password:
            return False
        return check_password(raw_password, self.password)

    def update_kpis(self):
        """Updates the KPIs for the ministry based on reports."""
        if hasattr(self, 'reports'):
            self.kpi_resolved = self.reports.filter(status="Resolved").count()
            self.kpi_pending = self.reports.filter(status="Pending").count()
            self.kpi_under_review = self.reports.filter(status="Under Review").count()
            self.kpi_rejected = self.reports.filter(status="Rejected").count()
            self.save()

    def resolve_report(self, report):
        """Ministry marks a report as resolved."""
        if report.status == "Under Review":
            report.status = "Resolved"
            report.save()
            self.update_kpis()
        else:
            raise ValueError("Only reports under review can be marked as resolved.")

    def get_total_reports(self):
        """Get total number of reports assigned to this ministry."""
        if hasattr(self, 'reports'):
            return self.reports.count()
        return 0

    def get_response_rate(self):
        """Calculate the response rate as a percentage."""
        total = self.get_total_reports()
        if total == 0:
            return 0
        return (self.kpi_resolved / total) * 100

    def __str__(self):
        return f"{self.name} ({self.ministry_id})"

    def save(self, *args, **kwargs):
        """Override save to ensure ministry_id is set."""
        if not self.ministry_id:
            self.ministry_id = uuid.uuid4()
        super().save(*args, **kwargs)
