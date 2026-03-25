from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from user_profile.models import UserProfile

from email_service.utils import send_email
from .models import AuthUser
from .utils import verify_google_id_token

User = get_user_model()


class AuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)

    id = serializers.IntegerField(read_only=True)
    email = serializers.CharField(read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
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


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists. "
                "If you signed up with Google, please sign in with Google instead."
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False,
        )
        UserProfile.objects.create(user=user, name=validated_data["display_name"])

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        send_email(
            to=user.email,
            subject="Verify your Diplicity account",
            html=f"<p>Click the link to verify your account:</p>"
            f"<a href=\"https://diplicity.com/verify-email?uid={uid}&token={token}\">"
            f"Verify Email</a>",
        )
        return user


class VerifyEmailSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid verification link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired verification token.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user
