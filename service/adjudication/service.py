import json
import logging
import requests

from django.db import transaction
from opentelemetry import metrics, trace

from .canonical import (
    canonicalize_godip_response,
    canonicalize_python_response,
    diff_canonical,
)
from .models import ShadowAdjudicationDiff
from .serializers import AdjudicationSerializer
from adjudicator.engine import Engine
from adjudicator.options import get_options
from adjudicator.serializers import (
    deserialize_game_state,
    deserialize_variant,
    serialize_game_state,
)
from common.constants import ADJUDICATION_BASE_URL
from phase.utils import phase_to_canonical_game_state
from variant.utils import variant_to_canonical_dict

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

_meter = metrics.get_meter(__name__)
_shadow_matches_counter = _meter.create_counter("adjudication.shadow.matches")
_shadow_mismatches_counter = _meter.create_counter("adjudication.shadow.mismatches")
_shadow_errors_counter = _meter.create_counter("adjudication.shadow.errors")


def _make_adjudication_request(phase, endpoint, method="GET", data=None):
    url = f"{ADJUDICATION_BASE_URL}/{endpoint}/{phase.variant.name}"
    context = {"game": phase.game}

    with tracer.start_as_current_span(
        f"adjudication.{endpoint}",
        attributes={
            "http.method": method.upper(),
            "http.url": url,
            "adjudication.endpoint": endpoint,
            "adjudication.variant": phase.variant.name,
        },
    ) as span:
        # Log the request attempt
        logger.info(f"Making {method.upper()} request to adjudication service: {url}")
        if data and method.upper() == "POST":
            logger.info(f"Request payload: {json.dumps(data, indent=2)}")

        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data)
            else:
                response = requests.get(url)

            logger.info(f"Received response with status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")

            span.set_attribute("http.status_code", response.status_code)

            response.raise_for_status()

            with tracer.start_as_current_span("adjudication.parse_json") as parse_span:
                response_data = response.json()
                parse_span.set_attribute("response.size_bytes", len(response.text))
                logger.info(f"Response data: {json.dumps(response_data, indent=2)}")

            with tracer.start_as_current_span("adjudication.deserialize_response") as deser_span:
                serializer = AdjudicationSerializer(data=response_data, context=context)
                serializer.is_valid(raise_exception=True)

                validated_data = serializer.validated_data
                try:
                    if validated_data and isinstance(validated_data, dict):
                        if "units" in validated_data:
                            deser_span.set_attribute("units.count", len(validated_data["units"]))
                        if "supply_centers" in validated_data:
                            deser_span.set_attribute("supply_centers.count", len(validated_data["supply_centers"]))
                        if "resolutions" in validated_data:
                            deser_span.set_attribute("resolutions.count", len(validated_data["resolutions"]))
                except (KeyError, TypeError):
                    pass

                logger.info(f"Serializer response data: {validated_data}")

            logger.info(f"Successfully processed adjudication request for endpoint: {endpoint}")
            return serializer.validated_data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred for {method.upper()} {url}: {e}")
            logger.error(f"Response status code: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            span.set_attribute("error", True)
            span.set_attribute("error.type", "HTTPError")
            span.set_attribute("http.status_code", response.status_code)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception occurred for {method.upper()} {url}: {e}")
            span.set_attribute("error", True)
            span.set_attribute("error.type", "RequestException")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from {url}: {e}")
            logger.error(f"Response text: {response.text}")
            span.set_attribute("error", True)
            span.set_attribute("error.type", "JSONDecodeError")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during adjudication request to {url}: {e}")
            if "response" in locals():
                logger.error(f"Response status: {response.status_code}, text: {response.text}")
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            raise


def start(phase):
    logger.info(f"Starting adjudication for phase {phase.id} of game {phase.game.id}")
    return _make_adjudication_request(phase, "start-with-options")


def resolve(phase):
    with tracer.start_as_current_span("adjudication.resolve") as span:
        span.set_attribute("phase.id", phase.id)
        span.set_attribute("game.id", str(phase.game.id))
        logger.info(f"Resolving adjudication for phase {phase.id} of game {phase.game.id}")

        # Snapshot the pre-adjudication state before godip is called, so the
        # shadow comparison runs against the inputs godip saw.
        canonical_variant = None
        pre_state = None
        try:
            canonical_variant = variant_to_canonical_dict(phase.variant)
            pre_state = phase_to_canonical_game_state(phase)
        except Exception:
            _shadow_errors_counter.add(1)
            logger.exception("Failed to capture shadow-mode inputs for phase %s", phase.id)

        with tracer.start_as_current_span("adjudication.serialize_request"):
            serialized_phase = AdjudicationSerializer(phase, context={"game": phase.game}).data

        godip_response = _make_adjudication_request(
            phase, "resolve-with-options", method="POST", data=serialized_phase
        )

        if canonical_variant is not None and pre_state is not None:
            _run_shadow_comparison(phase, canonical_variant, pre_state, godip_response)

        return godip_response


def compute_shadow_diff(canonical_variant, pre_state, godip_response):
    """Adjudicate pre_state with the Python engine and diff the result
    against a godip response. Returns (StructuredDiff, python_states)."""
    variant = deserialize_variant(canonical_variant)
    state = deserialize_game_state(pre_state, variant)
    python_states = Engine().adjudicate(state)
    options = get_options(python_states[-1])
    diff = diff_canonical(
        canonicalize_godip_response(godip_response),
        canonicalize_python_response(python_states, options),
    )
    return diff, python_states


def _run_shadow_comparison(phase, canonical_variant, pre_state, godip_response):
    """Run the Python adjudicator alongside godip and compare the outcomes.

    Never raises: a shadow-mode failure must not affect the user-facing
    resolution flow. Matches increment a telemetry counter; mismatches
    additionally persist a ShadowAdjudicationDiff row for later replay.
    """
    try:
        with tracer.start_as_current_span("adjudication.shadow_comparison"):
            diff, python_states = compute_shadow_diff(
                canonical_variant, pre_state, godip_response
            )

            if diff.matched:
                _shadow_matches_counter.add(1)
                return

            _shadow_mismatches_counter.add(1)
            with transaction.atomic():
                ShadowAdjudicationDiff.objects.create(
                    phase=phase,
                    tier=diff.tier,
                    pre_state=pre_state,
                    godip_response=godip_response,
                    python_response=[serialize_game_state(s) for s in python_states],
                    diff_summary=diff.to_dict(),
                )
            logger.warning(
                "Shadow adjudication mismatch for phase %s (%s): tier=%s diff=%s",
                phase.id,
                phase.name,
                diff.tier,
                diff.to_dict(),
            )
    except Exception:
        _shadow_errors_counter.add(1)
        logger.exception("Shadow adjudication comparison failed for phase %s", phase.id)
