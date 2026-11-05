"""MongoDB connection and shared collections."""

import os

from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "kiosk")

_client = MongoClient(MONGODB_URI)
_db = _client[MONGODB_DB]

orders_collection: Collection = _db["orders"]
counters_collection: Collection = _db["counters"]


def next_sequence(name: str) -> int:
    doc = counters_collection.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]
