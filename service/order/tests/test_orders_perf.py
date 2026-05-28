"""Local benchmark harness for the orders endpoints.

Production traces (14 days):
  GET /game/<id>/orders/<phase_id>  P50  64 ms  P95  404 ms  P99 1072 ms
  POST /game/<id>/orders/           P50 195 ms  P95  452 ms  P99  674 ms

The list endpoint has a striking ~10x P50→P99 spread — the slow tail is
where there's headroom. The create endpoint is hitting an interactive
action ~190 ms below the floor we'd want (sub-100 ms).

Run with -s to see the printed comparison table:

    docker compose run --rm service \\
        python3 -m pytest order/tests/test_orders_perf.py -s -v
"""
import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings
from django.urls import reverse
from rest_framework import status

from common.constants import OrderType


def _measure(label, fn, *, trials=3, warmup=1):
    """Warm-up + median-of-trials. Returns label + median sample."""
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
    return {"label": label, **samples[len(samples) // 2]}


def _print_row(label, metrics, payload_bytes):
    print(
        f"  {label:<32} "
        f"sql={metrics['sql_count']:>4}  "
        f"sql_ms={metrics['sql_ms']:>7.1f}  "
        f"wall_ms={metrics['wall_ms']:>7.1f}  "
        f"bytes={payload_bytes:>7}"
    )


def _print_header():
    print()
    print("  pattern                          sql    sql_ms     wall_ms    bytes")
    print("  " + "-" * 70)


@pytest.fixture
def game_with_orders(
    db,
    game_with_options,
    primary_user,
    classical_england_nation,
    classical_edinburgh_province,
    classical_liverpool_province,
    classical_london_province,
):
    """Game with options populated AND a handful of existing orders so the
    list endpoint isn't empty. England (primary_user) has orders on bud and
    tri (the two sources covered by sample_options)."""
    from order.models import Order
    from province.models import Province

    game = game_with_options
    phase = game.current_phase
    phase_state = phase.phase_states.get(member__user=primary_user)

    bud = Province.objects.get(province_id="bud", variant=game.variant)
    tri = Province.objects.get(province_id="tri", variant=game.variant)
    gal = Province.objects.get(province_id="gal", variant=game.variant)
    ven = Province.objects.get(province_id="ven", variant=game.variant)

    # The sample_options fixture only covers bud and tri sources for England.
    Order.objects.create(
        phase_state=phase_state, order_type=OrderType.MOVE, source=bud, target=gal,
    )
    Order.objects.create(
        phase_state=phase_state, order_type=OrderType.MOVE, source=tri, target=ven,
    )
    return game


@pytest.mark.django_db
def test_list_orders_baseline(authenticated_client, game_with_orders):
    """GET /game/<id>/orders/<phase_id>."""
    game = game_with_orders
    phase = game.current_phase
    url = reverse("order-list", args=[game.id, phase.id])

    metrics = _measure("GET /orders/", lambda: authenticated_client.get(url))
    response = metrics["result"]
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    _print_header()
    _print_row("GET /orders/ (2 orders)", metrics, len(response.content))


@pytest.mark.django_db
def test_list_orders_with_incomplete_orders(
    authenticated_client, game_with_options, primary_user
):
    """GET /game/<id>/orders/ with two INCOMPLETE orders (source-only,
    no order_type yet). This is the scenario the production P99 tail
    points at: each incomplete order computes options_display, which
    historically did a variant.provinces.get(province_id=...) per option.
    Regression guard for the variant.provinces lookup N+1."""
    from order.models import Order
    from province.models import Province

    game = game_with_options
    phase = game.current_phase
    phase_state = phase.phase_states.get(member__user=primary_user)

    bud = Province.objects.get(province_id="bud", variant=game.variant)
    tri = Province.objects.get(province_id="tri", variant=game.variant)
    Order.objects.create(phase_state=phase_state, source=bud)
    Order.objects.create(phase_state=phase_state, source=tri)

    url = reverse("order-list", args=[game.id, phase.id])
    metrics = _measure("GET /orders/ (incomplete)", lambda: authenticated_client.get(url))
    assert metrics["result"].status_code == status.HTTP_200_OK

    _print_header()
    _print_row("GET /orders/ (2 incomplete)", metrics, len(metrics["result"].content))


@pytest.mark.django_db
def test_create_order_partial_baseline(authenticated_client, game_with_options):
    """POST /game/<id>/orders/ with a partial selection (source only).
    Exercises the validate + return path without saving."""
    game = game_with_options
    url = reverse("order-create", args=[game.id])

    metrics = _measure(
        "POST /orders/ (partial)",
        lambda: authenticated_client.post(url, {"selected": ["bud"]}, format="json"),
    )
    response = metrics["result"]
    assert response.status_code == status.HTTP_201_CREATED

    _print_header()
    _print_row("POST /orders/ (partial)", metrics, len(response.content))


@pytest.mark.django_db
def test_create_order_complete_baseline(authenticated_client, game_with_options):
    """POST /game/<id>/orders/ with a complete selection (source + Hold).
    Exercises the full path: validate, delete existing, save, re-fetch via
    with_related_data. This is what users do most: click → confirm."""
    game = game_with_options
    url = reverse("order-create", args=[game.id])

    metrics = _measure(
        "POST /orders/ (complete)",
        lambda: authenticated_client.post(
            url, {"selected": ["bud", "Hold"]}, format="json"
        ),
    )
    response = metrics["result"]
    assert response.status_code == status.HTTP_201_CREATED

    _print_header()
    _print_row("POST /orders/ (complete)", metrics, len(response.content))


def _print_queries(label, ctx):
    print()
    print(f"  {label} — {len(ctx.captured_queries)} queries")
    print("  " + "-" * 70)
    for i, q in enumerate(ctx.captured_queries, 1):
        sql = q["sql"]
        if len(sql) > 130:
            sql = sql[:127] + "..."
        print(f"  {i:>2}. {sql}")


@pytest.mark.django_db
def test_query_breakdown_complete_create(authenticated_client, game_with_options):
    game = game_with_options
    url = reverse("order-create", args=[game.id])
    authenticated_client.post(url, {"selected": ["bud", "Hold"]}, format="json")  # warm
    with CaptureQueriesContext(connection) as ctx, override_settings(DEBUG=True):
        response = authenticated_client.post(
            url, {"selected": ["bud", "Hold"]}, format="json"
        )
    assert response.status_code == status.HTTP_201_CREATED
    _print_queries("POST /orders/ (complete)", ctx)


@pytest.mark.django_db
def test_query_breakdown_list(authenticated_client, game_with_orders):
    game = game_with_orders
    phase = game.current_phase
    url = reverse("order-list", args=[game.id, phase.id])
    authenticated_client.get(url)  # warm
    with CaptureQueriesContext(connection) as ctx, override_settings(DEBUG=True):
        response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    _print_queries("GET /orders/", ctx)
