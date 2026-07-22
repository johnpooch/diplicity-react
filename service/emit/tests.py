import pytest

import emit
from channel.models import Channel, ChannelMessage
from draw_proposal.models import DrawProposal
from emit.dispatch import recipients
from emit.specs import ChannelMessageSpec
from emit.transport import Email, Push, Timeline
from phase.models import Phase
from victory.models import Victory

_truncate = ChannelMessageSpec._truncate


def _create_victory(state, winners):
    game = state["game"]
    phase = Phase.objects.create(
        game=game,
        variant=game.variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status="Completed",
    )
    victory = Victory.objects.create(game=game, winning_phase=phase)
    victory.members.set(winners)
    return victory


class TestTruncateBody:
    def test_short_single_line_unchanged(self):
        assert _truncate("Hello world") == "Hello world"

    def test_exactly_three_lines_unchanged(self):
        text = "line1\nline2\nline3"
        assert _truncate(text) == "line1\nline2\nline3"

    def test_four_lines_truncated_to_three_with_ellipsis(self):
        text = "line1\nline2\nline3\nline4"
        assert _truncate(text) == "line1\nline2\nline3…"

    def test_many_lines_truncated_to_three_with_ellipsis(self):
        text = "\n".join(f"line{i}" for i in range(10))
        assert _truncate(text) == "line0\nline1\nline2…"

    def test_exceeds_max_chars_truncated_with_ellipsis(self):
        long_line = "x" * 250
        result = _truncate(long_line)
        assert result == "x" * 200 + "…"
        assert len(result) == 201

    def test_exceeds_max_chars_after_joining_lines(self):
        line = "x" * 70
        text = f"{line}\n{line}\n{line}"
        result = _truncate(text)
        assert result.endswith("…")
        assert len(result) <= 202

    def test_trailing_whitespace_stripped_before_ellipsis_on_char_limit(self):
        long_line = "x" * 199 + " " + "y" * 50
        result = _truncate(long_line)
        assert not result[:-1].endswith(" ")
        assert result.endswith("…")

    def test_empty_string_unchanged(self):
        assert _truncate("") == ""

    def test_custom_max_lines(self):
        text = "a\nb\nc\nd"
        assert _truncate(text, max_lines=2) == "a\nb…"

    def test_custom_max_chars(self):
        text = "x" * 50
        result = _truncate(text, max_chars=10)
        assert result == "x" * 10 + "…"

    def test_exactly_max_chars_no_ellipsis(self):
        text = "x" * 200
        assert _truncate(text) == "x" * 200


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
            assert all(transport in {Push, Timeline, Email} for transport in spec_class.transports)

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
            recipients=[state["active_two"].user_id],
        )
        assert result == {state["active_two"].user_id}


class TestActiveExceptActorResolver:
    def test_civil_disorder_recovery_excludes_eliminated_kicked_civil_disorder_and_actor(self, emit_game):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = recipients("civil_disorder_recovery", game=state["game"], actor=actor)
        assert result == {
            state["active_two"].user_id,
            state["game_master"].id,
        }

    @pytest.mark.django_db
    def test_draw_proposal_excludes_eliminated_kicked_civil_disorder_and_actor(self, emit_game):
        state = emit_game(with_game_master=True)
        phase = Phase.objects.create(
            game=state["game"],
            variant=state["game"].variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status="Active",
        )
        proposal = DrawProposal.objects.create(
            game=state["game"], created_by=state["active_one"], phase=phase
        )
        result = recipients("draw_proposal", draw_proposal=proposal)
        assert result == {
            state["active_two"].user_id,
            state["game_master"].id,
        }


class TestWinnersResolver:
    @pytest.mark.django_db
    def test_solo_win_targets_only_the_winner(self, emit_game):
        state = emit_game(with_game_master=True)
        winner = state["active_one"]
        _create_victory(state, [winner])
        result = recipients("game_solo_win", game=state["game"])
        assert result == {winner.user_id}

    @pytest.mark.django_db
    def test_solo_loss_excludes_the_winner(self, emit_game):
        state = emit_game(with_game_master=True)
        winner = state["active_one"]
        _create_victory(state, [winner])
        result = recipients("game_solo_loss", game=state["game"])
        assert winner.user_id not in result
        assert result == {
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestNmrExtensionAppliedResolver:
    def test_includes_all_players_and_game_master(self, emit_game):
        state = emit_game(with_game_master=True)
        result = recipients("nmr_extension_applied", game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestActorResolver:
    def test_nmr_extension_used_targets_only_the_actor(self, emit_game):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = recipients("nmr_extension_used", game=state["game"], actor=actor)
        assert result == {actor.id}


class TestAdminResolver:
    def test_game_admin_reassigned_targets_only_the_admin(self, emit_game):
        state = emit_game()
        game = state["game"]
        game.admin = state["active_one"].user
        game.save(update_fields=["admin"])
        result = recipients("game_admin_reassigned", game=game)
        assert result == {state["active_one"].user_id}


class TestExplicitResolvers:
    @pytest.mark.parametrize(
        "event_type",
        [
            "kicked_from_staging",
            "removed_from_staging",
            "elimination",
            "deadline_warning",
        ],
    )
    def test_returns_recipients_from_context(self, emit_game, event_type):
        state = emit_game()
        target = state["active_one"].user_id
        result = recipients(event_type, game=state["game"], recipients=[target])
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
        message = ChannelMessage.objects.create(channel=channel, sender=sender, body="hi")
        result = recipients("channel_message", message=message)
        assert sender.user_id not in result
        assert state["active_two"].user_id in result
        assert state["eliminated"].user_id in result

    def test_private_channel_notifies_only_channel_members_except_sender(self, emit_game):
        state = emit_game()
        channel = Channel.objects.create(game=state["game"], name="Private", private=True)
        sender = state["active_one"]
        channel.members.set([sender, state["active_two"]])
        message = ChannelMessage.objects.create(channel=channel, sender=sender, body="hi")
        result = recipients("channel_message", message=message)
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
            recipients=[state["active_one"].user_id],
        )

        jobs = _notification_jobs(in_memory_procrastinate, "elimination")
        assert len(jobs) == 1
        assert jobs[0]["args"]["user_ids"] == [state["active_one"].user_id]

    @pytest.mark.django_db
    def test_no_job_deferred_when_there_are_no_recipients(
        self, emit_game, in_memory_procrastinate
    ):
        state = emit_game()
        emit.emit("elimination", game=state["game"], recipients=[])

        assert _notification_jobs(in_memory_procrastinate, "elimination") == []

    @pytest.mark.django_db
    def test_manager_label_and_deadline_are_inferred_into_copy(self, emit_game, in_memory_procrastinate):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        emit.emit("game_resumed", game=state["game"], actor=actor)

        jobs = _notification_jobs(in_memory_procrastinate, "game_resumed")
        assert len(jobs) == 1
        assert jobs[0]["args"]["body"] == f"Game resumed by the Game Master ({actor.username}). New deadline: N/A"

    @pytest.mark.django_db
    def test_email_transport_defers_email_notification(self, emit_game, in_memory_procrastinate):
        state = emit_game()
        emit.emit("game_start", game=state["game"])

        email_jobs = [
            j for j in in_memory_procrastinate.jobs.values()
            if j["task_name"] == "email_service.send_email_notification"
        ]
        assert len(email_jobs) == 1
        assert "Game Started" in email_jobs[0]["args"]["subject"]
