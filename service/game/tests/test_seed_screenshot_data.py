import json

import pytest
from django.core.management import call_command

from channel.models import Channel, ChannelMessage
from game.models import Game
from login.models import AuthUser
from member.models import Member
from order.models import OrderResolution
from phase.models import Phase, PhaseState
from unit.models import Unit


@pytest.fixture
def seed_output(db):
    from io import StringIO

    out = StringIO()
    call_command("seed_screenshot_data", stdout=out)
    return out.getvalue()


@pytest.fixture
def seed_data(seed_output):
    return json.loads(seed_output)


class TestSeedScreenshotData:
    def test_seed_creates_expected_users(self, seed_data):
        users = AuthUser.objects.filter(
            email__startswith="screenshot-", email__endswith="@test.com"
        )
        assert users.count() == 7

    def test_seed_creates_three_games(self, seed_data):
        games = Game.objects.filter(name__startswith="screenshot:")
        assert games.count() == 3
        statuses = set(games.values_list("status", flat=True))
        assert "active" in statuses
        assert "pending" in statuses

    def test_seed_creates_correct_phases(self, seed_data):
        game1 = Game.objects.get(name="screenshot: The Great War")
        game2 = Game.objects.get(name="screenshot: Mediterranean Alliance")
        game3 = Game.objects.get(name="screenshot: North Sea Gambit")

        assert game1.phases.count() == 3
        assert game1.phases.filter(status="completed").count() == 2
        assert game1.phases.filter(status="active").count() == 1

        assert game2.phases.count() == 1
        assert game2.phases.filter(status="active").count() == 1

        assert game3.phases.count() == 0

    def test_seed_creates_members(self, seed_data):
        game1 = Game.objects.get(name="screenshot: The Great War")
        game2 = Game.objects.get(name="screenshot: Mediterranean Alliance")
        game3 = Game.objects.get(name="screenshot: North Sea Gambit")

        assert game1.members.count() == 7
        assert game2.members.count() == 7
        assert game3.members.count() == 3
        assert game3.members.filter(nation__isnull=True).count() == 3

    def test_seed_creates_phase_states(self, seed_data):
        game1 = Game.objects.get(name="screenshot: The Great War")
        total_states = PhaseState.objects.filter(member__game=game1).count()
        assert total_states == 21  # 7 members × 3 phases

    def test_seed_creates_chat(self, seed_data):
        game1 = Game.objects.get(name="screenshot: The Great War")
        channels = Channel.objects.filter(game=game1, private=True)
        assert channels.count() == 1

        channel = channels.first()
        assert channel.name == "England, France"
        assert ChannelMessage.objects.filter(channel=channel).count() == 6

    def test_seed_is_idempotent(self, seed_data):
        from io import StringIO

        call_command("seed_screenshot_data", stdout=StringIO())

        assert AuthUser.objects.filter(
            email__startswith="screenshot-", email__endswith="@test.com"
        ).count() == 7
        assert Game.objects.filter(name__startswith="screenshot:").count() == 3

    def test_seed_outputs_valid_json(self, seed_data):
        assert "accessToken" in seed_data
        assert "refreshToken" in seed_data
        assert "email" in seed_data
        assert "name" in seed_data
        assert "game1Id" in seed_data
        assert "phase2Id" in seed_data
        assert "phase3Id" in seed_data
        assert "channelId" in seed_data

    def test_game1_phase2_has_order_resolutions(self, seed_data):
        game1 = Game.objects.get(name="screenshot: The Great War")
        phase2 = game1.phases.get(ordinal=2)
        resolutions = OrderResolution.objects.filter(
            order__phase_state__phase=phase2
        )
        assert resolutions.count() > 0
        assert resolutions.filter(status="ErrBounce").exists()
        assert resolutions.filter(status="OK").exists()

    def test_game1_phase3_units(self, seed_data):
        game1 = Game.objects.get(name="screenshot: The Great War")
        phase3 = game1.phases.get(ordinal=3)
        assert phase3.units.count() == 22
