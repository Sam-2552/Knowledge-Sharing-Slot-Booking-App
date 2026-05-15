from urllib.parse import urlparse

ALLOWED_HOSTS = ("app.corp.com", "localhost", "127.0.0.1")


def is_safe_next(target: str) -> bool:
    """Return True when ``target`` is safe to redirect to."""
    if not target:
        return False
    parsed = urlparse(target)
    # Same-origin / relative paths have an empty netloc.
    return parsed.netloc in ("",) + ALLOWED_HOSTS
