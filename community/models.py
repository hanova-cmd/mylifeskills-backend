from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TipCategory(models.Model):
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Tip Categories"
    
    def __str__(self):
        return self.display_name

class CommunityTip(models.Model):
    """Совет от пользователя"""
    AGE_GROUP_CHOICES = [
        ('teen', 'Teenagers (13-17 years)'),
        ('young_adult', 'Young Adults (18-25 years)'),
        ('adult', 'Adults (26+ years)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_tips')
    category = models.ForeignKey(TipCategory, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, default='teen')
    
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.text[:50]}... by {self.user.username}"

class TipLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tip = models.ForeignKey(CommunityTip, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'tip']
    
    def __str__(self):
        return f"{self.user.username} likes tip #{self.tip.id}"

class TipComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tip = models.ForeignKey(CommunityTip, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    likes_count = models.IntegerField(default=0)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on tip #{self.tip.id}"