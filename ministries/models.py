from django.db import models
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import EmailValidator, RegexValidator, URLValidator

class Ministry(models.Model):
    ministry_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address.")]
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\+?\d{10,15}$',
            message="Enter a valid phone number with country code (e.g., +254712345678)."
        )]
    )
    website = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message="Enter a valid website URL.")],
        help_text="Optional: Official ministry website"
    )
    description = models.TextField()
    is_approved = models.BooleanField(default=False)

    # Add Password Field
    password = models.CharField(max_length=255)  # Store hashed password

    # KPI tracking
    kpi_resolved = models.IntegerField(default=0)
    kpi_pending = models.IntegerField(default=0)
    kpi_under_review = models.IntegerField(default=0)
    kpi_rejected = models.IntegerField(default=0)

    def set_password(self, raw_password):
        """Hash and store the ministry’s password."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if the entered password matches the stored hash."""
        return check_password(raw_password, self.password)

    def update_kpis(self):
        """Updates the KPIs for the ministry based on reports."""
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

    def __str__(self):
        return f"{self.name} - {self.ministry_id}"
