import pytest
from rest_framework import status
from common.constants import GameStatus
from draw_proposal.models import DrawProposal, DrawVote
from draw_proposal.constants import DrawProposalStatus
from victory.models import Victory


class TestDrawProposalModel:
    def test_status_pending_when_no_votes_yet(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        assert proposal.status == DrawProposalStatus.PENDING

    def test_status_accepted_when_all_accept(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
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
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        vote = proposal.votes.filter(member=member2).first()
        vote.accepted = False
        vote.save()

        assert proposal.status == DrawProposalStatus.REJECTED

    def test_status_expired_when_phase_changes(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase1 = phase_factory(game=game, ordinal=1)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase1,
            included_member_ids=[member1.id, member2.id],
        )

        phase2 = phase_factory(game=game, ordinal=2)

        assert proposal.status == DrawProposalStatus.EXPIRED

    def test_status_rejected_when_cancelled(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
            cancelled=True,
        )

        assert proposal.status == DrawProposalStatus.REJECTED

    def test_combined_sc_count(
        self, game_factory, phase_factory, member_factory, supply_center_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member1.nation)
        for _ in range(8):
            supply_center_factory(phase=phase, nation=member2.nation)
        for _ in range(5):
            supply_center_factory(phase=phase, nation=member3.nation)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        assert proposal.combined_sc_count == 18

    def test_included_members(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        included = proposal.included_members
        assert len(included) == 2
        assert member1 in included
        assert member2 in included
        assert member3 not in included


class TestDrawProposalManager:
    def test_create_proposal(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        proposal = DrawProposal.objects.create_proposal(
            game=game,
            created_by=member1,
            included_member_ids=[member1.id, member2.id],
        )

        assert proposal.game == game
        assert proposal.created_by == member1
        assert proposal.phase == phase
        assert proposal.votes.count() == 3

        vote1 = proposal.votes.get(member=member1)
        assert vote1.included is True
        assert vote1.accepted is True

        vote2 = proposal.votes.get(member=member2)
        assert vote2.included is True
        assert vote2.accepted is None

        vote3 = proposal.votes.get(member=member3)
        assert vote3.included is False
        assert vote3.accepted is None

    def test_active_queryset_excludes_cancelled(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        active_proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        cancelled_proposal = draw_proposal_factory(
            game=game,
            created_by=member2,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
            cancelled=True,
        )

        active_proposals = DrawProposal.objects.active()
        assert active_proposal in active_proposals
        assert cancelled_proposal not in active_proposals


class TestDrawProposalProcessAcceptance:
    def test_creates_victory_when_accepted(
        self, game_factory, phase_factory, member_factory, supply_center_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member1.nation)
        for _ in range(8):
            supply_center_factory(phase=phase, nation=member2.nation)
        for _ in range(5):
            supply_center_factory(phase=phase, nation=member3.nation)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        for vote in proposal.votes.all():
            vote.accepted = True
            vote.save()

        victory = proposal.process_acceptance()

        assert victory is not None
        assert victory.game == game
        assert victory.winning_phase == phase
        assert victory.members.count() == 2
        assert member1 in victory.members.all()
        assert member2 in victory.members.all()
        assert member3 not in victory.members.all()

        member1.refresh_from_db()
        member2.refresh_from_db()
        member3.refresh_from_db()
        assert member1.drew is True
        assert member2.drew is True
        assert member3.drew is False

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED

    def test_returns_none_when_not_accepted(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        victory = proposal.process_acceptance()
        assert victory is None


class TestDrawProposalCreateView:
    def test_create_proposal_success(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member1.nation)
        for _ in range(9):
            supply_center_factory(phase=phase, nation=member2.nation)

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {"includedMemberIds": [member1.id, member2.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert DrawProposal.objects.count() == 1
        proposal = DrawProposal.objects.first()
        assert proposal.created_by == member1
        assert proposal.votes.count() == 3

    def test_create_proposal_fails_if_not_including_self(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member2.nation)
        for _ in range(9):
            supply_center_factory(phase=phase, nation=member3.nation)

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {"includedMemberIds": [member2.id, member3.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_proposal_fails_if_below_threshold(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)

        for _ in range(8):
            supply_center_factory(phase=phase, nation=member1.nation)
        for _ in range(8):
            supply_center_factory(phase=phase, nation=member2.nation)

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {"includedMemberIds": [member1.id, member2.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_proposal_fails_if_sandbox_game(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18, sandbox=True)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member1.nation)
        for _ in range(9):
            supply_center_factory(phase=phase, nation=member2.nation)

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {"includedMemberIds": [member1.id, member2.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_proposal_fails_if_already_has_active_proposal(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member1.nation)
        for _ in range(9):
            supply_center_factory(phase=phase, nation=member2.nation)

        draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.post(
            f"/games/{game.id}/draw-proposals/create/",
            {"includedMemberIds": [member1.id, member2.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDrawProposalVoteView:
    def test_vote_accept_success(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=proposer.nation)
        for _ in range(9):
            supply_center_factory(phase=phase, nation=voter.nation)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

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
        supply_center_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

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

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is False

    def test_vote_creates_victory_when_all_accept(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=proposer.nation)
        for _ in range(9):
            supply_center_factory(phase=phase, nation=voter.nation)

        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert Victory.objects.count() == 1

        victory = Victory.objects.first()
        assert victory.game == game
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
        from rest_framework_simplejwt.tokens import RefreshToken

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

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": False},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDrawProposalCancelView:
    def test_cancel_own_proposal_success(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.delete(
            f"/games/{game.id}/draw-proposals/{proposal.id}/cancel/",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        proposal.refresh_from_db()
        assert proposal.cancelled is True
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
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=secondary_user)
        member2 = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.delete(
            f"/games/{game.id}/draw-proposals/{proposal.id}/cancel/",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDrawProposalListView:
    def test_list_proposals_for_current_phase(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase1 = phase_factory(game=game, ordinal=1)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)

        old_proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase1,
            included_member_ids=[member1.id, member2.id],
        )

        phase2 = phase_factory(game=game, ordinal=2)

        new_proposal = draw_proposal_factory(
            game=game,
            created_by=member2,
            phase=phase2,
            included_member_ids=[member1.id, member2.id],
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == new_proposal.id

    def test_list_excludes_cancelled_proposals(
        self,
        api_client,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        primary_user,
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member1 = member_factory(game=game, user=primary_user)
        member2 = member_factory(game=game)

        active_proposal = draw_proposal_factory(
            game=game,
            created_by=member1,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
        )

        cancelled_proposal = draw_proposal_factory(
            game=game,
            created_by=member2,
            phase=phase,
            included_member_ids=[member1.id, member2.id],
            cancelled=True,
        )

        refresh = RefreshToken.for_user(primary_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = api_client.get(f"/games/{game.id}/draw-proposals/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == active_proposal.id
