from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from common.views import CreateActionView
from member.models import Member

from .constants import ReportReason
from .models import Report
from .serializers import (
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
