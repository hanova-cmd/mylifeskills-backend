from django.core.management.base import BaseCommand
from django.utils import timezone
from game.models import DailyTask, MentalHealthProfile
from accounts.models import User
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Генерирует персонализированные ежедневные задачи для пользователей'
    
    def handle(self, *args, **options):
        users = User.objects.all()
        today = timezone.now().date()
        
        for user in users:
            self.generate_daily_tasks(user, today)
    
    def generate_daily_tasks(self, user, date):
        """Генерирует 4 персонализированные задачи для пользователя"""
        try:
            profile = MentalHealthProfile.objects.get(user=user)
        except MentalHealthProfile.DoesNotExist:
            profile = MentalHealthProfile.objects.create(user=user)
        
        recommended_categories = profile.get_recommended_tasks()
        
        base_tasks = DailyTask.objects.filter(
            is_active=True,
            difficulty__in=['easy', 'medium']
        ).order_by('?')[:2]
        
        personalized_tasks = DailyTask.objects.filter(
            is_active=True,
            category__in=recommended_categories
        ).order_by('?')[:2]
        
        if len(personalized_tasks) < 2:
            additional_tasks = DailyTask.objects.filter(
                is_active=True
            ).exclude(
                id__in=[t.id for t in base_tasks] + [t.id for t in personalized_tasks]
            ).order_by('?')[:2-len(personalized_tasks)]
            personalized_tasks = list(personalized_tasks) + list(additional_tasks)
        
        all_tasks = list(base_tasks) + list(personalized_tasks)
        
        DailyUserTask.objects.filter(user=user, assigned_date=date).delete()
        for task in all_tasks[:4]:
            DailyUserTask.objects.create(
                user=user,
                task=task,
                assigned_date=date,
                is_completed=False
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Сгенерированы задачи для {user.username}')
        )

class DailyUserTask(models.Model):
    """Ежедневные задачи пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(DailyTask, on_delete=models.CASCADE)
    assigned_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'task', 'assigned_date']