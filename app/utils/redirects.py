def is_safe_next(target: str) -> bool:
    """Return True when ``target`` is safe to redirect to.

    Relative paths are always safe; full URLs are blocked.
    """
    if not target:
        return False
    if target.startswith(("http://", "https://")):
        return False
    return target.startswith("/")
