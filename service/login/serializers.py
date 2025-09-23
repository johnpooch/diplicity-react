from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from user_profile.models import UserProfile

from .models import AuthUser
from .utils import verify_google_id_token


class AuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)

    id = serializers.IntegerField(read_only=True)
    email = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def create(self, validated_data):
        id_info = verify_google_id_token(validated_data["id_token"])
        user, _ = AuthUser.objects.create_from_google_id_info(id_info)
        UserProfile.objects.update_or_create(
            user=user, defaults={"name": id_info.get("name"), "picture": id_info.get("picture")}
        )
        refresh = RefreshToken.for_user(user)
        user.access_token = str(refresh.access_token)
        user.refresh_token = str(refresh)
        return user
