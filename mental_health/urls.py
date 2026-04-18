from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

def old_api_root(request):
    return JsonResponse({
        'accounts': '/api/accounts/',
        'game': '/api/game/',
        'shop': '/api/shop/',
        'community': '/api/community/',
    })

@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Mental Health App API',
        'version': '1.0',
        'endpoints': {
            'auth': {
                'login': request.build_absolute_uri('token/'),
                'super_login': request.build_absolute_uri('accounts/super-login/'),
                'refresh': request.build_absolute_uri('token/refresh/'),
                'register': request.build_absolute_uri('accounts/register/'),
            },
            'game': request.build_absolute_uri('game/'),
            'user': request.build_absolute_uri('accounts/user/'),
            'shop': request.build_absolute_uri('shop/'),
            'community': request.build_absolute_uri('community/'),
        },
        'status': 'running'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/', api_root, name='api-root'),
    path('api/accounts/', include('accounts.urls')),
    path('api/game/', include('game.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/shop/', include('shop.urls')),  
    path('api/community/', include('community.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)