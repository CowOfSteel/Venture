from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from characters.views import CharacterViewSet
from users.views import UserRegistrationView  # <-- Import from users app
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'characters', CharacterViewSet, basename='characters')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', UserRegistrationView.as_view(), name='register'),  # <-- Comma added here
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
