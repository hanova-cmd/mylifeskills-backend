import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health.settings')
django.setup()

from game.models import Category, Lesson, DailyTask
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def add_category_to_all_users(category_name):
    try:
        category = Category.objects.get(name=category_name)
        print(f" Found category: {category.name}")
    except Category.DoesNotExist:
        print(f" Category '{category_name}' not found")
        return
    
    lesson, created = Lesson.objects.get_or_create(
        title=f"Introduction to {category.name}",
        defaults={
            'category': category,
            'description': f'Your first lesson in {category.name} category',
            'lesson_type': 'theory',
            'difficulty': 'beginner',
            'duration': 10,
            'points': 10,
            'theory_content': f'Welcome to {category.name} category!',
            'order': 1,
            'is_active': True,
        }
    )
    
    print(f"{' Created' if created else ' Found'} lesson: {lesson.title}")
    
    users = User.objects.all()
    print(f"Found users: {users.count()}")
    
    tasks_created = 0
    for user in users:
        existing_task = DailyTask.objects.filter(
            user=user,
            category=category
        ).exists()
        
        if not existing_task:
            task = DailyTask.objects.create(
                user=user,
                title=f"Learn {category.name}",
                task_type='lesson',
                description=f'Explore {category.name} category',
                points=15,
                category=category,
                lesson=lesson,
                completed=False,
                assigned_date=timezone.now().date(),
            )
            tasks_created += 1
            print(f"   Added task for {user.username}")
    
    print("\n" + "="*50)
    print(f" DONE")
    print(f"Category '{category.name}' added to {tasks_created} users")
    print("="*50)

def list_all_categories():
    categories = Category.objects.all()
    print(" ALL CATEGORIES:")
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat.name} (ID: {cat.id})")
    return categories

if __name__ == '__main__':
    categories = list_all_categories()
    
    if categories:
        print("\nWhich category to add to all users?")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")
        
        try:
            choice = int(input("\nEnter number: ")) - 1
            if 0 <= choice < len(categories):
                selected_category = categories[choice]
                print(f"\nAdding category '{selected_category.name}'...")
                add_category_to_all_users(selected_category.name)
            else:
                print(" Invalid choice")
        except ValueError:
            print(" Please enter a number")
    else:
        print(" No categories found. Create them in admin first.")