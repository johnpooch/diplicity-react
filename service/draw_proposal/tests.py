import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from common.constants import GameStatus, PhaseStatus
from common.policies import Refused
from draw_proposal.models import DrawProposal, DrawVote
from draw_proposal.constants import DrawProposalStatus
from notification.models import Notification
from phase.models import Phase
from victory.models import Victory


class TestDrawProposalModel:
    def test_status_pending_when_votes_have_not_resolved(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        assert proposal.status == DrawProposalStatus.PENDING

    def test_status_accepted_when_all_accept(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        for vote in proposal.votes.all():
            vote.accepted = True
            vote.save()

        assert proposal.status == DrawProposalStatus.ACCEPTED

    def test_status_rejected_when_any_reject(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        vote = proposal.votes.filter(member=m2).first()
        vote.accepted = False
        vote.save()

        assert proposal.status == DrawProposalStatus.REJECTED

    def test_status_expired_when_phase_changes(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase1 = phase_factory(game=game, ordinal=1)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase1,
            included_member_ids=[m1.id, m2.id],
        )
        phase_factory(game=game, ordinal=2)

        assert proposal.status == DrawProposalStatus.EXPIRED

    def test_status_cancelled_when_cancelled(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
            cancelled_at=timezone.now(),
        )

        assert proposal.status == DrawProposalStatus.CANCELLED

    def test_included_members_excludes_non_included_votes(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        included = proposal.included_members
        assert m1 in included
        assert m2 in included
        assert m3 not in included


class TestDrawProposalManager:
    def test_propose_includes_all_active_non_cd_members(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        other = member_factory(game=game)
        third = member_factory(game=game)

        proposal = DrawProposal.objects.propose(game, proposer.user)

        assert proposal.phase == phase
        assert proposal.votes.count() == 3

        vote_proposer = proposal.votes.get(member=proposer)
        assert vote_proposer.included is True
        assert vote_proposer.accepted is True

        vote_other = proposal.votes.get(member=other)
        assert vote_other.included is True
        assert vote_other.accepted is None

        vote_third = proposal.votes.get(member=third)
        assert vote_third.included is True
        assert vote_third.accepted is None

    def test_propose_marks_cd_members_as_excluded_and_auto_accepted(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder_at = timezone.now()
        cd_member.save()

        proposal = DrawProposal.objects.propose(game, proposer.user)

        cd_vote = proposal.votes.get(member=cd_member)
        assert cd_vote.included is False
        assert cd_vote.accepted is True

    def test_propose_excludes_eliminated_and_replaced_members(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        other = member_factory(game=game)
        eliminated = member_factory(game=game, eliminated_at=timezone.now())
        replacement = member_factory(game=game)
        replaced = member_factory(
            game=game, removed_at=timezone.now(), replaced_by=replacement
        )

        proposal = DrawProposal.objects.propose(game, proposer.user)

        assert proposal.votes.count() == 3
        assert set(proposal.votes.values_list("member_id", flat=True)) == {
            proposer.id,
            other.id,
            replacement.id,
        }
        assert not proposal.votes.filter(member=eliminated).exists()
        assert not proposal.votes.filter(member=replaced).exists()

    def test_propose_auto_accepts_for_kicked_members(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        member_factory(game=game)
        kicked = member_factory(game=game, removed_at=timezone.now())

        proposal = DrawProposal.objects.propose(game, proposer.user)

        vote = proposal.votes.get(member=kicked)
        assert vote.accepted is True
        assert vote.included is False

    def test_active_queryset_excludes_cancelled(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        active_proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        cancelled_proposal = draw_proposal_factory(
            game=game,
            created_by=m2,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
            cancelled_at=timezone.now(),
        )

        active = DrawProposal.objects.active()
        assert active_proposal in active
        assert cancelled_proposal not in active

    def test_propose_refuses_while_another_proposal_is_pending(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        other = member_factory(game=game)
        draw_proposal_factory(
            game=game,
            created_by=other,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )

        with pytest.raises(Refused) as refused:
            DrawProposal.objects.propose(game, proposer.user)

        assert refused.value.decision.reason == "proposal_pending"
        assert DrawProposal.objects.count() == 1


class TestDrawProposalConclude:
    def test_creates_victory_for_included_members_only(
        self,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        draw_proposal_factory,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        future = timezone.now() + timezone.timedelta(hours=20)
        phase = phase_factory(game=game, scheduled_resolution=future)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=m1.nation)
        for _ in range(8):
            supply_center_factory(phase=phase, nation=m2.nation)
        for _ in range(5):
            supply_center_factory(phase=phase, nation=m3.nation)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        for vote in proposal.votes.all():
            vote.accepted = True
            vote.save()

        victory = DrawProposal.objects.conclude(proposal)

        assert victory is not None
        assert victory.members.count() == 2
        assert m1 in victory.members.all()
        assert m2 in victory.members.all()
        assert m3 not in victory.members.all()

        m1.refresh_from_db()
        m2.refresh_from_db()
        m3.refresh_from_db()
        assert m1.drew is True
        assert m2.drew is True
        assert m3.drew is False

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.COMPLETED
        assert phase.scheduled_resolution is None

    def test_completes_every_phase_of_the_game(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        future = timezone.now() + timezone.timedelta(hours=20)
        stale_phase = phase_factory(game=game, scheduled_resolution=future)
        phase = phase_factory(
            game=game, ordinal=stale_phase.ordinal + 1, scheduled_resolution=future
        )
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        for vote in proposal.votes.all():
            vote.accepted = True
            vote.save()

        assert DrawProposal.objects.conclude(proposal) is not None

        stale_phase.refresh_from_db()
        assert stale_phase.status == PhaseStatus.COMPLETED
        assert stale_phase.scheduled_resolution is None

    def test_cd_member_not_in_victory(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        active_other = member_factory(game=game)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder_at = timezone.now()
        cd_member.save()

        proposal = DrawProposal.objects.propose(game, proposer.user)
        vote = proposal.votes.get(member=active_other)
        vote.accepted = True
        vote.save()

        victory = DrawProposal.objects.conclude(proposal)

        assert victory is not None
        assert proposer in victory.members.all()
        assert active_other in victory.members.all()
        assert cd_member not in victory.members.all()

        cd_member.refresh_from_db()
        assert cd_member.drew is False

    def test_returns_none_when_not_accepted(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        victory = DrawProposal.objects.conclude(proposal)
        assert victory is None

    def test_returns_none_when_phase_is_being_resolved(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        for vote in proposal.votes.all():
            vote.accepted = True
            vote.save()

        Phase.objects.filter(pk=phase.pk).update(status=PhaseStatus.PROCESSING)

        assert DrawProposal.objects.conclude(proposal) is None
        assert Victory.objects.count() == 0

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE

    def test_concluding_notifies_players_of_the_draw(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        proposal.votes.update(accepted=True)

        DrawProposal.objects.conclude(proposal)

        recipients = set(
            Notification.objects.filter(event_type="game_draw").values_list(
                "recipient_id", flat=True
            )
        )
        assert recipients == {m1.user_id, m2.user_id}


class TestDrawProposalReleaseMember:
    def test_release_member_cancels_the_members_own_pending_proposal(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member = member_factory(game=game)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=member,
            phase=phase,
            included_member_ids=[member.id, other.id],
        )

        DrawProposal.objects.release_member(phase, member)

        proposal.refresh_from_db()
        assert proposal.cancelled is True

    def test_release_member_accepts_other_proposals_without_inclusion(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        member = member_factory(game=game)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, member.id, other.id],
        )

        DrawProposal.objects.release_member(phase, member)

        vote = proposal.votes.get(member=member)
        assert vote.accepted is True
        assert vote.included is False
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE

    def test_release_member_completes_a_draw_only_the_member_was_holding_up(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        member = member_factory(game=game)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, member.id, other.id],
        )
        proposal.votes.filter(member=other).update(accepted=True)

        DrawProposal.objects.release_member(phase, member)

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        victory = Victory.objects.get(game=game)
        assert set(victory.members.all()) == {proposer, other}


class TestDrawProposalCreateView:
    def _auth(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_create_proposal_success_with_empty_body(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        self._auth(api_client, primary_user)

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert DrawProposal.objects.count() == 1
        proposal = DrawProposal.objects.first()
        assert proposal.created_by == proposer
        assert proposal.votes.filter(included=True).count() == 2
        assert proposal.votes.get(member=proposer).accepted is True
        assert proposal.votes.get(member=other).accepted is None

    def test_create_proposal_succeeds_below_old_sc_threshold(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        for _ in range(2):
            supply_center_factory(phase=phase)

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_proposal_fails_in_sandbox_game(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18, sandbox=True)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)
        self._auth(api_client, primary_user)

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_proposal_fails_for_civil_disorder_member(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user, civil_disorder_at=timezone.now())
        member_factory(game=game)
        self._auth(api_client, primary_user)

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert DrawProposal.objects.count() == 0

    def test_create_proposal_fails_if_member_already_has_active_proposal(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id],
        )

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_proposal_fails_while_another_players_proposal_is_pending(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        draw_proposal_factory(
            game=game,
            created_by=other,
            phase=phase,
            included_member_ids=[member.id, other.id],
        )

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert DrawProposal.objects.count() == 1

    def test_create_proposal_succeeds_after_another_players_proposal_is_rejected(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        rejected = draw_proposal_factory(
            game=game,
            created_by=other,
            phase=phase,
            included_member_ids=[member.id, other.id],
        )
        rejected.votes.filter(member=member).update(accepted=False)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_proposal_succeeds_after_another_players_proposal_is_cancelled(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        draw_proposal_factory(
            game=game,
            created_by=other,
            phase=phase,
            included_member_ids=[member.id, other.id],
            cancelled_at=timezone.now(),
        )

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_proposal_fails_if_member_already_proposed_a_rejected_draw_this_phase(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        rejected = draw_proposal_factory(
            game=game,
            created_by=member,
            phase=phase,
            included_member_ids=[member.id, other.id],
        )
        rejected.votes.filter(member=other).update(accepted=False)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_proposal_cd_members_get_excluded_and_auto_accepted(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder_at = timezone.now()
        cd_member.save()

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        proposal = DrawProposal.objects.first()
        cd_vote = proposal.votes.get(member=cd_member)
        assert cd_vote.included is False
        assert cd_vote.accepted is True

    def test_create_proposal_fails_while_phase_is_being_resolved(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game, status=PhaseStatus.PROCESSING)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert DrawProposal.objects.count() == 0

    def test_create_proposal_fails_for_non_player(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        member_factory(game=game)
        member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "not_player"}

    def test_create_proposal_fails_for_withdrawn_player(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user, withdrawn_at=timezone.now())
        member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "inactive_player"}
        assert DrawProposal.objects.count() == 0

    def test_create_proposal_fails_in_finished_game(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(
            variant__solo_victory_sc_count=18, status=GameStatus.COMPLETED
        )
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "game_not_active"}

    def test_create_proposal_refusal_names_the_rule(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        rejected = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )
        rejected.votes.filter(member=other).update(accepted=False)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.data == {"code": "already_proposed"}

    def test_create_proposal_fails_for_game_that_has_not_started(
        self,
        authenticated_client,
        game_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(
            variant__solo_victory_sc_count=18, status=GameStatus.PENDING
        )
        member_factory(game=game, user=primary_user)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "game_not_active"}

    def test_create_proposal_ends_the_game_when_every_other_seat_is_vacant(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game, civil_disorder_at=timezone.now())
        member_factory(game=game, withdrawn_at=timezone.now())

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == DrawProposalStatus.ACCEPTED
        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        assert list(Victory.objects.get(game=game).members.all()) == [proposer]

    def test_create_proposal_notifies_other_active_players(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        member_factory(game=game, eliminated_at=timezone.now())

        authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]),
            {},
            format="json",
        )

        recipients = set(
            Notification.objects.filter(event_type="draw_proposal").values_list(
                "recipient_id", flat=True
            )
        )
        assert recipients == {other.user_id}


class TestDrawProposalVoteView:
    def _auth(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_vote_accept_success(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is True

    def test_vote_reject_success(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is False

    def test_rejecting_notifies_included_players_except_the_voter(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)
        bystander = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id, bystander.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        recipients = set(
            Notification.objects.filter(
                event_type="draw_proposal_rejected"
            ).values_list("recipient_id", flat=True)
        )
        assert recipients == {proposer.user_id, bystander.user_id}

    def test_accepting_sends_no_rejection_notification(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True},
            format="json",
        )

        assert not Notification.objects.filter(
            event_type="draw_proposal_rejected"
        ).exists()

    def test_vote_creates_victory_when_all_accept(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert Victory.objects.count() == 1
        victory = Victory.objects.first()
        assert victory.members.count() == 2

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED

    def test_vote_fails_if_already_voted(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        vote.accepted = True
        vote.save()

        self._auth(api_client, primary_user)
        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_vote_fails_while_phase_is_being_resolved(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, status=PhaseStatus.PROCESSING)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Victory.objects.count() == 0

    def test_vote_accepts_put(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)
        member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        response = authenticated_client.put(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["my_vote"] == {"included": True, "accepted": True}

    def test_vote_without_accepted_is_invalid(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert proposal.votes.get(member=voter).accepted is None

    def test_vote_fails_for_player_who_joined_after_the_proposal(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )
        member_factory(game=game, user=primary_user)

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "no_vote"}

    def test_vote_fails_on_a_rejected_proposal(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)
        rejecter = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id, rejecter.id],
        )
        proposal.votes.filter(member=rejecter).update(accepted=False)

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "not_pending"}

    def test_vote_fails_for_non_player(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "not_player"}

    def test_vote_on_a_proposal_from_another_game_is_not_found(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        other_game = game_factory(variant__solo_victory_sc_count=18)
        other_phase = phase_factory(game=other_game)
        proposer = member_factory(game=other_game)
        voter = member_factory(game=other_game)
        proposal = draw_proposal_factory(
            game=other_game,
            created_by=proposer,
            phase=other_phase,
            included_member_ids=[proposer.id, voter.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDrawProposalCancelView:
    def _auth(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_cancel_own_proposal_success(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.delete(
            f"/games/{game.id}/draw-proposals/{proposal.id}/cancel/",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        proposal.refresh_from_db()
        assert proposal.cancelled_at is not None
        assert proposal.status == DrawProposalStatus.CANCELLED

    def test_cannot_cancel_a_rejected_proposal(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )
        proposal.votes.filter(member=other).update(accepted=False)

        response = authenticated_client.delete(
            reverse("draw-proposal-cancel", args=[game.id, proposal.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        proposal.refresh_from_db()
        assert proposal.status == DrawProposalStatus.REJECTED

    def test_cannot_cancel_others_proposal(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
        secondary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=secondary_user)
        member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.delete(
            f"/games/{game.id}/draw-proposals/{proposal.id}/cancel/",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "not_proposer"}

    def test_cannot_cancel_an_already_cancelled_proposal(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            cancelled_at=timezone.now(),
        )

        response = authenticated_client.delete(
            reverse("draw-proposal-cancel", args=[game.id, proposal.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "not_pending"}

    def test_cancel_own_proposal_while_phase_is_being_resolved(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, status=PhaseStatus.PROCESSING)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )

        response = authenticated_client.delete(
            reverse("draw-proposal-cancel", args=[game.id, proposal.id])
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        proposal.refresh_from_db()
        assert proposal.cancelled is True


class TestDrawProposalListView:
    def _auth(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_list_includes_proposals_from_earlier_phases_as_expired(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase1 = phase_factory(game=game, ordinal=1)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        old_proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase1,
            included_member_ids=[m1.id, m2.id],
        )
        phase2 = phase_factory(game=game, ordinal=2)
        new_proposal = draw_proposal_factory(
            game=game,
            created_by=m2,
            phase=phase2,
            included_member_ids=[m1.id, m2.id],
        )

        response = authenticated_client.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert [(p["id"], p["status"]) for p in response.data] == [
            (new_proposal.id, DrawProposalStatus.PENDING),
            (old_proposal.id, DrawProposalStatus.EXPIRED),
        ]
        assert response.data[1]["phase_id"] == phase1.id
        assert response.data[1]["phase_name"] == phase1.name

    def test_list_keeps_earlier_phase_rejection_as_rejected(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase1 = phase_factory(game=game, ordinal=1)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase1,
            included_member_ids=[m1.id, m2.id],
        )
        proposal.votes.filter(member=m2).update(accepted=False)
        phase_factory(game=game, ordinal=2)

        response = authenticated_client.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        assert response.data[0]["status"] == DrawProposalStatus.REJECTED

    def test_list_counts_only_players_included_in_the_draw(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)
        member_factory(game=game, civil_disorder_at=timezone.now())
        member_factory(game=game, civil_disorder_at=timezone.now())
        DrawProposal.objects.propose(game, proposer.user)

        response = authenticated_client.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        item = response.data[0]
        assert item["accepted_count"] == 1
        assert item["pending_count"] == 1
        assert item["total_votes"] == 2

    def test_list_query_count_does_not_grow_with_proposal_history(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)
        url = reverse("draw-proposal-list", args=[game.id])

        def add_proposal(ordinal):
            phase = phase_factory(game=game, ordinal=ordinal)
            draw_proposal_factory(
                game=game,
                created_by=m1,
                phase=phase,
                included_member_ids=[m1.id, m2.id],
            )

        add_proposal(1)
        with CaptureQueriesContext(connection) as single:
            authenticated_client.get(url)

        add_proposal(2)
        add_proposal(3)
        with CaptureQueriesContext(connection) as several:
            response = authenticated_client.get(url)

        assert len(response.data) == 3
        assert len(several) == len(single)

    def test_list_includes_cancelled_proposals_as_cancelled(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        pending = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        cancelled = draw_proposal_factory(
            game=game,
            created_by=m2,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
            cancelled_at=timezone.now(),
        )

        response = authenticated_client.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert [(p["id"], p["status"]) for p in response.data] == [
            (cancelled.id, DrawProposalStatus.CANCELLED),
            (pending.id, DrawProposalStatus.PENDING),
        ]

    def test_list_proposals_as_non_member(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
        secondary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        self._auth(api_client, secondary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == proposal.id
        assert response.data[0]["my_vote"] is None

    def test_list_response_no_longer_includes_combined_sc_count_or_threshold(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        item = response.data[0]
        assert "combined_sc_count" not in item
        assert "victory_threshold" not in item

    def test_list_is_empty_for_a_game_that_has_not_started(
        self,
        authenticated_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(
            variant__solo_victory_sc_count=18, status=GameStatus.PENDING
        )
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        draw_proposal_factory(game=game, created_by=m1, phase=phase)

        response = authenticated_client.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_masks_the_proposer_in_an_anonymous_game(
        self,
        authenticated_client_for_secondary_user,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
        secondary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18, anonymous=True)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game, user=secondary_user)
        draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, other.id],
        )

        response = authenticated_client_for_secondary_user.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        created_by = response.data[0]["created_by"]
        assert created_by["name"] == "Anonymous"
        assert created_by["picture"] is None


class TestDrawProposalSecretVoting:
    def _auth(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_list_response_does_not_expose_per_member_votes(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id, m3.id],
        )
        vote = proposal.votes.get(member=m2)
        vote.accepted = True
        vote.save()

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        item = response.data[0]
        assert "votes" not in item
        assert item["accepted_count"] == 2
        assert item["rejected_count"] == 0
        assert item["pending_count"] == 1
        assert item["total_votes"] == 3

    def test_list_response_includes_included_member_ids(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        draw_proposal_factory(
            game=game,
            created_by=m1,
            phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        item = response.data[0]
        assert set(item["included_member_ids"]) == {m1.id, m2.id}
        assert m3.id not in item["included_member_ids"]

    def test_list_response_my_vote_reflects_current_user(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
        secondary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=secondary_user)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        vote = proposal.votes.get(member=voter)
        vote.accepted = False
        vote.save()

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        item = response.data[0]
        assert item["my_vote"] == {"included": True, "accepted": False}

    def test_vote_response_does_not_expose_per_member_votes(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)
        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "votes" not in response.data
        assert response.data["my_vote"] == {"included": True, "accepted": False}
