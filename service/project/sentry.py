import re

DEFAULT_TRACES_SAMPLE_RATE = 0.02
POLLED_TRACES_SAMPLE_RATE = 0.002

UNTRACED_PATHS = [
    re.compile(r"^/health/$"),
    re.compile(r"^/version/$"),
    re.compile(r"^/update/check/$"),
    re.compile(r"^/users/\d+/picture/[^/]+$"),
    re.compile(r"^/variants/[^/]+/nations/[^/]+/flag/[^/]+$"),
]

POLLED_PATHS = [
    re.compile(r"^/game/[^/]+/$"),
    re.compile(r"^/games/[^/]+/channels/$"),
]


def traces_sampler(sampling_context):
    environ = sampling_context.get("wsgi_environ")
    if environ is None:
        return DEFAULT_TRACES_SAMPLE_RATE

    path = environ.get("PATH_INFO", "")
    if any(pattern.match(path) for pattern in UNTRACED_PATHS):
        return 0
    if environ.get("REQUEST_METHOD") == "GET" and any(pattern.match(path) for pattern in POLLED_PATHS):
        return POLLED_TRACES_SAMPLE_RATE
    return DEFAULT_TRACES_SAMPLE_RATE
