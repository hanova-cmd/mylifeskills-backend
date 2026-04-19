# accounts/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model
from django.db import transaction

from .serializers import UserRegistrationSerializer, UserSerializer, CustomTokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("=== REGISTRATION ===")
        print("Data received:", request.data)
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            print("❌ Validation errors:", serializer.errors)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = serializer.save()
            print(f" User registered: {user.username} (ID: {user.id})")
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "success": True,
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "Registration Succeeded"
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({
        'success': True,
        'authenticated': True,
        'user': UserSerializer(request.user).data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_public(request):
    if request.user.is_authenticated:
        return Response({
            'success': True,
            'authenticated': True,
            'user': UserSerializer(request.user).data
        })
    else:
        return Response({
            'success': True,
            'authenticated': False,
            'user': None,
            'message': 'Not authenticated'
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    base = request.build_absolute_uri('/api/')

    return Response({
        "app": "Mental Health App API",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "auth": {
                "login": base + "accounts/token/",
                "refresh": base + "accounts/token/refresh/",
                "register": base + "accounts/register/",
                "profile": base + "accounts/user/",
            },
            "game": base + "game/",
            "shop": base + "shop/",
            "community": base + "community/",
        }
    })