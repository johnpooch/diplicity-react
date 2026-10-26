from django.utils.http import parse_etags

# GZipMiddleware compresses our JSON responses, and because it re-encodes the
# body it downgrades the ETag it sends to a weak validator. Clients
# therefore replay `If-None-Match: W/"abc"` against an ETag we issued as
# `"abc"`, and a plain `==` never matches — so every conditional request falls
# through to a full 200. RFC 9110 13.1.2 requires If-None-Match to use the weak
# comparison function, which ignores the `W/` prefix on either side.
_WEAK_PREFIX = "W/"


def _strip_weak(etag):
    if etag.startswith(_WEAK_PREFIX):
        return etag[len(_WEAK_PREFIX) :]
    return etag


def if_none_match(request, etag):
    header = request.headers.get("If-None-Match")
    if not header:
        return False
    candidates = parse_etags(header)
    if candidates == ["*"]:
        return True
    target = _strip_weak(etag)
    return any(_strip_weak(candidate) == target for candidate in candidates)
