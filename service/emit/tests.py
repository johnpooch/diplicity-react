import pytest

import emit
from channel.models import Channel
from emit.dispatch import recipients
from emit.transport import Push, Timeline


def _notification_jobs(connector, notification_type=None):
    jobs = [j for j in connector.jobs.values() if j["task_name"] == "notification.send_notification"]
    if notification_type is not None:
        jobs = [j for j in jobs if j["args"]["notification_type"] == notification_type]
    return jobs


@pytest.fixture
def emit_game(db, game_factory, member_factory, user_factory, classical_variant):
    def _create(with_game_master=False):
        game_master = user_factory() if with_game_master else None
        game = game_factory(variant=classical_variant, game_master=game_master)
        active_one = member_factory(game=game, user=user_factory())
        active_two = member_factory(game=game, user=user_factory())
        eliminated = member_factory(game=game, user=user_factory(), eliminated=True)
        kicked = member_factory(game=game, user=user_factory(), kicked=True)
        civil = member_factory(game=game, user=user_factory(), civil_disorder=True)
        return {
            "game": game,
            "game_master": game_master,
            "active_one": active_one,
            "active_two": active_two,
            "eliminated": eliminated,
            "kicked": kicked,
            "civil": civil,
        }

    return _create


class TestRegistry:
    def test_all_live_notification_types_are_registered(self):
        expected = {
            "channel_message",
            "draw_proposal",
            "game_start",
            "game_draw",
            "game_solo_win",
            "game_solo_loss",
            "phase_resolved",
            "phase_resolved_early",
            "game_deleted",
            "game_admin_reassigned",
            "game_paused",
            "game_resumed",
            "game_deadline_extended",
            "kicked_from_staging",
            "removed_from_staging",
            "civil_disorder",
            "civil_disorder_recovery",
            "elimination",
            "nmr_extension_used",
            "nmr_extension_applied",
            "deadline_warning",
        }
        assert set(emit.REGISTRY) == expected

    def test_every_type_declares_known_transports(self):
        for spec_class in emit.REGISTRY.values():
            assert spec_class.transports
            assert all(transport in {Push, Timeline} for transport in spec_class.transports)

    def test_every_type_currently_pushes(self):
        for spec_class in emit.REGISTRY.values():
            assert Push in spec_class.transports


class TestActiveResolver:
    def test_civil_disorder_excludes_eliminated_kicked_civil_and_includes_game_master(self, emit_game):
        state = emit_game(with_game_master=True)
        result = recipients("civil_disorder", game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["game_master"].id,
        }

    def test_civil_disorder_without_game_master(self, emit_game):
        state = emit_game(with_game_master=False)
        result = recipients("civil_disorder", game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
        }


class TestAllRecipientsResolver:
    @pytest.mark.parametrize(
        "event_type",
        ["game_start", "game_draw", "phase_resolved", "phase_resolved_early"],
    )
    def test_includes_eliminated_and_kicked_and_game_master(self, emit_game, event_type):
        state = emit_game(with_game_master=True)
        result = recipients(event_type, game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestAllPlayersExceptActorResolver:
    @pytest.mark.parametrize(
        "event_type",
        ["game_paused", "game_resumed", "game_deadline_extended"],
    )
    def test_excludes_the_actor(self, emit_game, event_type):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = recipients(event_type, game=state["game"], actor=actor)
        assert actor.id not in result
        assert result == {
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }

    def test_game_deleted_uses_explicit_recipients(self, emit_game):
        state = emit_game()
        result = recipients(
            "game_deleted",
            game=state["game"],
            context={"recipients": [state["active_two"].user_id]},
        )
        assert result == {state["active_two"].user_id}


class TestActiveExceptActorResolver:
    @pytest.mark.parametrize(
        "event_type",
        ["draw_proposal", "civil_disorder_recovery"],
    )
    def test_excludes_eliminated_kicked_civil_disorder_and_actor(self, emit_game, event_type):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = recipients(event_type, game=state["game"], actor=actor)
        assert result == {
            state["active_two"].user_id,
            state["game_master"].id,
        }


class TestSoloLossResolver:
    def test_excludes_the_winner(self, emit_game):
        state = emit_game(with_game_master=True)
        winner_id = state["active_one"].user_id
        result = recipients(
            "game_solo_loss",
            game=state["game"],
            context={"winner_user_id": winner_id},
        )
        assert winner_id not in result
        assert result == {
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestNmrExtensionAppliedResolver:
    def test_excludes_members_that_used_an_extension(self, emit_game):
        state = emit_game(with_game_master=True)
        used = state["active_one"].user_id
        result = recipients(
            "nmr_extension_applied",
            game=state["game"],
            context={"extension_user_ids": [used]},
        )
        assert used not in result
        assert result == {
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestExplicitResolvers:
    @pytest.mark.parametrize(
        "event_type",
        [
            "game_solo_win",
            "game_admin_reassigned",
            "kicked_from_staging",
            "removed_from_staging",
            "elimination",
            "nmr_extension_used",
            "deadline_warning",
        ],
    )
    def test_returns_recipients_from_context(self, emit_game, event_type):
        state = emit_game()
        target = state["active_one"].user_id
        result = recipients(event_type, game=state["game"], context={"recipients": [target]})
        assert result == {target}

    def test_empty_when_no_recipients_provided(self, emit_game):
        state = emit_game()
        result = recipients("elimination", game=state["game"])
        assert result == set()


class TestChannelMessageResolver:
    def test_public_channel_notifies_all_game_members_except_sender(self, emit_game):
        state = emit_game()
        channel = Channel.objects.create(game=state["game"], name="Global", private=False)
        sender = state["active_one"]
        result = recipients(
            "channel_message",
            game=state["game"],
            actor=sender.user,
            channel=channel,
        )
        assert sender.user_id not in result
        assert state["active_two"].user_id in result
        assert state["eliminated"].user_id in result

    def test_private_channel_notifies_only_channel_members_except_sender(self, emit_game):
        state = emit_game()
        channel = Channel.objects.create(game=state["game"], name="Private", private=True)
        sender = state["active_one"]
        channel.members.set([sender, state["active_two"]])
        result = recipients(
            "channel_message",
            game=state["game"],
            actor=sender.user,
            channel=channel,
        )
        assert result == {state["active_two"].user_id}


class TestEmitDispatch:
    @pytest.mark.django_db
    def test_push_type_defers_send_notification_with_resolved_recipients(
        self, emit_game, in_memory_procrastinate
    ):
        state = emit_game(with_game_master=True)
        emit.emit("game_start", game=state["game"])

        jobs = _notification_jobs(in_memory_procrastinate, "game_start")
        assert len(jobs) == 1
        args = jobs[0]["args"]
        assert set(args["user_ids"]) == recipients("game_start", game=state["game"])
        assert args["title"] == state["game"].name
        assert "The game has started" in args["body"]
        assert args["data"]["game_id"] == str(state["game"].id)

    @pytest.mark.django_db
    def test_push_only_type_defers_send_notification(self, emit_game, in_memory_procrastinate):
        state = emit_game()
        emit.emit(
            "elimination",
            game=state["game"],
            context={"recipients": [state["active_one"].user_id]},
        )

        jobs = _notification_jobs(in_memory_procrastinate, "elimination")
        assert len(jobs) == 1
        assert jobs[0]["args"]["user_ids"] == [state["active_one"].user_id]

    @pytest.mark.django_db
    def test_no_job_deferred_when_there_are_no_recipients(
        self, emit_game, in_memory_procrastinate
    ):
        state = emit_game()
        emit.emit("elimination", game=state["game"], context={"recipients": []})

        assert _notification_jobs(in_memory_procrastinate, "elimination") == []

    @pytest.mark.django_db
    def test_context_values_are_interpolated_into_copy(self, emit_game, in_memory_procrastinate):
        state = emit_game(with_game_master=True)
        emit.emit(
            "game_resumed",
            game=state["game"],
            actor=state["active_one"].user,
            context={"manager_label": "the game creator", "deadline": "1 Jan 2026"},
        )

        jobs = _notification_jobs(in_memory_procrastinate, "game_resumed")
        assert len(jobs) == 1
        assert jobs[0]["args"]["body"] == "Game resumed by the game creator. New deadline: 1 Jan 2026"
