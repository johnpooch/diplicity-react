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
    def test_emit_creates_channel_event_on_every_channel(
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
        assert events.count() == 2
        assert {e.channel_id for e in events} == {public.id, private.id}
        assert all(e.phase_id == phase.id for e in events)


class TestPhaseResolvedEventDisplay:
    @pytest.mark.django_db
    def test_phase_resolved_event_is_displayed_with_phase_name(self, game_factory, classical_variant):
        game = game_factory(variant=classical_variant)
        channel = Channel.objects.create(game=game, name="Public Press", private=False)
        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
        )

        event = ChannelEvent.objects.create_for_channels("phase_resolved", [channel], phase=phase)[0]

        assert ChannelEvent.objects.for_display().filter(id=event.id).exists()
        assert event.text == "Spring 1901, Movement has been resolved"

    @pytest.mark.django_db
    def test_phase_resolved_early_event_is_displayed_with_phase_name(self, game_factory, classical_variant):
        game = game_factory(variant=classical_variant)
        channel = Channel.objects.create(game=game, name="Public Press", private=False)
        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
        )

        event = ChannelEvent.objects.create_for_channels("phase_resolved_early", [channel], phase=phase)[0]

        assert ChannelEvent.objects.for_display().filter(id=event.id).exists()
        assert event.text == "Spring 1901, Movement resolved early — all players confirmed their orders"
