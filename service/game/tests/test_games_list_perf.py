"""Local benchmark harness for the MyGames page load pattern.

Production traces show one GET /games/ triggers ~7-8 parallel
GET /game/<id>/phase/<phase_id>/ fetches (the per-game phase fan-out).
This file lets us A/B that pattern against alternatives (e.g. embedding
a slim current_phase sub-object on the games list response) so we can
iterate locally before shipping.

Run with -s to see the printed comparison table:

    docker compose run --rm service \\
        python3 -m pytest game/tests/test_games_list_perf.py -s -v
"""
import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings
from django.urls import reverse
from rest_framework import status

from common.constants import (
    DeadlineMode,
    GameStatus,
    PhaseStatus,
    UnitType,
)
from game.models import Game


N_GAMES = 10
PHASES_PER_GAME = 6


@pytest.fixture
def heavy_user_games(
    db,
    primary_user,
    secondary_user,
    classical_variant,
    classical_england_nation,
    classical_france_nation,
    classical_edinburgh_province,
    classical_liverpool_province,
    classical_london_province,
):
    """Seed N_GAMES active games for primary_user, each with PHASES_PER_GAME
    phases and a small but non-trivial member/unit/supply-center footprint.

    Picked to roughly match a typical MyGames user. Returns the list of
    created Game objects."""
    games = []
    for game_index in range(N_GAMES):
        game = Game.objects.create(
            name=f"Perf Game {game_index}",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.DURATION,
        )
        primary_member = game.members.create(
            user=primary_user, nation=classical_england_nation
        )
        secondary_member = game.members.create(
            user=secondary_user, nation=classical_france_nation
        )

        for phase_index in range(PHASES_PER_GAME):
            is_current = phase_index == PHASES_PER_GAME - 1
            phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901 + phase_index,
                type="Movement",
                status=PhaseStatus.ACTIVE if is_current else PhaseStatus.COMPLETED,
                ordinal=phase_index + 1,
            )
            for province in (
                classical_edinburgh_province,
                classical_liverpool_province,
                classical_london_province,
            ):
                phase.units.create(
                    type=UnitType.FLEET,
                    nation=classical_england_nation,
                    province=province,
                )
                phase.supply_centers.create(
                    nation=classical_england_nation, province=province
                )
            phase.phase_states.create(member=primary_member, has_possible_orders=True)
            phase.phase_states.create(member=secondary_member, has_possible_orders=True)

        games.append(game)

    return games


def _measure(label, fn, *, trials=3, warmup=1):
    """Run fn `warmup` + `trials` times. Returns the median trial.

    A warm-up smooths over first-request overhead (connection setup,
    middleware import, query plan cache). Median of N trials damps any
    one-off slowdown."""
    for _ in range(warmup):
        fn()

    samples = []
    for _ in range(trials):
        with CaptureQueriesContext(connection) as ctx, override_settings(DEBUG=True):
            start = time.perf_counter()
            result = fn()
            elapsed_ms = (time.perf_counter() - start) * 1000
        samples.append(
            {
                "wall_ms": elapsed_ms,
                "sql_count": len(ctx.captured_queries),
                "sql_ms": sum(float(q["time"]) for q in ctx.captured_queries) * 1000,
                "result": result,
            }
        )
    samples.sort(key=lambda s: s["wall_ms"])
    median = samples[len(samples) // 2]
    return {"label": label, **median}


def _print_row(metrics, payload_bytes, http_calls):
    print(
        f"  {metrics['label']:<32} "
        f"http={http_calls:>2}  "
        f"sql={metrics['sql_count']:>4}  "
        f"sql_ms={metrics['sql_ms']:>7.1f}  "
        f"wall_ms={metrics['wall_ms']:>7.1f}  "
        f"bytes={payload_bytes:>7}"
    )


def _print_header():
    print()
    print(
        "  pattern                          "
        "http   sql    sql_ms     wall_ms    bytes"
    )
    print("  " + "-" * 78)


@pytest.mark.django_db
def test_current_pattern_baseline(authenticated_client, heavy_user_games):
    """Today's MyGames flow: GET /games/, then GET /game/<id>/phase/<phase_id>/
    for each returned game. Measured serially — production parallelism wins
    back some wall time, but SQL count, SQL time, and payload bytes are
    apples-to-apples."""

    games_metrics = _measure(
        "GET /games/",
        lambda: authenticated_client.get(reverse("game-list") + "?mine=1"),
    )
    games_response = games_metrics["result"]
    assert games_response.status_code == status.HTTP_200_OK
    games_list = games_response.data.get("results", games_response.data)
    # The session may leak a couple of practice games owned by primary_user
    # via other session-scoped fixtures. Take only the ones we created here.
    games_list = [g for g in games_list if g["name"].startswith("Perf Game ")]
    assert len(games_list) == N_GAMES
    games_bytes = len(games_response.content)

    phase_targets = [(g["id"], g["current_phase_id"]) for g in games_list]

    phase_metrics_list = []
    phase_total_bytes = 0
    for game_id, phase_id in phase_targets:
        m = _measure(
            f"  GET phase {game_id}",
            lambda gid=game_id, pid=phase_id: authenticated_client.get(
                reverse("phase-retrieve", args=[gid, pid])
            ),
        )
        assert m["result"].status_code == status.HTTP_200_OK
        phase_metrics_list.append(m)
        phase_total_bytes += len(m["result"].content)

    phase_sql_total = sum(m["sql_count"] for m in phase_metrics_list)
    phase_sql_ms_total = sum(m["sql_ms"] for m in phase_metrics_list)
    phase_wall_ms_total = sum(m["wall_ms"] for m in phase_metrics_list)

    total_http = 1 + len(phase_metrics_list)
    total_sql = games_metrics["sql_count"] + phase_sql_total
    total_sql_ms = games_metrics["sql_ms"] + phase_sql_ms_total
    # Wall time is reported two ways: serial sum (worst case if the client
    # were sequential), and max-of-phase + games (best-case parallel client).
    serial_wall_ms = games_metrics["wall_ms"] + phase_wall_ms_total
    parallel_wall_ms = games_metrics["wall_ms"] + max(
        (m["wall_ms"] for m in phase_metrics_list), default=0
    )
    total_bytes = games_bytes + phase_total_bytes

    _print_header()
    _print_row(games_metrics, games_bytes, 1)
    print(
        f"  {'per-phase fetch (x'+str(len(phase_metrics_list))+')':<32} "
        f"http={len(phase_metrics_list):>2}  "
        f"sql={phase_sql_total:>4}  "
        f"sql_ms={phase_sql_ms_total:>7.1f}  "
        f"wall_ms={phase_wall_ms_total:>7.1f}  "
        f"bytes={phase_total_bytes:>7}"
    )
    print("  " + "-" * 78)
    print(
        f"  {'TOTAL (current, serial)':<32} "
        f"http={total_http:>2}  "
        f"sql={total_sql:>4}  "
        f"sql_ms={total_sql_ms:>7.1f}  "
        f"wall_ms={serial_wall_ms:>7.1f}  "
        f"bytes={total_bytes:>7}"
    )
    print(
        f"  {'TOTAL (current, parallel*)':<32} "
        f"http={total_http:>2}  "
        f"sql={total_sql:>4}  "
        f"sql_ms={total_sql_ms:>7.1f}  "
        f"wall_ms={parallel_wall_ms:>7.1f}  "
        f"bytes={total_bytes:>7}"
    )
    print("  (* parallel = games_list + max(per-phase), upper bound on speedup)")


@pytest.mark.django_db
def test_combined_pattern(authenticated_client, heavy_user_games):
    """Proposed shape: a single GET /games/ that already carries the slim
    current_phase data MyGames needs. Right now this is a placeholder — it
    just measures the current games-list response. Once Option A lands
    (embed a slim current_phase on GameListSerializer) this baseline will
    move; the assertions stay the same."""

    metrics = _measure(
        "GET /games/ (combined)",
        lambda: authenticated_client.get(reverse("game-list") + "?mine=1"),
    )
    response = metrics["result"]
    assert response.status_code == status.HTTP_200_OK
    games_list = response.data.get("results", response.data)
    # The session may leak a couple of practice games owned by primary_user
    # via other session-scoped fixtures. Take only the ones we created here.
    games_list = [g for g in games_list if g["name"].startswith("Perf Game ")]
    assert len(games_list) == N_GAMES
    payload_bytes = len(response.content)

    _print_header()
    _print_row(metrics, payload_bytes, 1)
    print("  (single request — no fan-out)")
