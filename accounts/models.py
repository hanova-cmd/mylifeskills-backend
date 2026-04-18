from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    @property
    def level(self):
        try:
            return self.stats.level
        except:
            return 1
    
    @property
    def coins(self):
        try:
            return self.stats.coins
        except:
            return 0
    
    @property
    def daily_streak(self):
        try:
            return self.stats.daily_streak
        except:
            return 0
    
    @property
    def total_xp(self):
        try:
            return self.stats.total_xp
        except:
            return 0
    
    @property
    def lessons_completed(self):
        try:
            return self.stats.lessons_completed
        except:
            return 0


class UserStats(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='stats' 
    )
    level = models.IntegerField(default=1)
    coins = models.IntegerField(default=0)
    daily_streak = models.IntegerField(default=0)
    total_xp = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Stats'
        verbose_name_plural = 'User Stats'
    
    def __str__(self):
        return f"Stats for {self.user.username}"
    

User.add_to_class('level', property(lambda self: getattr(self.stats, 'level', 1) if hasattr(self, 'stats') else 1))
User.add_to_class('coins', property(lambda self: getattr(self.stats, 'coins', 0) if hasattr(self, 'stats') else 0))
User.add_to_class('daily_streak', property(lambda self: getattr(self.stats, 'daily_streak', 0) if hasattr(self, 'stats') else 0))
User.add_to_class('total_xp', property(lambda self: getattr(self.stats, 'total_xp', 0) if hasattr(self, 'stats') else 0))