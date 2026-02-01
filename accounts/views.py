from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.conf import settings
from django.contrib.auth.models import Group
from .serializers import GroupSerializer
from django.views.decorators.csrf import csrf_protect,ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

class GroupViewSet(ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

# @method_decorator(ensure_csrf_cookie, name="dispatch") Commented cause don't want to use csrf protection here for simplicity
class CookieTokenObtainPairView(TokenObtainPairView):
    # Automatically use the CustomSerializer that I defined in the settings Of SIMPLE_JWT["TOKEN_OBTAIN_SERIALIZER"]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # `response.data` contains {'refresh': '...', 'access': '...', roles:[...]} 
        refresh = response.data.get("refresh")

        # set refresh cookie
        if refresh:
            cookie_max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
 
            response.set_cookie(
                settings.JWT_REFRESH_COOKIE_NAME,
                refresh,
                max_age=cookie_max_age,
                secure=settings.JWT_COOKIE_SECURE,
                httponly=settings.JWT_COOKIE_HTTPONLY,
                samesite=settings.JWT_COOKIE_SAMESITE, 
                path=settings.JWT_COOKIE_PATH,
            )

        response.data.pop("refresh", None) #If refresh is not present, don't throw an error, just return None
        return response

# @method_decorator(csrf_protect, name="dispatch") Commented cause don't want to use csrf protection here for simplicity
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        
        if not refresh_token:
            raise exceptions.ParseError("No refresh token cookie set.")
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            # Return clean JSON instead of full traceback
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
 
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

# @method_decorator(csrf_protect, name="dispatch") Commented it cause don't want to use csrf protection here for simplicity
class LogoutView(APIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        res = Response({"detail": "success"}, status=status.HTTP_200_OK)
        res.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path=settings.JWT_COOKIE_PATH)
        return res

