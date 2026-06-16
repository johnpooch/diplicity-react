import pytest
from django.utils import timezone
from rest_framework import status
from common.constants import GameStatus, PhaseStatus
from draw_proposal.models import DrawProposal, DrawVote
from draw_proposal.constants import DrawProposalStatus
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
            game=game, created_by=m1, phase=phase,
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
            game=game, created_by=m1, phase=phase,
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
            game=game, created_by=m1, phase=phase,
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
            game=game, created_by=m1, phase=phase1,
            included_member_ids=[m1.id, m2.id],
        )
        phase_factory(game=game, ordinal=2)

        assert proposal.status == DrawProposalStatus.EXPIRED

    def test_status_rejected_when_cancelled(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id], cancelled=True,
        )

        assert proposal.status == DrawProposalStatus.REJECTED

    def test_included_members_excludes_non_included_votes(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        included = proposal.included_members
        assert m1 in included
        assert m2 in included
        assert m3 not in included


class TestDrawProposalManager:
    def test_create_proposal_includes_all_active_non_cd_members(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        other = member_factory(game=game)
        third = member_factory(game=game)

        proposal = DrawProposal.objects.create_proposal(
            game=game, created_by=proposer,
        )

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

    def test_create_proposal_marks_cd_members_as_excluded_and_auto_accepted(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder = True
        cd_member.save()

        proposal = DrawProposal.objects.create_proposal(
            game=game, created_by=proposer,
        )

        cd_vote = proposal.votes.get(member=cd_member)
        assert cd_vote.included is False
        assert cd_vote.accepted is True

    def test_create_proposal_excludes_eliminated_and_kicked_members(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        eliminated = member_factory(game=game, eliminated=True)
        kicked = member_factory(game=game, kicked=True)

        proposal = DrawProposal.objects.create_proposal(
            game=game, created_by=proposer,
        )

        assert proposal.votes.count() == 1
        assert proposal.votes.first().member == proposer
        assert not proposal.votes.filter(member=eliminated).exists()
        assert not proposal.votes.filter(member=kicked).exists()

    def test_active_queryset_excludes_cancelled(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game)
        m2 = member_factory(game=game)

        active_proposal = draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        cancelled_proposal = draw_proposal_factory(
            game=game, created_by=m2, phase=phase,
            included_member_ids=[m1.id, m2.id], cancelled=True,
        )

        active = DrawProposal.objects.active()
        assert active_proposal in active
        assert cancelled_proposal not in active


class TestDrawProposalProcessAcceptance:
    def test_creates_victory_for_included_members_only(
        self, game_factory, phase_factory, member_factory, supply_center_factory, draw_proposal_factory
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
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        for vote in proposal.votes.all():
            vote.accepted = True
            vote.save()

        victory = proposal.process_acceptance()

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

    def test_cd_member_not_in_victory(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game)
        active_other = member_factory(game=game)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder = True
        cd_member.save()

        proposal = DrawProposal.objects.create_proposal(
            game=game, created_by=proposer,
        )
        # Active other accepts; CD member already auto-accepted.
        vote = proposal.votes.get(member=active_other)
        vote.accepted = True
        vote.save()

        victory = proposal.process_acceptance()

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
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        victory = proposal.process_acceptance()
        assert victory is None


class TestDrawProposalCreateView:
    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_create_proposal_success_with_empty_body(
        self, api_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)
        self._auth(api_client, primary_user)

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/", {}, format="json",
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
        api_client, game_factory, phase_factory, member_factory,
        supply_center_factory, primary_user,
    ):
        # Under DIAS, there is no SC threshold for proposing a draw.
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        # Combined SCs (4) far below the old victory threshold (18).
        for _ in range(2):
            supply_center_factory(phase=phase)

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/", {}, format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_proposal_fails_in_sandbox_game(
        self, api_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18, sandbox=True)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)
        self._auth(api_client, primary_user)

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/", {}, format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_proposal_fails_if_member_already_has_active_proposal(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id],
        )

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/", {}, format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_proposal_cd_members_get_excluded_and_auto_accepted(
        self, api_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder = True
        cd_member.save()

        self._auth(api_client, primary_user)
        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/", {}, format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        proposal = DrawProposal.objects.first()
        cd_vote = proposal.votes.get(member=cd_member)
        assert cd_vote.included is False
        assert cd_vote.accepted is True


class TestDrawProposalVoteView:
    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_vote_accept_success(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is True

    def test_vote_reject_success(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is False

    def test_vote_creates_victory_when_all_accept(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert Victory.objects.count() == 1
        victory = Victory.objects.first()
        assert victory.members.count() == 2

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED

    def test_vote_fails_if_already_voted(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        vote.accepted = True
        vote.save()

        self._auth(api_client, primary_user)
        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False}, format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDrawProposalCancelView:
    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_cancel_own_proposal_success(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.delete(
            f"/games/{game.id}/draw-proposals/{proposal.id}/cancel/",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        proposal.refresh_from_db()
        assert proposal.cancelled is True
        assert proposal.status == DrawProposalStatus.REJECTED

    def test_cannot_cancel_others_proposal(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user, secondary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=secondary_user)
        member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id],
        )
        self._auth(api_client, primary_user)

        response = api_client.delete(
            f"/games/{game.id}/draw-proposals/{proposal.id}/cancel/",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDrawProposalListView:
    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_list_proposals_for_current_phase(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase1 = phase_factory(game=game, ordinal=1)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        draw_proposal_factory(
            game=game, created_by=m1, phase=phase1,
            included_member_ids=[m1.id, m2.id],
        )
        phase2 = phase_factory(game=game, ordinal=2)
        new_proposal = draw_proposal_factory(
            game=game, created_by=m2, phase=phase2,
            included_member_ids=[m1.id, m2.id],
        )

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == new_proposal.id

    def test_list_excludes_cancelled_proposals(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        active = draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        draw_proposal_factory(
            game=game, created_by=m2, phase=phase,
            included_member_ids=[m1.id, m2.id], cancelled=True,
        )

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == active.id

    def test_list_response_no_longer_includes_combined_sc_count_or_threshold(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )
        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        item = response.data[0]
        assert "combined_sc_count" not in item
        assert "victory_threshold" not in item


class TestDrawProposalSecretVoting:
    def _auth(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_list_response_does_not_expose_per_member_votes(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id, m3.id],
        )
        # m2 has accepted; m3 has not yet voted.
        vote = proposal.votes.get(member=m2)
        vote.accepted = True
        vote.save()

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        item = response.data[0]
        assert "votes" not in item
        assert item["accepted_count"] == 2  # proposer m1 + m2
        assert item["rejected_count"] == 0
        assert item["pending_count"] == 1  # m3
        assert item["total_votes"] == 3

    def test_list_response_includes_included_member_ids(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)
        m3 = member_factory(game=game)

        draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        item = response.data[0]
        assert set(item["included_member_ids"]) == {m1.id, m2.id}
        assert m3.id not in item["included_member_ids"]

    def test_list_response_my_vote_reflects_current_user(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user, secondary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=secondary_user)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        # voter rejects.
        vote = proposal.votes.get(member=voter)
        vote.accepted = False
        vote.save()

        self._auth(api_client, primary_user)
        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        item = response.data[0]
        assert item["my_vote"] == {"included": True, "accepted": False}

    def test_vote_response_does_not_expose_per_member_votes(
        self, api_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )
        self._auth(api_client, primary_user)
        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "votes" not in response.data
        assert response.data["my_vote"] == {"included": True, "accepted": False}
