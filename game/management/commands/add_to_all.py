from django.core.management.base import BaseCommand
from game.models import Category, Lesson

class Command(BaseCommand):
    help = 'Add category or lesson to all users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=int,
            help='Category ID to add to all users'
        )
        parser.add_argument(
            '--lesson',
            type=int,
            help='Lesson ID to add to all users'
        )
    
    def handle(self, *args, **options):
        category_id = options.get('category')
        lesson_id = options.get('lesson')
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                tasks_created = category.add_to_all_users()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Category '{category.name}' added to all users ({tasks_created} tasks)")
                )
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Category with ID {category_id} not found"))
        
        elif lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                category = lesson.category
                
                from django.contrib.auth import get_user_model
                from django.utils import timezone
                from game.models import DailyTask
                
                User = get_user_model()
                users = User.objects.all()
                tasks_created = 0
                
                for user in users:
                    if not DailyTask.objects.filter(
                        user=user,
                        lesson=lesson,
                        assigned_date=timezone.now().date()
                    ).exists():
                        DailyTask.objects.create(
                            user=user,
                            title=f"Learn {lesson.title}",
                            task_type='lesson',
                            description=lesson.description[:100],
                            points=lesson.points,
                            category=category,
                            lesson=lesson,
                            completed=False,
                            assigned_date=timezone.now().date(),
                        )
                        tasks_created += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Lesson '{lesson.title}' added to all users ({tasks_created} tasks)")
                )
            except Lesson.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Lesson with ID {lesson_id} not found"))
        
        else:
            self.stdout.write(self.style.ERROR("❌ Please specify --category or --lesson"))