import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings_secure')

app = Celery('PublicBridge')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery with Redis broker
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 1 hour
    beat_schedule={
        'cleanup-old-reports': {
            'task': 'reports.tasks.cleanup_old_reports',
            'schedule': 86400.0,  # Daily at midnight
        },
        'update-agency-status': {
            'task': 'disaster_reporting.tasks.update_agency_status',
            'schedule': 300.0,  # Every 5 minutes
        },
        'process-ai-analysis': {
            'task': 'reports.tasks.process_pending_ai_analysis',
            'schedule': 60.0,  # Every minute
        },
        'cleanup-old-ai-analysis': {
            'task': 'reports.tasks.cleanup_old_ai_analysis',
            'schedule': 86400.0,  # Daily at midnight
        },
        'check-ai-gateway-health': {
            'task': 'reports.tasks.check_ai_gateway_health',
            'schedule': 300.0,  # Every 5 minutes
        },
    }
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configure logging for Celery
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

# Error handling for Celery tasks
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def handle_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Handle task failures with retry logic."""
    logger.error(f'Task {task_id} failed: {exc}')
    # Send notification to admins for critical failures
    if hasattr(settings, 'ADMINS') and settings.ADMINS:
        from django.core.mail import mail_admins
        mail_admins(
            'Celery Task Failure',
            f'Task {task_id} failed after {self.request.retries} retries.\n'
            f'Exception: {exc}\n'
            f'Args: {args}\n'
            f'Kwargs: {kwargs}',
            fail_silently=True
        )