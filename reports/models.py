import uuid

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from ministries.models import Ministry  # Use consolidated Ministry model
from users.models import GovernmentAdmin
from utils.nlp_utils import analyze_text  # Use actual NLP function

User = get_user_model()

# Activity Log Model
class ActivityLog(models.Model):
    action = models.CharField(max_length=255)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_report = models.ForeignKey('Report', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Action: {self.action} performed by {self.performed_by.username if self.performed_by else 'Anonymous'} at {self.timestamp}"


# ReportAttachment Model
class ReportAttachment(models.Model):
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='report_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Report {self.report.id}"




# AnonymousReport Model
class AnonymousReport(models.Model):
    CATEGORY_CHOICES = [
        ('corruption', 'Corruption'),
        ('service', 'Public Service Issue'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Anonymous Report: {self.title}"


# AssignmentQueue Model
class AssignmentQueue(models.Model):
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='queue')
    assigned_to = models.ForeignKey(GovernmentAdmin, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('queued', 'Queued'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='queued')

    def __str__(self):
        return f"Report {self.report.id} assigned to {self.assigned_to.user.username if self.assigned_to else 'Unassigned'}"


# Report Model with NLP Features
class Report(models.Model):
    STATUS_CHOICES = [
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    ]

    CATEGORY_CHOICES = [
        ('corruption', 'Corruption'),
        ('service', 'Public Service Issue'),
        ('other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'citizen'})
    user_contact = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Enter a valid contact number. It must be between 9 and 15 digits and may include a leading '+' sign."
        )]
    )
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    urgency = models.IntegerField()  # 1 (Low) to 5 (High)
    citizen_email = models.EmailField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ministry = models.ForeignKey(Ministry, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_history = models.JSONField(default=list)

    # NLP Analysis Fields
    sentiment = models.CharField(max_length=50, blank=True, null=True)  # Sentiment Analysis
    keywords = models.TextField(blank=True, null=True)  # Extracted Keywords
    nlp_category = models.CharField(max_length=100, blank=True, null=True)  # NLP-based Category

    def analyze_report(self):
        """Runs NLP analysis on the report description."""
        if self.description:
            analysis = analyze_text(self.description)  # Call NLP function
            self.sentiment = analysis.get("sentiment", "Neutral")
            self.keywords = ', '.join(analysis.get("keywords", [])) or None
            self.nlp_category = analysis.get("category", self.category)  # Default to selected category if NLP fails
            self.save()

    def update_status(self, new_status, updated_by):
        """Update the report status and log the change."""
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError("Invalid status provided.")

        if self.status != new_status:
            self.status = new_status
            self.updated_at = timezone.now()
            self.status_history.append(
                {
                    "status": new_status,
                    "updated_by": updated_by.username,
                    "timestamp": str(self.updated_at),
                }
            )
            self.save()

            ActivityLog.objects.create(
                action=f"Updated status to {new_status}",
                performed_by=updated_by,
                related_report=self
            )

    def __str__(self):
        return f"Report {self.id} - {self.status}"

    def resolve_report(self, comment):
        """Marks the report as resolved and adds a resolution comment."""
        self.status = "Resolved"
        ReportComment.objects.create(report=self, comment=comment)
        self.save()

class ReportComment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.report.title}"