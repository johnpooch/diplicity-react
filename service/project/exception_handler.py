from django.contrib.auth import get_user_model
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken


def custom_exception_handler(exc, context):
    # simplejwt's TokenRefreshSerializer calls User.objects.get() without catching
    # DoesNotExist when the token's user has been deleted; convert to 401.
    if isinstance(exc, get_user_model().DoesNotExist):
        exc = InvalidToken()
    return exception_handler(exc, context)
