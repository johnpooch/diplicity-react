import pytest

import emit
from channel.models import Channel, ChannelEvent
from common.constants import PhaseStatus
from phase.models import Phase


class TestChannelEventManager:
    @pytest.mark.django_db
    def test_create_for_channels_creates_row_per_channel(self, game_factory, classical_variant):
        game = game_factory(variant=classical_variant)
        public = Channel.objects.create(game=game, name="Public Press", private=False)
        private = Channel.objects.create(game=game, name="Secret", private=True)

        events = ChannelEvent.objects.create_for_channels("phase_resolved", [public, private])

        assert len(events) == 2
        assert {e.channel_id for e in events} == {public.id, private.id}
        assert all(e.type == "phase_resolved" for e in events)
        assert all(e.phase_id is None for e in events)

    @pytest.mark.django_db
    def test_create_for_channels_attaches_phase(self, game_factory, classical_variant):
        game = game_factory(variant=classical_variant)
        public = Channel.objects.create(game=game, name="Public Press", private=False)
        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
        )

        events = ChannelEvent.objects.create_for_channels("phase_resolved", [public], phase=phase)

        assert len(events) == 1
        assert events[0].phase_id == phase.id

    @pytest.mark.django_db
    def test_create_for_channels_empty_is_noop(self, game_factory, classical_variant):
        events = ChannelEvent.objects.create_for_channels("phase_resolved", [])

        assert events == []
        assert ChannelEvent.objects.count() == 0


class TestChannelEventDispatch:
    @pytest.mark.django_db
    def test_emit_creates_channel_event_on_public_press_channel(
        self, game_factory, classical_variant, in_memory_procrastinate
    ):
        game = game_factory(variant=classical_variant)
        public = Channel.objects.create(game=game, name="Public Press", private=False)
        private = Channel.objects.create(game=game, name="Secret", private=True)
        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
        )

        emit.emit("phase_resolved", phase=phase)

        events = ChannelEvent.objects.filter(type="phase_resolved")
        assert events.count() == 1
        event = events.first()
        assert event.channel_id == public.id
        assert event.phase_id == phase.id
        assert not ChannelEvent.objects.filter(channel=private).exists()
