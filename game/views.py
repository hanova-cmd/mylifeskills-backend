from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Category, Lesson, LessonProgress, DailyTask
from .serializers import (
    CategorySerializer,
    LessonSerializer,
    UserLessonProgressSerializer,
    DailyTaskSerializer
)

User = get_user_model()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.filter(is_active=True)
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start_lesson(self, request, pk=None):
        lesson = get_object_or_404(Lesson, pk=pk, is_active=True)

        with transaction.atomic():
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson=lesson,
                defaults={"attempts": 1, "started_at": timezone.now()}
            )

            if not created:
                progress.attempts += 1
                progress.save()

        return Response({
            "success": True,
            "message": "Lesson started successfully",
            "lesson_id": lesson.id,
            "lesson_title": lesson.title,
            "attempts": progress.attempts,
            "progress_id": progress.id
        })

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete_lesson(self, request, pk=None):
        lesson = get_object_or_404(Lesson, pk=pk, is_active=True)
        score = request.data.get("score", 100)

        with transaction.atomic():
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson=lesson
            )

            progress.completed = True
            progress.completed_at = timezone.now()
            progress.progress = 100
            progress.coins_earned = lesson.coins
            progress.best_score = max(progress.best_score or 0, score)
            progress.save()

            try:
                stats = request.user.stats  
                stats.total_xp += lesson.coins
                stats.lessons_completed += 1
                stats.save()
            except AttributeError:
                pass

        return Response({
            "success": True,
            "coins_earned": lesson.coins,
            "message": "Lesson completed successfully!"
        })

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def submit_quiz(self, request, pk=None):
        lesson = get_object_or_404(Lesson, pk=pk, is_active=True)
        user = request.user
        user_answers = request.data.get('answers', [])
        
        quiz_data = lesson.quiz_questions
        questions = quiz_data.get('questions', [])
        passing_score = lesson.passing_score
        
        correct_count = 0
        for i, answer in enumerate(user_answers):
            if i < len(questions) and answer == questions[i].get('correct'):
                correct_count += 1
        
        total_questions = len(questions)
        if total_questions > 0:
            score_percentage = int((correct_count / total_questions) * 100)
        else:
            score_percentage = 0
        
        progress, created = LessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson
        )
        
        progress.attempts += 1
        if score_percentage > progress.best_score:
            progress.best_score = score_percentage
        
        passed = score_percentage >= passing_score
        coins_earned = 0
        xp_earned = 0
        new_coins = 0
        new_xp = 0
        
        if passed and not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.coins_earned = lesson.coins
            coins_earned = lesson.coins
            xp_earned = lesson.coins
            progress.progress = 100
            
            try:
                stats = user.stats 
                stats.coins += coins_earned
                stats.total_xp += xp_earned
                stats.lessons_completed += 1
                stats.save()
                
                new_coins = stats.coins
                new_xp = stats.total_xp
                
            except AttributeError as e:
                print(f"Error updating stats: {e}")
                new_coins = 0
                new_xp = 0
        
        progress.save()
        
        return Response({
            'success': passed,
            'completed': progress.completed,
            'score': score_percentage,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'coins_earned': coins_earned,
            'points_earned': coins_earned,
            'xp_earned': xp_earned,
            'new_coins': new_coins,
            'new_points': new_coins,
            'new_xp': new_xp,
            'best_score': progress.best_score,
            'attempts': progress.attempts,
            'message': f'You scored {score_percentage}%! ' + ('You passed! 🎉' if passed else 'Try again! 💪')
        })


class UserLessonProgressViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserLessonProgressSerializer

    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user)


class DailyTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DailyTaskSerializer

    def get_queryset(self):
        today = timezone.now().date()
        return DailyTask.objects.filter(user=self.request.user, assigned_date=today)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete_task(self, request, pk=None):
        task = get_object_or_404(DailyTask, pk=pk, user=request.user)

        with transaction.atomic():
            task.completed = True
            task.completed_at = timezone.now()
            task.save()

            try:
                stats = request.user.stats 
                stats.daily_streak += 1
                if hasattr(stats, 'coins'):
                    stats.coins += task.coins
                stats.save()
            except AttributeError:
                pass

        return Response({
            "success": True,
            "coins_earned": task.coins,
            "message": "Task completed!"
        })


class TodayTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        tasks = DailyTask.objects.filter(user=request.user, assigned_date=today)

        return Response({
            "success": True,
            "tasks": DailyTaskSerializer(tasks, many=True).data
        })


class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            stats = user.stats 
            coins = stats.coins
            level = stats.level
            streak = stats.daily_streak
            lessons_completed = stats.lessons_completed
            total_xp = stats.total_xp
        except AttributeError:
            coins = 0
            level = 1
            streak = 0
            lessons_completed = 0
            total_xp = 0
        
        total_lessons = Lesson.objects.filter(is_active=True).count()
        
        return Response({
            "coins": coins,
            "level": level,
            "streak": streak,
            "lessons_completed": lessons_completed,
            "total_lessons": total_lessons,
            "total_xp": total_xp,
            "tasks_completed": DailyTask.objects.filter(user=user, completed=True).count()
        })

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            stats = user.stats 
            coins = stats.coins
            level = stats.level
            streak = stats.daily_streak
            lessons_completed = stats.lessons_completed
        except AttributeError:
            coins = 0
            level = 1
            streak = 0
            lessons_completed = 0
        
        total_lessons = Lesson.objects.filter(is_active=True).count()
        
        return Response({
            "username": user.username,
            "email": user.email,
            "coins": coins,
            "completed_lessons": lessons_completed,
            "total_lessons": total_lessons,
            "streak_days": streak,
            "level": level,
            "progress_percent": int((lessons_completed / total_lessons * 100)) if total_lessons else 0
        })


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            stats = user.stats 
            coins = stats.coins
            level = stats.level
            streak = stats.daily_streak
            lessons_completed = stats.lessons_completed
        except AttributeError:
            coins = 0
            level = 1
            streak = 0
            lessons_completed = 0

        return Response({
            "username": user.username,
            "email": user.email,
            "coins": coins,
            "completed_lessons": lessons_completed,
            "streak_days": streak,
            "level": level
        })


class CommunityTipsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([])


class AchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([])


class CompletedLessonsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        completed = LessonProgress.objects.filter(
            user=user, completed=True
        ).select_related("lesson", "lesson__category")

        lessons = [{
            "id": p.lesson.id,
            "title": p.lesson.title,
            "category": p.lesson.category.name,
            "coins_earned": p.coins_earned,
            "completed_at": p.completed_at
        } for p in completed]

        return Response(lessons)


class ShopItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([])