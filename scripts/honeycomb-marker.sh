#!/bin/sh

if [ -z "$HONEYCOMB_MARKERS_API_KEY" ]; then
    echo "HONEYCOMB_MARKERS_API_KEY is not set; skipping Honeycomb marker." >&2
    exit 0
fi

MARKER_TYPE="$1"
MARKER_MESSAGE="$2"

if ! curl --silent --show-error --fail --max-time 10 \
    --request POST "https://api.honeycomb.io/1/markers/__all__" \
    --header "X-Honeycomb-Team: $HONEYCOMB_MARKERS_API_KEY" \
    --header "Content-Type: application/json" \
    --data "{\"type\": \"$MARKER_TYPE\", \"message\": \"$MARKER_MESSAGE\"}"; then
    echo "Failed to create Honeycomb marker." >&2
fi

exit 0
