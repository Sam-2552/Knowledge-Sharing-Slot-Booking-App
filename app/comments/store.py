from pymongo import MongoClient
from flask import current_app

_client = None


def _collection():
    global _client
    if _client is None:
        _client = MongoClient(
            current_app.config["MONGO_URI"], serverSelectionTimeoutMS=2000
        )
    return _client.get_default_database()["comments"]


def add_comment(slot_id: int, author_email: str, author_name: str, body: str):
    doc = {
        "slot_id": int(slot_id),
        "author_email": author_email,
        "author_name": author_name,
        "body": body,
    }
    _collection().insert_one(doc)
    return doc


def list_for_slot(slot_id: int):
    cursor = _collection().find({"slot_id": int(slot_id)}).sort("_id", 1)
    return [_serialise(d) for d in cursor]


def search(filter_doc: dict):
    cursor = _collection().find(filter_doc).limit(50)
    return [_serialise(d) for d in cursor]


def _serialise(doc):
    doc.pop("_id", None)
    return doc
