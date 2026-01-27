from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .serializers import AuthSerializer

# LSP TEST: This should show a type error - assigning int to str
lsp_test_error: str = 123


class AuthView(CreateAPIView):
    serializer_class = AuthSerializer
    permission_classes = [AllowAny]