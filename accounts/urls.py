from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    UserView,
    check_auth,
    check_auth_public,
    api_root
)

urlpatterns = [
    path('', api_root, name='api_root'),
    
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    path('user/', UserView.as_view(), name='user'),
    
    path('check-auth/', check_auth, name='check_auth'),
    path('check-auth-public/', check_auth_public, name='check_auth_public'),
]