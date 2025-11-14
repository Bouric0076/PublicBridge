"""
Django signals for automatic AI processing of reports and user activities.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import threading
import time

from .models import Report, ReportComment
from users.models import User

# Background processing thread
class AIProcessingThread(threading.Thread):
    def __init__(self, instance, process_type, delay=2):
        super().__init__()
        self.instance = instance
        self.process_type = process_type
        self.delay = delay
    
    def run(self):
        """Run AI processing after a delay."""
        time.sleep(self.delay)
        
        try:
            if self.process_type == 'report':
                self.instance.process_with_ai()
            elif self.process_type == 'user':
                if hasattr(self.instance, 'profile'):
                    self.instance.profile.analyze_with_ai()
        except Exception as e:
            print(f"Background AI processing failed: {e}")

@receiver(post_save, sender=Report)
def process_report_with_ai(sender, instance, created, **kwargs):
    """
    Automatically process new reports with AI after a short delay.
    """
    if created and settings.AUTO_AI_PROCESSING:
        # Start background processing thread
        thread = AIProcessingThread(instance, 'report')
        thread.start()

@receiver(post_save, sender=User)
def analyze_user_with_ai(sender, instance, created, **kwargs):
    """
    Analyze user behavior with AI when profile is updated.
    """
    if not created and settings.AUTO_AI_PROCESSING:
        # Only process if user has sufficient activity
        # Use reverse relationships: report_set for reports
        # For comments, we need to go through reports since ReportComment doesn't have a direct user field
        report_count = instance.report_set.count()
        comment_count = 0
        
        # Count comments made by user across all their reports
        for report in instance.report_set.all():
            comment_count += report.comments.count()
        
        if report_count > 2 or comment_count > 5:
            thread = AIProcessingThread(instance, 'user', delay=5)
            thread.start()

@receiver(post_save, sender=ReportComment)
def update_report_ai_analysis(sender, instance, created, **kwargs):
    """
    Re-analyze report when new comments are added.
    """
    if created and settings.AUTO_AI_PROCESSING:
        report = instance.report
        # Re-process report if it has significant new activity
        if report.comments.count() > 3:
            thread = AIProcessingThread(report, 'report', delay=3)
            thread.start()

# Signal for batch AI processing
def batch_process_reports_with_ai(report_ids):
    """
    Process multiple reports with AI in batch.
    """
    from .models import Report
    
    processed_count = 0
    for report_id in report_ids:
        try:
            report = Report.objects.get(id=report_id)
            if report.process_with_ai():
                processed_count += 1
        except Report.DoesNotExist:
            print(f"Report {report_id} not found")
        except Exception as e:
            print(f"Failed to process report {report_id}: {e}")
    
    return processed_count

def batch_analyze_users_with_ai(user_ids):
    """
    Analyze multiple users with AI in batch.
    """
    from users.models import User
    
    processed_count = 0
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            if hasattr(user, 'profile'):
                if user.profile.analyze_with_ai():
                    processed_count += 1
        except User.DoesNotExist:
            print(f"User {user_id} not found")
        except Exception as e:
            print(f"Failed to analyze user {user_id}: {e}")
    
    return processed_count