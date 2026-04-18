from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from .models import DailyTask, Lesson, Category

User = get_user_model()


@receiver(post_save, sender=User)
def create_initial_data(sender, instance, created, **kwargs):
    """
    Создание начальных данных для нового пользователя
    """
    if created:
        print(f"[SIGNAL] Создание данных для пользователя: {instance.username}")
        
        transaction.on_commit(lambda: _create_user_initial_data(instance))


def _create_user_initial_data(user):
    """
    Фактическое создание данных пользователя
    Выполняется после коммита транзакции
    """
    try:
        # Двойная проверка, что пользователь существует
        if not User.objects.filter(id=user.id).exists():
            print(f"[SIGNAL] ⚠️ Пользователь {user.id} не найден, пропускаем")
            return
        
        print(f"[SIGNAL] Создание задач для пользователя: {user.username}")
        create_initial_tasks(user)
        
        print(f"[SIGNAL] ✅ Данные созданы для: {user.username}")
        
    except Exception as e:
        print(f"[SIGNAL] ❌ Ошибка при создании данных: {e}")


def create_initial_tasks(user):
    """
    Создание начальных задач для пользователя
    """
    today = timezone.now().date()
    
    active_lessons = Lesson.objects.filter(is_active=True).order_by('?')[:3]
    
    if active_lessons.exists():
        print(f"[SIGNAL] Найдены активные уроки: {active_lessons.count()}")
        
        for i, lesson in enumerate(active_lessons):
            task_type = 'interactive' if i == 2 else 'lesson'
            points = lesson.points + 10 if i == 2 else lesson.points
            duration = lesson.duration + 5 if i == 2 else lesson.duration
            
            DailyTask.objects.create(
                user=user,
                lesson=lesson,
                task_type=task_type,
                title=f'Урок: {lesson.title}' if i < 2 else f'Квест: {lesson.title}',
                description=lesson.description if i < 2 else 'Практическое задание',
                points=points,
                duration=duration,
                category=lesson.category,
                assigned_date=today
            )
    else:
        print("[SIGNAL] Активные уроки не найдены, создаем демо-задачи")
        
        categories_data = [
            {'name': 'psychology', 'emoji': '🧠', 'color': '#FF6B6B'},
            {'name': 'finance', 'emoji': '💰', 'color': '#4ECDC4'},
            {'name': 'household', 'emoji': '🏠', 'color': '#45B7D1'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': f'Категория: {cat_data["name"]}',
                    'emoji': cat_data['emoji'],
                    'color': cat_data['color'],
                    'age_min': 10,
                    'age_max': 25
                }
            )
            categories[cat_data['name']] = category
        
        demo_tasks = [
            {
                'task_type': 'lesson',
                'title': 'Основы стресс-менеджмента',
                'description': 'Изучите техники управления стрессом',
                'points': 15,
                'duration': 10,
                'category_name': 'psychology'
            },
            {
                'task_type': 'lesson',
                'title': 'Бюджет на неделю',
                'description': 'Планирование расходов и доходов',
                'points': 20,
                'duration': 15,
                'category_name': 'finance'
            },
            {
                'task_type': 'interactive',
                'title': 'Приготовление простых блюд',
                'description': 'Освоение базовых кулинарных навыков',
                'points': 25,
                'duration': 20,
                'category_name': 'household'
            }
        ]
        
        for task_data in demo_tasks:
            DailyTask.objects.create(
                user=user,
                task_type=task_data['task_type'],
                title=task_data['title'],
                description=task_data['description'],
                points=task_data['points'],
                duration=task_data['duration'],
                category=categories[task_data['category_name']],
                assigned_date=today
            )
    
    print(f"[SIGNAL] Задачи созданы для пользователя: {user.username}")