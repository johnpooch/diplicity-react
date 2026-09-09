from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from user_profile.models import UserProfile

from email_service.templates import password_reset_email, verify_email_email
from email_service.utils import send_email
from .models import AuthUser
from .utils import verify_apple_id_token, verify_google_id_token

User = get_user_model()


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def create(self, validated_data):
        user = User.objects.filter(email__iexact=validated_data["email"]).first()
        if user is None or not user.check_password(validated_data["password"]):
            raise exceptions.AuthenticationFailed("Invalid email or password.")
        if not user.is_active:
            raise exceptions.AuthenticationFailed(
                "Account not verified. Please check your email for a verification link."
            )
        refresh = RefreshToken.for_user(user)
        user.access_token = str(refresh.access_token)
        user.refresh_token = str(refresh)
        return user


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)

    id = serializers.IntegerField(read_only=True)
    email = serializers.CharField(read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def create(self, validated_data):
        id_info = verify_google_id_token(validated_data["id_token"])
        user, _, name = AuthUser.objects.create_from_google_id_info(id_info)
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"name": name, "picture": id_info.get("picture")},
        )
        if not created and not profile.has_uploaded_picture:
            profile.picture = id_info.get("picture")
            profile.save(update_fields=["picture"])
        refresh = RefreshToken.for_user(user)
        user.access_token = str(refresh.access_token)
        user.refresh_token = str(refresh)
        return user


class AppleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    id = serializers.IntegerField(read_only=True)
    email = serializers.CharField(read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def create(self, validated_data):
        decoded = verify_apple_id_token(validated_data["id_token"])
        user, created, name = AuthUser.objects.create_from_apple_id_info(
            decoded,
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
        )
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        profile, profile_created = UserProfile.objects.get_or_create(user=user, defaults={"name": name})
        if not profile_created and (validated_data.get("first_name") or validated_data.get("last_name")):
            profile.name = name
            profile.save(update_fields=["name"])
        refresh = RefreshToken.for_user(user)
        user.access_token = str(refresh.access_token)
        user.refresh_token = str(refresh)
        return user


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists. "
                "If you signed up with Google or Apple, please sign in with Google or Apple instead."
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
        verify_url = f"https://diplicity.com/verify-email?uid={uid}&token={token}"

        send_email(
            to=user.email,
            subject="Verify your Diplicity account",
            html=verify_email_email(verify_url),
        )
        return user


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def create(self, validated_data):
        user = User.objects.filter(email__iexact=validated_data["email"], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"https://diplicity.com/reset-password?uid={uid}&token={token}"

            send_email(
                to=user.email,
                subject="Reset your Diplicity password",
                html=password_reset_email(reset_url),
            )
        return validated_data


class VerifyEmailSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate_uid(self, value):
        try:
            user_id = force_str(urlsafe_base64_decode(value))
            return User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid verification link.")

    def validate(self, attrs):
        if not default_token_generator.check_token(attrs["uid"], attrs["token"]):
            raise serializers.ValidationError("Invalid or expired verification token.")
        return attrs

    def create(self, validated_data):
        user = validated_data["uid"]
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_uid(self, value):
        try:
            user_id = force_str(urlsafe_base64_decode(value))
            return User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid or expired reset link.")

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        if not default_token_generator.check_token(attrs["uid"], attrs["token"]):
            raise serializers.ValidationError("Invalid or expired reset link.")

        return attrs

    def create(self, validated_data):
        user = validated_data["uid"]
        user.set_password(validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
