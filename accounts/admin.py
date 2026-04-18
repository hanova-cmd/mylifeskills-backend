from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import User, UserStats

User = get_user_model()

admin.site.register(User, UserAdmin)

@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'coins', 'daily_streak', 'total_xp', 'lessons_completed']
    list_filter = ['level']
    search_fields = ['user__username', 'user__email']