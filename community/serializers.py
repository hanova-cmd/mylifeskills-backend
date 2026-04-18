from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import TipCategory, CommunityTip, TipLike, TipComment

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'level', 'coins')

class TipCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TipCategory
        fields = ('id', 'name', 'display_name', 'icon', 'is_active')

class TipCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = TipComment
        fields = ('id', 'user', 'text', 'likes_count', 'created_at')
        read_only_fields = ('id', 'user', 'likes_count', 'created_at')
    
    def get_user(self, obj):
        user = obj.user
        return {
            'id': user.id,
            'username': user.username,
            'level': getattr(user, 'level', 1) if hasattr(user, 'level') else 1,
            'coins': getattr(user, 'coins', 0) if hasattr(user, 'coins') else 0
        }

class CommunityTipSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    liked = serializers.SerializerMethodField()
    comments = TipCommentSerializer(many=True, read_only=True, source='comments.all')
    
    class Meta:
        model = CommunityTip
        fields = ('id', 'user', 'category', 'category_name', 'text', 
                 'age_group', 'likes_count', 'comments_count', 'views_count',
                 'is_approved', 'is_featured', 'verified', 'created_at', 
                 'liked', 'comments')
        read_only_fields = ('likes_count', 'comments_count', 'views_count', 
                           'is_approved', 'is_featured', 'verified')
    
    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return TipLike.objects.filter(user=request.user, tip=obj).exists()
        return False

class CreateTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityTip
        fields = ('text', 'category', 'age_group')

class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipComment
        fields = ('text',)