import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health.settings')

app = Celery('mental_health')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'generate-daily-tasks': {
        'task': 'game.tasks.generate_daily_tasks_for_all_users',
        'schedule': crontab(hour=0, minute=0), 
    },
    'reset-daily-progress': {
        'task': 'game.tasks.reset_daily_progress',
        'schedule': crontab(hour=0, minute=5), 
    },
    'update-streak-stats': {
        'task': 'game.tasks.update_user_streaks',
        'schedule': crontab(hour=1, minute=0), 
    },
}