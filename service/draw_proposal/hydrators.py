from common.loaders import Hydrator
from member.models import Member


class MyVoteHydrator(Hydrator):
    def hydrate(self, proposals, actor):
        member_ids = {}
        if actor.pk is not None:
            members = Member.objects.filter(
                game_id__in={proposal.game_id for proposal in proposals},
                user_id=actor.pk,
            ).order_by("pk")
            for member in members:
                member_ids.setdefault(member.game_id, member.id)
        for proposal in proposals:
            member_id = member_ids.get(proposal.game_id)
            proposal.my_vote = next(
                (
                    {"included": vote.included, "accepted": vote.accepted}
                    for vote in proposal.votes.all()
                    if member_id is not None and vote.member_id == member_id
                ),
                None,
            )
