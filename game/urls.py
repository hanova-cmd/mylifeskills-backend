from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import TodayTasksView
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'lessons', views.LessonViewSet, basename='lessons')
router.register(r'daily-tasks', views.DailyTaskViewSet, basename='daily-tasks')

router.register(r'lesson-progress', views.UserLessonProgressViewSet, basename='lesson-progress')

@api_view(["GET"])
def game_root(request):
    return Response({
        "categories": request.build_absolute_uri("categories/"),
        "lessons": request.build_absolute_uri("lessons/"),
        "daily-tasks": request.build_absolute_uri("daily-tasks/"),
        "lesson-progress": request.build_absolute_uri("lesson-progress/"),
        "user-stats": request.build_absolute_uri("user-stats/"),
        "today-tasks": request.build_absolute_uri("today-tasks/"),
        "profile": request.build_absolute_uri("profile/"),
        "me": request.build_absolute_uri("me/"),
        "community-tips": request.build_absolute_uri("community-tips/"),
        "achievements": request.build_absolute_uri("achievements/"),
        "completed-lessons": request.build_absolute_uri("completed-lessons/"),
        "shop-items": request.build_absolute_uri("shop-items/"),
    })

urlpatterns = [
    path('', game_root, name='game-api-root'), 
    path('', include(router.urls)), 
    
    path('user-stats/', views.UserStatsView.as_view(), name='user-stats'),
    path('today-tasks/', TodayTasksView.as_view(), name='today-tasks'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('me/', views.CurrentUserView.as_view(), name='me'),
    path('community-tips/', views.CommunityTipsView.as_view(), name='community-tips'),
    path('achievements/', views.AchievementsView.as_view(), name='achievements'),
    path('completed-lessons/', views.CompletedLessonsView.as_view(), name='completed-lessons'),
    path('shop/items/', views.ShopItemsView.as_view(), name='shop-items'),
]