from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from user_profile.models import UserProfile

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
        user = User.objects.filter(email=validated_data["email"]).first()
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
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"name": id_info.get("name"), "picture": id_info.get("picture")},
        )
        if not created:
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
        if created or validated_data.get("first_name") or validated_data.get("last_name"):
            UserProfile.objects.get_or_create(user=user, defaults={"name": name})
        elif not hasattr(user, "profile"):
            UserProfile.objects.create(user=user, name=name)
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
        verify_url = f"https://diplicity.com/verify-email?uid={uid}&token={token}"
        logo_url = "https://diplicity.com/otto.png"

        html = """<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <title>Verify your Diplicity account</title>
  <!--[if mso]>
  <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
  <![endif]-->
  <style>
    @media only screen and (max-width: 480px) {
      .container { width: 100% !important; padding: 24px 20px !important; }
      .h1        { font-size: 28px !important; line-height: 1.15 !important; }
      .btn-a     { display: block !important; width: 100% !important; box-sizing: border-box; }
      .stamp     { font-size: 10px !important; }
      .pad-md    { padding: 28px 22px !important; }
    }
    a.fallback-url { color: #5b4a36 !important; text-decoration: none !important; word-break: break-all; }
  </style>
</head>
<body style="margin:0; padding:0; background:#ece4d3; font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif; color:#23201a;">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all; font-size:1px; line-height:1px; color:#ece4d3;">
    Confirm your email address. &#8199;&#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847;
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ece4d3;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" class="container" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:560px; background:#f5efe0; border:1px solid #d8cdb4;">
          <tr>
            <td style="padding: 0; border-bottom: 1px dashed #b3a685;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="left"  style="padding: 16px 28px; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color:#6b5c3f; font-family: Georgia, serif;">Diplomatic Cable</td>
                  <td align="right" style="padding: 16px 28px; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color:#6b5c3f; font-family: Georgia, serif;">No. 001 / Verification</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="pad-md" align="center" style="padding: 44px 44px 8px;">
              <img src="__LOGO_URL__" width="56" height="56" alt="Diplicity" style="display:block; width:56px; height:56px; border:0; outline:none; border-radius:50%;">
              <div class="stamp" style="margin-top: 22px; font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color:#7a6843;">&mdash; Welcome to Diplicity &mdash;</div>
              <h1 class="h1" style="margin: 14px 0 0; font-family: Georgia, 'Iowan Old Style', serif; font-weight: 400; font-size: 34px; line-height: 1.1; letter-spacing:-0.01em; color:#1c1a14;">
                Confirm your address.
              </h1>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 22px 44px 8px; font-family: Georgia, serif; font-size: 16px; line-height: 1.65; color:#3a3527;">
              <p style="margin: 0 0 14px;">Welcome to this awesome game of strategy and negotiation. Before you start, we need to confirm this email is yours.</p>
              <p style="margin: 0;">Click below to confirm.</p>
            </td>
          </tr>
          <tr>
            <td class="pad-md" align="center" style="padding: 28px 44px 8px;">
              <!--[if mso]>
                <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="__VERIFY_URL__" style="height:48px;v-text-anchor:middle;width:260px;" arcsize="8%" stroke="f" fillcolor="#1c1a14">
                  <w:anchorlock/>
                  <center style="color:#f5efe0;font-family:Georgia,serif;font-size:15px;letter-spacing:0.18em;text-transform:uppercase;">Verify Email &#8594;</center>
                </v:roundrect>
              <![endif]-->
              <!--[if !mso]><!-- -->
              <a class="btn-a" href="__VERIFY_URL__" style="display:inline-block; background:#1c1a14; color:#f5efe0; text-decoration:none; padding: 16px 36px; font-family: Georgia, serif; font-size: 14px; letter-spacing: 0.20em; text-transform: uppercase; border:1px solid #1c1a14;">
                Verify Email &nbsp;&rarr;
              </a>
              <!--<![endif]-->
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 8px; font-family: Georgia, serif; font-size: 13px; line-height: 1.6; color:#5b4a36;">
              <p style="margin:0 0 6px;">Or paste this address into your browser:</p>
              <a class="fallback-url" href="__VERIFY_URL__">__VERIFY_URL__</a>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 28px 44px 0;">
              <div style="border-top:1px dashed #b3a685; line-height:0; height:0;">&nbsp;</div>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 6px; font-family: Georgia, serif; font-size: 13px; line-height: 1.6; color:#5b4a36;">
              <p style="margin:0;"><em>If you didn&rsquo;t sign up for Diplicity, ignore this letter. No account will be created.</em></p>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 36px; font-family: Georgia, serif; font-size: 14px; line-height: 1.6; color:#3a3527;">
              <p style="margin:0;">&mdash; The Diplicity volunteers</p>
            </td>
          </tr>
        </table>
        <table role="presentation" class="container" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:560px;">
          <tr>
            <td align="center" style="padding: 22px 24px 8px; font-family: Georgia, serif; font-size: 12px; line-height: 1.6; color:#7a6843;">
              <a href="https://discord.gg/GyqEmaWS" style="color:#5b4a36; text-decoration:underline;">Discord</a>
              &nbsp;&middot;&nbsp;
              <a href="https://diplicity.com" style="color:#5b4a36; text-decoration:underline;">diplicity.com</a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 4px 24px 28px; font-family: Georgia, serif; font-size: 11px; line-height: 1.6; color:#9b8a64; letter-spacing: 0.12em; text-transform: uppercase;">
              Diplicity &middot; Since 2014 &middot; Sent because someone used this address to register
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        html = html.replace("__VERIFY_URL__", verify_url).replace("__LOGO_URL__", logo_url)

        send_email(
            to=user.email,
            subject="Verify your Diplicity account",
            html=html,
        )
        return user


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def create(self, validated_data):
        user = User.objects.filter(email=validated_data["email"], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"https://diplicity.com/reset-password?uid={uid}&token={token}"
            logo_url = "https://diplicity.com/otto.png"

            html = """<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <title>Reset your Diplicity password</title>
  <!--[if mso]>
  <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
  <![endif]-->
  <style>
    @media only screen and (max-width: 480px) {
      .container { width: 100% !important; padding: 24px 20px !important; }
      .pad-md    { padding: 28px 22px !important; }
      .h1        { font-size: 28px !important; line-height: 1.15 !important; }
      .btn-a     { display: block !important; width: 100% !important; box-sizing: border-box; }
    }
    a.fallback-url { color: #5b4a36 !important; text-decoration: none !important; word-break: break-all; }
  </style>
</head>
<body style="margin:0; padding:0; background:#ece4d3; font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif; color:#23201a;">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all; font-size:1px; line-height:1px; color:#ece4d3;">
    A new password is one click away &mdash; the link expires in an hour. &#8199;&#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847; &zwnj; &nbsp; &#847;
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ece4d3;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" class="container" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:560px; background:#f5efe0; border:1px solid #d8cdb4;">
          <tr>
            <td style="padding: 0; border-bottom: 1px dashed #b3a685;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="left"  style="padding: 16px 28px; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color:#6b5c3f; font-family: Georgia, serif;">Diplomatic Cable</td>
                  <td align="right" style="padding: 16px 28px; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color:#6b5c3f; font-family: Georgia, serif;">Valid for 60 min</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td class="pad-md" align="center" style="padding: 44px 44px 8px;">
              <img src="__LOGO_URL__" width="56" height="56" alt="Diplicity" style="display:block; width:56px; height:56px; border:0; outline:none; border-radius:50%;">
              <div style="margin-top: 22px; font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color:#7a6843;">&mdash; Confidential &mdash;</div>
              <h1 class="h1" style="margin: 14px 0 0; font-family: Georgia, 'Iowan Old Style', serif; font-weight: 400; font-size: 34px; line-height: 1.1; letter-spacing:-0.01em; color:#1c1a14;">
                Forgot your password?
              </h1>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 22px 44px 6px; font-family: Georgia, serif; font-size: 16px; line-height: 1.65; color:#3a3527;">
              <p style="margin: 0 0 14px;">Someone asked to reset the password for the Diplicity account tied to this address.</p>
              <p style="margin: 0;">Use the link below within the next <strong>60 minutes</strong> to set a new one.</p>
            </td>
          </tr>
          <tr>
            <td class="pad-md" align="center" style="padding: 28px 44px 6px;">
              <!--[if mso]>
                <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="__RESET_URL__" style="height:48px;v-text-anchor:middle;width:280px;" arcsize="8%" stroke="f" fillcolor="#1c1a14">
                  <w:anchorlock/>
                  <center style="color:#f5efe0;font-family:Georgia,serif;font-size:14px;letter-spacing:0.20em;text-transform:uppercase;">Reset Password &#8594;</center>
                </v:roundrect>
              <![endif]-->
              <!--[if !mso]><!-- -->
              <a class="btn-a" href="__RESET_URL__" style="display:inline-block; background:#1c1a14; color:#f5efe0; text-decoration:none; padding: 16px 36px; font-family: Georgia, serif; font-size: 14px; letter-spacing: 0.20em; text-transform: uppercase; border:1px solid #1c1a14;">
                Reset Password &nbsp;&rarr;
              </a>
              <!--<![endif]-->
            </td>
          </tr>
          <tr>
            <td class="pad-md" align="center" style="padding: 14px 44px 0; font-family: Georgia, serif; font-size: 12px; line-height: 1.6; color:#7a6843; letter-spacing: 0.10em;">
              <em>This link expires in 1 hour.</em>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 22px 44px 4px; font-family: Georgia, serif; font-size: 13px; line-height: 1.6; color:#5b4a36;">
              <p style="margin:0 0 6px;">Or paste this address into your browser:</p>
              <a class="fallback-url" href="__RESET_URL__">__RESET_URL__</a>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 28px 44px 0;">
              <div style="border-top:1px dashed #b3a685; line-height:0; height:0;">&nbsp;</div>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 6px; font-family: Georgia, serif; font-size: 13px; line-height: 1.6; color:#5b4a36;">
              <p style="margin:0;"><em>Didn&rsquo;t ask to reset your password? Ignore this message &mdash; your current password keeps working. Nobody can change it without this link.</em></p>
            </td>
          </tr>
          <tr>
            <td class="pad-md" style="padding: 18px 44px 36px; font-family: Georgia, serif; font-size: 14px; line-height: 1.6; color:#3a3527;">
              <p style="margin:0;">&mdash; The Diplicity volunteers</p>
            </td>
          </tr>
        </table>
        <table role="presentation" class="container" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:560px;">
          <tr>
            <td align="center" style="padding: 22px 24px 8px; font-family: Georgia, serif; font-size: 12px; line-height: 1.6; color:#7a6843;">
              <a href="https://discord.gg/GyqEmaWS" style="color:#5b4a36; text-decoration:underline;">Discord</a>
              &nbsp;&middot;&nbsp;
              <a href="https://diplicity.com" style="color:#5b4a36; text-decoration:underline;">diplicity.com</a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 4px 24px 28px; font-family: Georgia, serif; font-size: 11px; line-height: 1.6; color:#9b8a64; letter-spacing: 0.12em; text-transform: uppercase;">
              Diplicity &middot; Since 2014 &middot; You requested this password reset from diplicity.com
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

            html = html.replace("__RESET_URL__", reset_url).replace("__LOGO_URL__", logo_url)

            send_email(
                to=user.email,
                subject="Reset your Diplicity password",
                html=html,
            )
        return validated_data


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


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid or expired reset link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired reset link.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        user.set_password(validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
