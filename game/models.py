from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone 

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=20, default='#000000')
    age_min = models.IntegerField(default=0)
    age_max = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def add_to_all_users(self, lesson=None):
        if not lesson:
            lesson, created = Lesson.objects.get_or_create(
                title=f"Introduction to {self.name}",
                category=self,
                defaults={
                    'description': f'Basic lesson about {self.name}',
                    'lesson_type': 'theory',
                    'difficulty': 'beginner',
                    'duration': 10,
                    'coins': 10,
                    'order': 1,
                    'is_active': True,
                }
            )
        
        users = User.objects.all()
        tasks_created = 0
        
        for user in users:
            if not DailyTask.objects.filter(
                user=user, 
                category=self,
                assigned_date=timezone.now().date()
            ).exists():
                DailyTask.objects.create(
                    user=user,
                    title=f"Learn {self.name}",
                    task_type='lesson',
                    description=f'Explore {self.name} category',
                    coins=15,
                    category=self,
                    lesson=lesson,
                    completed=False,
                    assigned_date=timezone.now().date(),
                )
                tasks_created += 1
        
        return tasks_created
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return f"{self.emoji} {self.name}"

class Lesson(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    LESSON_TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('interactive', 'Interactive'),
        ('quiz', 'Quiz'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='lessons')
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default='interactive')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    age_min = models.IntegerField(default=10)
    age_max = models.IntegerField(default=25)
    duration = models.IntegerField(help_text="Duration in minutes", default=15)
    coins = models.IntegerField(default=30)
    
    theory_content = models.TextField(blank=True)
    interactive_content = models.JSONField(default=dict, blank=True)
    quiz_questions = models.JSONField(default=dict, blank=True)
    
    passing_score = models.IntegerField(default=70, help_text="Passing score in %")
    max_attempts = models.IntegerField(default=3, help_text="Maximum attempts allowed")
    theory_images = models.JSONField(default=list, blank=True, help_text="List of image URLs")
    
    image = models.ImageField(upload_to='lesson_images/', blank=True, null=True)
    video_url = models.URLField(blank=True)

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
    
    def __str__(self):
        return self.title
    
    @property
    def category_name(self):
        return self.category.name
    
    @property
    def category_emoji(self):
        return self.category.emoji

class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    progress = models.IntegerField(default=0)  
    completed = models.BooleanField(default=False)
    coins_earned = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    best_score = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'lesson']
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progresses"
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"

class DailyTask(models.Model):
    TASK_TYPES = [
        ('lesson', 'Complete Lesson'),
        ('practice', 'Practice'),
        ('quiz', 'Quiz'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    coins = models.IntegerField(default=10)
    completed = models.BooleanField(default=False)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='daily_tasks')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='daily_tasks')
    
    assigned_date = models.DateField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_date']
        verbose_name = "Daily Task"
        verbose_name_plural = "Daily Tasks"
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"