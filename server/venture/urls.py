from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from characters.views import CharacterViewSet, SkillViewSet, BackgroundViewSet, EdgeViewSet
from users.views import UserRegistrationView, user_roles  # <-- Import from users app
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.views import user_roles

router = routers.DefaultRouter()
router.register(r'characters', CharacterViewSet, basename='characters')
router.register(r'skills', SkillViewSet, basename='skills')
router.register(r'backgrounds', BackgroundViewSet, basename='backgrounds')
router.register(r'edges', EdgeViewSet, basename='edges')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', UserRegistrationView.as_view(), name='register'),  # <-- Comma added here
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user_roles/', user_roles, name='user_roles'),
]
