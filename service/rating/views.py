from django.utils import timezone
from rest_framework import permissions

from common.views import LoaderListView

from .models import Rating
from .pagination import LeaderboardPagination
from .serializers import LeaderboardEntryOutputSerializer


class LeaderboardListView(LoaderListView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LeaderboardEntryOutputSerializer
    pagination_class = LeaderboardPagination

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.now = timezone.now()

    def get_queryset(self):
        return super().get_queryset().established(self.now).ranked()

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data, own=self.get_own_entry())

    def get_own_entry(self):
        own = super().get_queryset().established(self.now).filter(
            user=self.request.user
        )
        entries = self.get_loader().hydrate(own, self.request.user)
        if not entries:
            return None
        entry = entries[0]
        entry.rank = Rating.objects.established(self.now).rank_of(entry)
        return self.get_serializer(entry).data
