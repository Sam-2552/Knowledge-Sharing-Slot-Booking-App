import redis
from flask import current_app


_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(current_app.config["REDIS_URL"])
    return _client
