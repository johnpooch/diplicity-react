SPIKE_PREFIX = "/spike/"


def exclude_spike_endpoints(endpoints, **kwargs):
    return [endpoint for endpoint in endpoints if not endpoint[0].startswith(SPIKE_PREFIX)]
