from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as BaseTokenObtainPairSerializer,
    TokenRefreshSerializer as BaseTokenRefreshSerializer,
)
from config.settings import AUTH_USER_MODEL as User


# This Serializer will be used for the endpoint auth/jwt/create/ which returns the tokens and roles during logging in.
class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)  # gives 'access' and 'refresh'
        user = self.user
        # add extra fields to the response
        data.update(
            {"id": user.id, "roles": user.groups.values_list("name", flat=True)}
        )
        return data


# I didn't understand this part. Fahad Bhai added this part which I have to understand later.
class CustomTokenRefreshSerializer(BaseTokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # decode refresh token to get user_id
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get("user_id")

        user = User.objects.get(id=user_id)
        data["roles"] = list(user.groups.values_list("name", flat=True))
        data["id"] = user.id
        data["user"] = user.username

        return data


class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
