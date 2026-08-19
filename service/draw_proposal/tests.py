import pytest
from django.urls import reverse
from rest_framework import status
from common.constants import GameStatus, PhaseStatus
from draw_proposal.models import DrawProposal, DrawVote
from draw_proposal.constants import DrawProposalStatus
from victory.models import Victory


class TestDrawProposalCreateView:

    def test_create_proposal_success_with_empty_body(
        self, authenticated_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        other = member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
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
        authenticated_client, game_factory, phase_factory, member_factory,
        supply_center_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        for _ in range(2):
            supply_center_factory(phase=phase)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_proposal_fails_in_sandbox_game(
        self, authenticated_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18, sandbox=True)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_proposal_fails_if_member_already_has_active_proposal(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_proposal_cd_members_get_excluded_and_auto_accepted(
        self, authenticated_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        member_factory(game=game, user=primary_user)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder = True
        cd_member.save()
        member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        proposal = DrawProposal.objects.first()
        cd_vote = proposal.votes.get(member=cd_member)
        assert cd_vote.included is False
        assert cd_vote.accepted is True

    def test_create_proposal_excludes_eliminated_and_kicked_members(
        self, authenticated_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)
        eliminated = member_factory(game=game, eliminated=True)
        kicked = member_factory(game=game, kicked=True)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        proposal = DrawProposal.objects.get(created_by=proposer)
        assert proposal.votes.count() == 2
        assert not proposal.votes.filter(member=eliminated).exists()
        assert not proposal.votes.filter(member=kicked).exists()

    def test_create_proposal_completes_game_when_proposer_is_only_active_voter(
        self, authenticated_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        cd_member = member_factory(game=game)
        cd_member.civil_disorder = True
        cd_member.save()

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Victory.objects.count() == 1
        victory = Victory.objects.first()
        assert list(victory.members.all()) == [proposer]

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED

    def test_create_proposal_fails_while_phase_is_being_resolved(
        self, authenticated_client, game_factory, phase_factory, member_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game, status=PhaseStatus.PROCESSING)
        member_factory(game=game, user=primary_user)
        member_factory(game=game)

        response = authenticated_client.post(
            reverse("draw-proposal-create", args=[game.id]), {}, format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert DrawProposal.objects.count() == 0


class TestDrawProposalVoteUpdateView:

    def test_vote_accept_success(
        self, authenticated_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is True

    def test_vote_reject_success(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": False}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == DrawProposalStatus.REJECTED
        vote = DrawVote.objects.get(proposal=proposal, member=voter)
        assert vote.accepted is False

    def test_vote_creates_victory_when_all_accept(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert Victory.objects.count() == 1
        victory = Victory.objects.first()
        assert victory.members.count() == 2

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED

    def test_vote_fails_if_already_voted(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": False}, format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_vote_fails_while_phase_is_being_resolved(
        self, authenticated_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, status=PhaseStatus.PROCESSING)
        proposer = member_factory(game=game)
        voter = member_factory(game=game, user=primary_user)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id, voter.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": True}, format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Victory.objects.count() == 0

    def test_vote_on_proposal_from_other_game_not_found(
        self, authenticated_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user, secondary_user,
    ):
        game_a = game_factory(variant__solo_victory_sc_count=18)
        phase_factory(game=game_a)
        member_factory(game=game_a, user=primary_user)
        member_factory(game=game_a)

        game_b = game_factory(variant__solo_victory_sc_count=18)
        phase_b = phase_factory(game=game_b)
        proposer_b = member_factory(game=game_b, user=secondary_user)
        proposal_b = draw_proposal_factory(
            game=game_b, created_by=proposer_b, phase=phase_b,
            included_member_ids=[proposer_b.id],
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game_a.id, proposal_b.id]),
            {"accepted": True}, format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_vote_response_does_not_expose_per_member_votes(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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
        response = authenticated_client.patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]),
            {"accepted": False}, format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "votes" not in response.data
        assert response.data["my_vote"] == {"included": True, "accepted": False}


class TestDrawProposalCancelView:

    def test_cancel_own_proposal_success(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.patch(
            reverse("draw-proposal-cancel", args=[game.id, proposal.id]),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == proposal.id
        assert response.data["status"] == DrawProposalStatus.REJECTED

        proposal.refresh_from_db()
        assert proposal.cancelled is True

    def test_cancel_already_cancelled_proposal_not_found(
        self, authenticated_client, game_factory, phase_factory, member_factory,
        draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        proposer = member_factory(game=game, user=primary_user)
        member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=proposer, phase=phase,
            included_member_ids=[proposer.id], cancelled=True,
        )

        response = authenticated_client.patch(
            reverse("draw-proposal-cancel", args=[game.id, proposal.id]),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_cancel_others_proposal(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.patch(
            reverse("draw-proposal-cancel", args=[game.id, proposal.id]),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDrawProposalListView:

    def test_list_proposals_for_current_phase(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.get(reverse("draw-proposal-list", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == new_proposal.id

    def test_list_excludes_cancelled_proposals(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.get(reverse("draw-proposal-list", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == active.id

    def test_list_proposals_as_non_member(
        self, authenticated_client_for_secondary_user, game_factory, phase_factory,
        member_factory, draw_proposal_factory, primary_user,
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game)
        m1 = member_factory(game=game, user=primary_user)
        m2 = member_factory(game=game)

        proposal = draw_proposal_factory(
            game=game, created_by=m1, phase=phase,
            included_member_ids=[m1.id, m2.id],
        )

        response = authenticated_client_for_secondary_user.get(
            reverse("draw-proposal-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == proposal.id
        assert response.data[0]["my_vote"] is None

    def test_list_response_no_longer_includes_combined_sc_count_or_threshold(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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
        response = authenticated_client.get(reverse("draw-proposal-list", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        item = response.data[0]
        assert "combined_sc_count" not in item
        assert "victory_threshold" not in item

    def test_list_response_does_not_expose_per_member_votes(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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
        vote = proposal.votes.get(member=m2)
        vote.accepted = True
        vote.save()

        response = authenticated_client.get(reverse("draw-proposal-list", args=[game.id]))

        item = response.data[0]
        assert "votes" not in item
        assert item["accepted_count"] == 2
        assert item["rejected_count"] == 0
        assert item["pending_count"] == 1
        assert item["total_votes"] == 3

    def test_list_response_includes_included_member_ids(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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

        response = authenticated_client.get(reverse("draw-proposal-list", args=[game.id]))

        item = response.data[0]
        assert set(item["included_member_ids"]) == {m1.id, m2.id}
        assert m3.id not in item["included_member_ids"]

    def test_list_response_my_vote_reflects_current_user(
        self, authenticated_client, game_factory, phase_factory, member_factory,
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
        vote = proposal.votes.get(member=voter)
        vote.accepted = False
        vote.save()

        response = authenticated_client.get(reverse("draw-proposal-list", args=[game.id]))

        item = response.data[0]
        assert item["my_vote"] == {"included": True, "accepted": False}
