import pytest
from django.urls import reverse
from rest_framework import status
from common.constants import GameStatus, PhaseStatus

from game.models import Game
from channel.models import Channel, ChannelMessage
from draw_proposal.models import DrawProposal, DrawVote
from victory.models import Victory


retrieve_viewname = "game-retrieve"
channel_list_viewname = "channel-list"
draw_proposal_list_viewname = "draw-proposal-list"
game_list_viewname = "game-list"
phase_state_list_viewname = "phase-state-list"


def create_anonymous_game(classical_variant, classical_england_nation, classical_france_nation,
                          classical_edinburgh_province, primary_user, secondary_user,
                          game_status=GameStatus.ACTIVE, anonymous=True):
    phase_status = PhaseStatus.PENDING if game_status == GameStatus.PENDING else PhaseStatus.ACTIVE
    game = Game.objects.create(
        name=f"Anon {game_status} Game",
        variant=classical_variant,
        status=game_status,
        anonymous=anonymous,
    )
    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=phase_status,
        ordinal=1,
    )
    phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)

    game.members.create(
        user=primary_user, nation=classical_england_nation, is_game_master=True
    )
    game.members.create(user=secondary_user, nation=classical_france_nation)
    return game


class TestAnonymousGames:

    @pytest.mark.django_db
    def test_non_anonymous_game_shows_real_member_data(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
            anonymous=False,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        england = members_by_nation["England"]
        assert england["name"] == "Primary User"
        assert england["is_game_master"] is True

    @pytest.mark.django_db
    def test_anonymous_active_game_masks_other_players(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        england = members_by_nation["England"]
        assert england["name"] == "Anonymous"
        assert england["picture"] is None
        assert england["is_game_master"] is False

    @pytest.mark.django_db
    def test_anonymous_active_game_shows_self_real_identity(
        self,
        authenticated_client,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_nation = {m["nation"]: m for m in response.data["members"]}

        # Self: real identity visible
        england = members_by_nation["England"]
        assert england["name"] == "Primary User"
        assert england["is_current_user"] is True
        assert england["is_game_master"] is True

        # Other player: masked
        france = members_by_nation["France"]
        assert france["name"] == "Anonymous"
        assert france["picture"] is None
        assert france["is_current_user"] is False

    @pytest.mark.django_db
    def test_anonymous_completed_game_reveals_all_identities(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
            game_status=GameStatus.COMPLETED,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        england = members_by_nation["England"]
        assert england["name"] == "Primary User"
        assert england["is_game_master"] is True

    @pytest.mark.django_db
    def test_anonymous_abandoned_game_stays_masked(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
            game_status=GameStatus.ABANDONED,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        england = members_by_nation["England"]
        assert england["name"] == "Anonymous"
        assert england["picture"] is None
        assert england["is_game_master"] is False

    @pytest.mark.django_db
    def test_anonymous_pending_game_is_masked(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
            game_status=GameStatus.PENDING,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        england = members_by_nation["England"]
        assert england["name"] == "Anonymous"
        assert england["picture"] is None
        assert england["is_game_master"] is False

    @pytest.mark.django_db
    def test_anonymous_game_masks_channel_message_senders(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        primary_member = game.members.get(user=primary_user)
        secondary_member = game.members.get(user=secondary_user)

        channel = Channel.objects.create(name="Public Press", game=game, private=False)
        channel.members.add(primary_member, secondary_member)
        ChannelMessage.objects.create(
            channel=channel, sender=primary_member, body="Hello from England"
        )

        url = reverse(channel_list_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

        public_channel = next(c for c in response.data if c["name"] == "Public Press")
        assert len(public_channel["messages"]) == 1

        sender = public_channel["messages"][0]["sender"]
        assert sender["name"] == "Anonymous"
        assert sender["picture"] is None

    @pytest.mark.django_db
    def test_anonymous_game_masks_draw_proposal_members(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        primary_member = game.members.get(user=primary_user)
        secondary_member = game.members.get(user=secondary_user)

        phase = game.current_phase
        proposal = DrawProposal.objects.create(
            game=game, created_by=primary_member, phase=phase,
        )
        DrawVote.objects.create(
            proposal=proposal, member=primary_member, included=True, accepted=True,
        )
        DrawVote.objects.create(
            proposal=proposal, member=secondary_member, included=True, accepted=None,
        )

        url = reverse(draw_proposal_list_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        proposal_data = response.data[0]
        assert proposal_data["created_by"]["name"] == "Anonymous"
        assert proposal_data["created_by"]["picture"] is None

        for vote in proposal_data["votes"]:
            member = vote["member"]
            if member["is_current_user"]:
                assert member["name"] == "Secondary User"
            else:
                assert member["name"] == "Anonymous"
                assert member["picture"] is None

    @pytest.mark.django_db
    def test_anonymous_game_masks_members_in_game_list(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        url = reverse(game_list_viewname)
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK

        results = response.data["results"] if isinstance(response.data, dict) else response.data
        game_data = next(g for g in results if g["id"] == str(game.id))
        members_by_nation = {m["nation"]: m for m in game_data["members"]}
        england = members_by_nation["England"]
        assert england["name"] == "Anonymous"
        assert england["picture"] is None
        assert england["is_game_master"] is False

    @pytest.mark.django_db
    def test_anonymous_game_phase_state_shows_own_identity(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        phase = game.current_phase
        secondary_member = game.members.get(user=secondary_user)
        phase.phase_states.create(member=secondary_member, has_possible_orders=True)

        url = reverse(phase_state_list_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        member = response.data[0]["member"]
        assert member["is_current_user"] is True
        assert member["name"] == "Secondary User"

    @pytest.mark.django_db
    def test_anonymous_completed_game_reveals_victory_members(
        self,
        authenticated_client_for_secondary_user,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
            game_status=GameStatus.COMPLETED,
        )

        phase = game.current_phase
        primary_member = game.members.get(user=primary_user)
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(primary_member)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["victory"] is not None

        victory_members = response.data["victory"]["members"]
        assert len(victory_members) == 1
        assert victory_members[0]["name"] == "Primary User"

    @pytest.mark.django_db
    def test_anonymous_game_masks_all_members_for_unauthenticated_user(
        self,
        unauthenticated_client,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
    ):
        game = create_anonymous_game(
            classical_variant, classical_england_nation, classical_france_nation,
            classical_edinburgh_province, primary_user, secondary_user,
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = unauthenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        for member in response.data["members"]:
            assert member["name"] == "Anonymous"
            assert member["picture"] is None
            assert member["is_current_user"] is False
