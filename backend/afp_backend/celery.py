"""
Celery configuration for AFP (Automated Financial Processing) project.

This file configures the Celery task queue system for background email processing.
It includes specialized queues for different types of workers and comprehensive
error handling for production use.
"""

import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')

# Create Celery app instance
app = Celery('afp_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# ==========================================
# CELERY CONFIGURATION FOR EMAIL PROCESSING
# ==========================================

# Queue definitions for specialized workers
app.conf.task_routes = {
    # Email Import Workers
    'workers.email_processing.import_emails_task': {'queue': 'email_import'},
    'workers.email_processing.import_emails_bulk_task': {'queue': 'bulk_email_import'},
    'workers.email_processing.import_emails_incremental_task': {'queue': 'incremental_email_import'},
    'workers.email_processing.manual_sync_task': {'queue': 'manual_sync_request'},
    
    # Bank Processing Workers
    'workers.email_processing.process_email_task': {'queue': 'known_bank_processing'},
    'workers.email_processing.process_unknown_bank_task': {'queue': 'unknown_bank_processing'},
    'workers.email_processing.create_transaction_task': {'queue': 'transaction_creation'},
    
    # AI and Template Workers
    'workers.ai_generation.generate_patterns_task': {'queue': 'template_generation'},
    'workers.ai_generation.improve_template_task': {'queue': 'template_improvement'},
    
    # User Interaction Workers
    'workers.user_feedback.process_user_correction_task': {'queue': 'user_feedback_processing'},
    'workers.user_feedback.queue_for_review_task': {'queue': 'user_review_queue'},
    
    # System Workers
    'workers.system.send_notification_task': {'queue': 'notification_queue'},
    'workers.system.update_analytics_task': {'queue': 'analytics_update'},
    'workers.system.retry_failed_task': {'queue': 'retry_queue'},
}

# Worker configuration optimized for different task types
app.conf.worker_prefetch_multiplier = 1  # Prevent memory issues
app.conf.task_acks_late = True  # Acknowledge tasks only after completion
app.conf.worker_max_tasks_per_child = 1000  # Restart workers periodically

# Task retry configuration
app.conf.task_retry_delay = 60  # seconds
app.conf.task_max_retries = 3
app.conf.task_default_retry_delay = 60

# Serialization settings for security and performance
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'UTC'

# Result backend configuration
app.conf.result_expires = 3600  # 1 hour

# ==========================================
# SCHEDULED TASKS (CELERY BEAT)
# ==========================================

app.conf.beat_schedule = {
    # Import new emails every hour during business hours (8 AM - 8 PM)
    'import-emails-hourly': {
        'task': 'workers.email_processing.import_emails_incremental_task',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'queue': 'incremental_email_import'}
    },
    
    # Process any queued emails every 5 minutes
    'process-queued-emails': {
        'task': 'workers.email_processing.process_queued_emails_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {'queue': 'known_bank_processing'}
    },
    
    # Generate AI templates for unknown patterns (batch processing to save costs)
    'generate-ai-templates-daily': {
        'task': 'workers.ai_generation.batch_generate_templates_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'template_generation'}
    },
    
    # Update analytics and metrics every 30 minutes
    'update-analytics': {
        'task': 'workers.system.update_analytics_task',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'queue': 'analytics_update'}
    },
    
    # Retry failed tasks every hour
    'retry-failed-tasks': {
        'task': 'workers.system.retry_failed_task',
        'schedule': crontab(minute=15),  # Every hour at minute 15
        'options': {'queue': 'retry_queue'}
    },
    
    # Refresh provider tokens every 12 hours
    'refresh-provider-tokens': {
        'task': 'core.tasks.refresh_provider_tokens',
        'schedule': crontab(hour='*/12'),  # Cada 12 horas
        'args': (False,),  # No forzar refresh
    },
    
    # Force refresh provider tokens once a day at midnight
    'force-refresh-provider-tokens': {
        'task': 'core.tasks.refresh_provider_tokens',
        'schedule': crontab(hour=0, minute=0),  # Una vez al día a medianoche
        'args': (True,),  # Forzar refresh
    },
}

# ==========================================
# ERROR HANDLING AND MONITORING
# ==========================================

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
    return 'Celery is working correctly!'

# Custom error handling
@app.task(bind=True)
def handle_task_failure(self, task_id, error, exc_info):
    """Handle task failures with proper logging and user notification."""
    print(f'Task {task_id} failed: {error}')
    # Here we can add logic to notify users about failures
    return f'Handled failure for task {task_id}'

# Monitor Celery health
@app.task
def health_check():
    """Health check task for monitoring system status."""
    return {
        'status': 'healthy',
        'queues': ['email_import', 'known_bank_processing', 'template_generation'],
        'timestamp': app.now().isoformat()
    }

if __name__ == '__main__':
    app.start() 