from django.db import models
from django.conf import settings  # Important: Import settings to reference your custom user model

class AnonymousReport(models.Model):
    CATEGORY_CHOICES = [
        ('corruption', 'Corruption'),
        ('service', 'Public Service Issue'),
        ('other', 'Other'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}"


class Comment(models.Model):
    report = models.ForeignKey('Report', on_delete=models.CASCADE,
                               related_name='comments')  # Foreign key to the Report model
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Reference to the user who commented
    content = models.TextField()  # Content of the comment
    created_at = models.DateTimeField(
        auto_now_add=True)  # Automatically sets the timestamp when the comment was created

    def __str__(self):
        return f"Comment by {self.user.username} on {self.report.title} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['created_at']

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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="General")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_department = models.ForeignKey(
        'users.GovernmentAdmin',  # Correct app and model name
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
    )
    def __str__(self):
        return self.title