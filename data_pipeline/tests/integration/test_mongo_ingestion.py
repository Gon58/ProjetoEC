import os
from pymongo import MongoClient


def test_mongo_insert():
    client = MongoClient(host=os.getenv("MONGO_HOST", "localhost"), port=27017)
    db = client[os.getenv("MONGO_DB", "ec_project")]
    col = db["steam_reviews"]

    doc = {
        "recommendationid": "test123",
        "review": "test review",
        "is_market_related": True,
        "source": "test",
    }

    col.replace_one({"recommendationid": doc["recommendationid"]}, doc, upsert=True)

    result = col.find_one({"recommendationid": "test123"})

    assert result is not None
    assert result["is_market_related"] is True

    col.delete_one({"recommendationid": "test123"})