from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.TipCategoriesView.as_view(), name='tip_categories'),
    
    path('tips/', views.CommunityTipsView.as_view(), name='community_tips'),
    path('tips/create/', views.CreateTipView.as_view(), name='create_tip'),
    path('tips/<int:pk>/', views.TipDetailView.as_view(), name='tip_detail'),
    path('tips/<int:tip_id>/like/', views.LikeTipView.as_view(), name='like_tip'),
    path('tips/<int:tip_id>/comments/', views.CommentView.as_view(), name='comments'),
    
    path('comments/<int:comment_id>/like/', views.LikeCommentView.as_view(), name='like_comment'),
    
    path('admin/tips/', views.AdminTipsView.as_view(), name='admin_tips'),
    path('admin/tips/<int:tip_id>/approve/', views.ApproveTipView.as_view(), name='approve_tip'),
    
    path('stats/', views.community_stats, name='community_stats'),
    
    path('test/', views.TestCommunityAPI.as_view(), name='community_test'),
]