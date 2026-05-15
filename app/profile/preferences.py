import json


DEFAULT_PREFERENCES = {
    "theme": {"mode": "light", "accent": "indigo"},
    "notifications": {"email": True, "in_app": True},
    "calendar": {"start_of_week": "monday", "timezone": "UTC"},
}


def load_preferences(raw):
    if not raw:
        return json.loads(json.dumps(DEFAULT_PREFERENCES))
    try:
        return json.loads(raw)
    except Exception:
        return json.loads(json.dumps(DEFAULT_PREFERENCES))


def dump_preferences(prefs) -> str:
    return json.dumps(prefs)


def deep_merge(target, updates):
    """Apply ``updates`` to ``target`` in place.

    Supports dotted-path keys so the UI can patch nested settings
    like ``theme.mode`` without sending the whole tree.
    """
    for key, value in updates.items():
        if "." in key:
            parts = key.split(".")
            cursor = target
            for part in parts[:-1]:
                if part not in cursor or not isinstance(cursor[part], dict):
                    cursor[part] = {}
                cursor = cursor[part]
            cursor[parts[-1]] = value
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target
