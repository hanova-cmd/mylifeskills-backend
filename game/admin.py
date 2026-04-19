from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Count
from .models import Category, Lesson, LessonProgress, DailyTask

User = get_user_model()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'user_count', 'task_count', 'add_to_all_button']
    list_filter = ['age_min', 'age_max']
    search_fields = ['name', 'description']
    actions = ['add_to_all_users_action']
    
    def user_count(self, obj):
        return User.objects.filter(daily_tasks__category=obj).distinct().count()
    user_count.short_description = 'Users'
    
    def task_count(self, obj):
        return DailyTask.objects.filter(category=obj).count()
    task_count.short_description = 'Tasks'
    
    def add_to_all_button(self, obj):
        url = reverse('admin:add_category_to_all', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; margin-right: 5px;">➕ Add to all</a>',
            url
        )
    add_to_all_button.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:category_id>/add_to_all/',
                 self.admin_site.admin_view(self.add_to_all_view),
                 name='add_category_to_all'),
        ]
        return custom_urls + urls
    
    def add_to_all_view(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
            tasks_created = category.add_to_all_users()
            
            self.message_user(
                request,
                f' Category "{category.name}" added to all users ({tasks_created} tasks created)',
                messages.SUCCESS
            )
            
        except Category.DoesNotExist:
            self.message_user(request, '❌ Category not found', messages.ERROR)
        
        return redirect('admin:game_category_changelist')
    
    def add_to_all_users_action(self, request, queryset):
        total_tasks = 0
        for category in queryset:
            tasks_created = category.add_to_all_users()
            total_tasks += tasks_created
        
        self.message_user(
            request,
            f' Added {len(queryset)} categories to all users ({total_tasks} tasks created)',
            messages.SUCCESS
        )
    add_to_all_users_action.short_description = "Add selected categories to all users"

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'lesson_type', 'difficulty', 'coins', 'order', 'is_active']
    list_filter = ['category', 'lesson_type', 'difficulty', 'is_active']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'lesson_type', 'difficulty')
        }),
        ('Settings', {
            'fields': ('duration', 'coins', 'order', 'is_active', 'age_min', 'age_max')
        }),
        ('Theory Content with Images', {
            'fields': ('theory_content', 'theory_images', 'image', 'video_url'),
            'classes': ('wide',),
            'description': 'You can use HTML in theory_content. For images: <img src="URL" style="max-width:100%">'
        }),
        ('Quiz Questions (JSON Format)', {
            'fields': ('quiz_questions', 'passing_score', 'max_attempts'),
            'classes': ('wide',),
            'description': '''
                Example format for quiz_questions:
                {
                    "questions": [
                        {
                            "text": "What is stress?",
                            "options": ["Body's reaction", "Disease", "Sport", "Medicine"],
                            "correct": 0,
                            "explanation": "Stress is the body's natural response"
                        },
                        {
                            "text": "Second question?",
                            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                            "correct": 1,
                            "explanation": "Explanation why option 2 is correct"
                        }
                    ]
                }
            '''
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'lesson', 'task_type', 'title', 'completed', 'assigned_date']
    list_filter = ['category', 'task_type', 'completed', 'assigned_date']
    search_fields = ['title', 'user__username', 'category__name', 'lesson__title']
    
    fields = ['user', 'task_type', 'title', 'description', 'coins', 'completed', 
              'category', 'lesson', 'assigned_date']
    
    def save_model(self, request, obj, form, change):
        if not obj.assigned_date:
            from datetime import date
            obj.assigned_date = date.today()
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_completed', 'mark_as_incomplete']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(completed=True, completed_at=timezone.now())
        self.message_user(request, f'✅ {queryset.count()} tasks marked as completed', messages.SUCCESS)
    mark_as_completed.short_description = "Mark selected tasks as completed"
    
    def mark_as_incomplete(self, request, queryset):
        queryset.update(completed=False, completed_at=None)
        self.message_user(request, f'✅ {queryset.count()} tasks marked as incomplete', messages.SUCCESS)
    mark_as_incomplete.short_description = "Mark selected tasks as incomplete"

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'completed', 'progress', 'coins_earned', 'attempts', 'best_score']
    list_filter = ['completed', 'started_at']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['user', 'lesson', 'started_at', 'completed_at']