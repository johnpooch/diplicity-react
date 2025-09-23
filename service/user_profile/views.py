from rest_framework import permissions, generics

from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return UserProfile.objects.with_related_data().get(user=self.request.user)
