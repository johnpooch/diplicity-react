from datetime import timedelta

import pytest

from game_spike.factories import GameFactory, UserFactory
from game_spike.tasks import send_muster_reminder

pytestmark = pytest.mark.django_db

PASSED = timedelta(minutes=-1)
SOON = timedelta(minutes=10)


class TestSendMusterReminder:
    def test_reminds_unmustered_players_when_deadline_is_near(self, assert_notification):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player], muster_ends_in=SOON)
        send_muster_reminder(game_id=game.id)
        assert_notification(player, "muster_reminder")

    def test_does_not_remind_mustered_players(self, assert_notification):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player], mustered=[player], muster_ends_in=SOON)
        send_muster_reminder(game_id=game.id)
        assert_notification(player, "muster_reminder", sent=False)

    def test_does_not_remind_before_the_reminder_window(self, assert_notification):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player])
        send_muster_reminder(game_id=game.id)
        assert_notification(player, "muster_reminder", sent=False)

    def test_does_not_remind_after_the_deadline(self, assert_notification):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player], muster_ends_in=PASSED)
        send_muster_reminder(game_id=game.id)
        assert_notification(player, "muster_reminder", sent=False)
