from rest_framework import status, views, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .. import services
from ..serializers import UserProfileSerializer


class UserProfileRetrieveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        user_profile_service = services.UserProfileService(request.user)
        profile = user_profile_service.retrieve()
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
