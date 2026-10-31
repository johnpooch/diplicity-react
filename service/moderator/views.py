from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions

from common.views import LoaderDetailView, LoaderListView

from .filters import ModerationReportFilterSet
from .policies import ModeratorPolicy
from .serializers import ModerationReportOutputSerializer


class ModerationReportListView(LoaderListView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModerationReportOutputSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ModerationReportFilterSet

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not ModeratorPolicy.decide(None, request.user):
            raise Http404


class ModerationReportDetailView(LoaderDetailView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModerationReportOutputSerializer
