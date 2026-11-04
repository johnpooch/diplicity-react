from rest_framework import permissions

from common.views import LoaderDetailView, SelectedGameMixin

from .serializers import RatingResultOutputSerializer


class MemberRatingRetrieveView(SelectedGameMixin, LoaderDetailView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RatingResultOutputSerializer
    lookup_field = "member_id"

    def get_queryset(self):
        return super().get_queryset().filter(member__game=self.get_game())
