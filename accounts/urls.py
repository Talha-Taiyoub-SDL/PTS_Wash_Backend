from django.urls import include, path
from rest_framework_nested.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("groups", views.GroupViewSet, basename="group") # For returning the groups (in other words: roles)

urlpatterns = [path("", include(router.urls)),
               path("auth/jwt/create/", views.CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
               path("auth/jwt/refresh/", views.CookieTokenRefreshView.as_view(), name="token_refresh"),
               path("auth/jwt/logout/", views.LogoutView.as_view(), name="token_logout"),
               ]