import json
import logging
import requests

from opentelemetry import trace

from .serializers import AdjudicationSerializer
from common.constants import ADJUDICATION_BASE_URL

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


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
        }
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

        with tracer.start_as_current_span("adjudication.serialize_request"):
            serialized_phase = AdjudicationSerializer(phase, context={"game": phase.game}).data

        return _make_adjudication_request(phase, "resolve-with-options", method="POST", data=serialized_phase)
