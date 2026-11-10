from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from common.views import (
    ActionView,
    CreateActionView,
    LoaderDetailView,
    LoaderListView,
)
from member.models import Member

from .constants import ReportReason
from .filters import ModerationReportFilterSet
from .models import Report
from .policies import ModeratorPolicy
from .serializers import (
    ModerationReportOutputSerializer,
    ReportApproveInputSerializer,
    ReportDecisionInputSerializer,
    ReportMemberInputSerializer,
    ReportOutputSerializer,
    ReportReasonSerializer,
)


class ReportReasonListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReportReasonSerializer

    def get_queryset(self):
        return ReportReason.REASONS


class ReportCreateView(CreateActionView):
    permission_classes = [permissions.IsAuthenticated]
    input_serializer_class = ReportMemberInputSerializer
    serializer_class = ReportOutputSerializer

    def perform(self, reason, note):
        member = get_object_or_404(
            Member, game_id=self.kwargs["game_id"], id=self.kwargs["member_id"]
        )
        return Report.objects.report(member, self.request.user, reason, note)


class ModeratorOnlyMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not ModeratorPolicy.decide(None, request.user):
            raise Http404


class ModerationReportListView(ModeratorOnlyMixin, LoaderListView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModerationReportOutputSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ModerationReportFilterSet


class ModerationReportDetailView(ModeratorOnlyMixin, LoaderDetailView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModerationReportOutputSerializer


class ModerationReportAssignView(ModeratorOnlyMixin, ActionView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    serializer_class = ModerationReportOutputSerializer

    def perform(self, report):
        return Report.objects.assign(report, self.request.user)


class ModerationReportUnassignView(ModeratorOnlyMixin, ActionView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    serializer_class = ModerationReportOutputSerializer

    def perform(self, report):
        return Report.objects.unassign(report, self.request.user)


class ModerationReportApproveView(ModeratorOnlyMixin, ActionView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    input_serializer_class = ReportApproveInputSerializer
    serializer_class = ModerationReportOutputSerializer

    def perform(self, report, note, reason=None):
        return Report.objects.approve(report, self.request.user, note, reason)


class ModerationReportRejectView(ModeratorOnlyMixin, ActionView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    input_serializer_class = ReportDecisionInputSerializer
    serializer_class = ModerationReportOutputSerializer

    def perform(self, report, note):
        return Report.objects.reject(report, self.request.user, note)
