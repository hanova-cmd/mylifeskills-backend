from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
from .models import User, UserStats, DailyUserTask
from datetime import timedelta

@shared_task
def generate_daily_tasks_for_all_users():
    """Генерирует ежедневные задачи для всех пользователей"""
    call_command('generate_tasks')

@shared_task
def reset_daily_progress():
    """Сбрасывает ежедневный прогресс"""
    today = timezone.now().date()

@shared_task
def update_user_streaks():
    """Обновляет серии выполнения задач пользователей"""
    users = User.objects.all()
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    for user in users:
        stats, created = UserStats.objects.get_or_create(user=user)
        
        yesterday_tasks = DailyUserTask.objects.filter(
            user=user,
            assigned_date=yesterday,
            is_completed=True
        )
        
        if yesterday_tasks.exists():
            stats.current_streak += 1
            if stats.current_streak > stats.longest_streak:
                stats.longest_streak = stats.current_streak
        else:
            stats.current_streak = 0
            
        stats.save()