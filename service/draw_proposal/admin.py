from django.contrib import admin
from draw_proposal.models import DrawProposal, DrawVote


@admin.register(DrawProposal)
class DrawProposalAdmin(admin.ModelAdmin):
    list_display = ["id", "game", "created_by", "phase", "status", "cancelled", "created_at"]
    list_filter = ["cancelled", "created_at"]
    raw_id_fields = ["game", "created_by", "phase"]


@admin.register(DrawVote)
class DrawVoteAdmin(admin.ModelAdmin):
    list_display = ["id", "proposal", "member", "included", "accepted", "created_at"]
    list_filter = ["included", "accepted", "created_at"]
    raw_id_fields = ["proposal", "member"]
