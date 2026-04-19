from rest_framework import serializers
from .models import Category, Lesson, LessonProgress, DailyTask

class CategorySerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'emoji', 'color', 'age_min', 'age_max',
            'lessons_count', 'created_at'
        ]
        read_only_fields = ['created_at', 'lessons_count']  

    def get_lessons_count(self, obj):
        return obj.lessons.filter(is_active=True).count()

class LessonSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_emoji = serializers.CharField(source='category.emoji', read_only=True)
    user_progress = serializers.SerializerMethodField()
    completed = serializers.SerializerMethodField()
    interactive_content = serializers.JSONField(required=False, allow_null=True)
    quiz_questions = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'category', 'category_name', 'category_emoji',
            'lesson_type', 'difficulty', 'age_min', 'age_max', 'duration', 'coins',
            'theory_content', 'interactive_content', 'quiz_questions', 'image', 'video_url',
            'user_progress', 'completed', 'order', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user_progress', 'completed', 'category_name', 'category_emoji']

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = LessonProgress.objects.filter(
                    user=request.user, 
                    lesson=obj
                ).first()
                if progress:
                    return {
                        'progress': progress.progress,
                        'completed': progress.completed,
                        'coins_earned': progress.coins_earned,
                        'attempts': progress.attempts,
                        'best_score': progress.best_score,
                        'started_at': progress.started_at,
                        'completed_at': progress.completed_at
                    }
            except LessonProgress.DoesNotExist:
                pass
        return None

    def get_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LessonProgress.objects.filter(
                user=request.user, 
                lesson=obj, 
                completed=True
            ).exists()
        return False

class UserLessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    category_name = serializers.CharField(source='lesson.category.name', read_only=True)
    lesson_points = serializers.IntegerField(source='lesson.points', read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'lesson_title', 'category_name', 'lesson_coins',
            'completed', 'points_earned', 'progress', 'attempts', 'best_score',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['user', 'started_at', 'completed_at']

class DailyTaskSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='lesson.category.name', read_only=True, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True) 

    class Meta:
        model = DailyTask
        fields = [
            'id', 'user', 'lesson', 'lesson_title', 'category_name',
            'task_type', 'title', 'description', 'coins', 'duration', 
            'completed', 'assigned_date', 'completed_at', 'category'
        ]
        read_only_fields = ['user', 'assigned_date', 'completed_at', 'created_at']