from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from .models import TipCategory, CommunityTip, TipLike, TipComment
from .serializers import (
    TipCategorySerializer, CommunityTipSerializer,
    TipCommentSerializer, CreateTipSerializer, CreateCommentSerializer, TipCommentSerializer
)


class TipCategoriesView(generics.ListAPIView):
    queryset = TipCategory.objects.filter(is_active=True)
    serializer_class = TipCategorySerializer
    permission_classes = [AllowAny]


class CommunityTipsView(generics.ListAPIView):
    serializer_class = CommunityTipSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = CommunityTip.objects.filter(is_approved=True)
        
        category_id = self.request.query_params.get('category')
        age_group = self.request.query_params.get('age_group')
        search = self.request.query_params.get('search')
        featured = self.request.query_params.get('featured')
        
        if category_id and category_id != 'all':
            queryset = queryset.filter(category_id=category_id)
        if age_group:
            queryset = queryset.filter(age_group=age_group)
        if search:
            queryset = queryset.filter(text__icontains=search)
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        sort = self.request.query_params.get('sort', 'newest')
        if sort == 'popular':
            queryset = queryset.order_by('-likes_count', '-created_at')
        elif sort == 'commented':
            queryset = queryset.order_by('-comments_count', '-created_at')
        else:  
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CreateTipView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateTipSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if hasattr(user, 'userstats'): 
                user.stats.coins += 10  
                user.stats.save()    
                reward = 10
                new_coins = user.stats.coins  
            elif hasattr(user, 'coins'):
                user.coins += 10
                user.save()
                reward = 10
                new_coins = user.coins
            else:
                reward = 0
                new_coins = 0
            
            tip = serializer.save(user=user)
            
            return Response({
                'success': True,
                'message': 'Tip submitted successfully!',
                'tip': CommunityTipSerializer(tip, context={'request': request}).data,
                'reward': reward,
                'new_coins': new_coins
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TipDetailView(generics.RetrieveAPIView):
    queryset = CommunityTip.objects.filter(is_approved=True)
    serializer_class = CommunityTipSerializer
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class LikeTipView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, tip_id):
        try:
            tip = CommunityTip.objects.get(id=tip_id, is_approved=True)
        except CommunityTip.DoesNotExist:
            return Response({'error': 'Tip not found'}, status=404)
        
        user = request.user
        
        like, created = TipLike.objects.get_or_create(user=user, tip=tip)
        
        if created:
            tip.likes_count += 1
            tip.save()
            
            if tip.user != user:
                if hasattr(tip.user, 'stats'):
                    tip.user.stats.points += 5
                    tip.user.stats.save()
            
            return Response({
                'success': True,
                'liked': True,
                'likes_count': tip.likes_count,
                'message': 'Tip liked!'
            })
        else:
            like.delete()
            tip.likes_count = max(0, tip.likes_count - 1)
            tip.save()
            
            return Response({
                'success': True,
                'liked': False,
                'likes_count': tip.likes_count,
                'message': 'Like removed'
            })

class CommentView(APIView):
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get(self, request, tip_id):
        try:
            tip = get_object_or_404(CommunityTip, id=tip_id, is_approved=True)
            comments = TipComment.objects.filter(tip=tip).order_by('-created_at')
            serializer = TipCommentSerializer(comments, many=True)
            
            return Response({
                'success': True,
                'comments': serializer.data,
                'count': comments.count()
            })
            
        except CommunityTip.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Tip not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, tip_id):
        try:
            tip = CommunityTip.objects.get(id=tip_id, is_approved=True)
        except CommunityTip.DoesNotExist:
            return Response({'error': 'Tip not found'}, status=404)
        
        serializer = CreateCommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                user=request.user,
                tip=tip
            )
            
            tip.comments_count += 1
            tip.save()
            
            user = request.user
            if hasattr(user, 'stats'):
                user.stats.coins += 3
                user.stats.save()
                reward = 3
                new_coins = user.stats.coins
            else:
                reward = 0
                new_coins = 0
            
            return Response({
                'success': True,
                'comment': TipCommentSerializer(comment).data,
                'reward': reward,
                'new_coins': new_coins,
                'message': 'Comment added successfully!'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LikeCommentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        try:
            comment = TipComment.objects.get(id=comment_id)
        except TipComment.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=404)
        
        comment.likes_count += 1
        comment.save()
        
        return Response({
            'success': True,
            'likes_count': comment.likes_count,
            'message': 'Comment liked!'
        })


class AdminTipsView(generics.ListAPIView):
    """Все советы для админа (включая неподтвержденные)"""
    queryset = CommunityTip.objects.all().order_by('-created_at')
    serializer_class = CommunityTipSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ApproveTipView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, tip_id):
        try:
            tip = CommunityTip.objects.get(id=tip_id)
        except CommunityTip.DoesNotExist:
            return Response({'error': 'Tip not found'}, status=404)
        
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=403)
        
        tip.is_approved = True
        tip.save()
        
        return Response({
            'success': True,
            'message': 'Tip approved',
            'tip': CommunityTipSerializer(tip, context={'request': request}).data
        })


class TestCommunityAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        user_count = CommunityTip.objects.count()
        return Response({
            "success": True,
            "message": "Community API is working!",
            "stats": {
                "total_tips": user_count,
                "approved_tips": CommunityTip.objects.filter(is_approved=True).count(),
                "featured_tips": CommunityTip.objects.filter(is_featured=True).count()
            },
            "endpoints": {
                "GET /categories/": "All categories",
                "GET /tips/": "All tips with filters",
                "POST /tips/create/": "Create new tip",
                "GET /tips/<id>/": "Get tip details",
                "POST /tips/<id>/like/": "Like/unlike tip",
                "POST /tips/<id>/comment/": "Add comment",
                "POST /comments/<id>/like/": "Like comment",
                "GET /test/": "This endpoint"
            }
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def community_stats(request):
    """Статистика комьюнити"""
    total_tips = CommunityTip.objects.count()
    total_likes = CommunityTip.objects.aggregate(total_likes=Count('likes_count'))['total_likes'] or 0
    total_comments = CommunityTip.objects.aggregate(total_comments=Count('comments_count'))['total_comments'] or 0
    
    return Response({
        'success': True,
        'stats': {
            'total_tips': total_tips,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'top_categories': list(TipCategory.objects.annotate(
                tip_count=Count('communitytip')
            ).order_by('-tip_count').values('display_name', 'tip_count')[:5])
        }
    })