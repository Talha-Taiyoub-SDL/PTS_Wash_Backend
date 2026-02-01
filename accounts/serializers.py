from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer


# This Serializer will be used for the endpoint auth/jwt/create/ which returns the tokens and roles during logging in.
class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs) # gives 'access' and 'refresh'
        user = self.user
        # add extra fields to the response
        data.update({
            "id":user.id,
            "roles":user.groups.values_list('name',flat=True)
        })
        return data



class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()