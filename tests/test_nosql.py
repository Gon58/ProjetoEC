import os
import unittest

from pymongo import MongoClient


class TestNoSQLStorage(unittest.TestCase):
    def setUp(self):
        self.client = MongoClient(host=os.getenv("MONGO_HOST", "localhost"), port=27017)
        self.db = self.client[os.getenv("MONGO_DB", "ec_project")]
        self.collection = self.db["steam_reviews"]
        
        self.test_doc = {
            "recommendationid": "test_id_999",
            "review": "Testing the NoSQL insertion with a mock review.",
            "is_market_related": True,
            "source": "unit_test"
        }

    def test_insert_and_retrieve_document(self):
        self.collection.update_one(
            {"recommendationid": self.test_doc["recommendationid"]},
            {"$set": self.test_doc},
            upsert=True
        )

        retrieved_doc = self.collection.find_one({"recommendationid": "test_id_999"})

        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc["recommendationid"], "test_id_999")
        self.assertTrue(retrieved_doc["is_market_related"])
        self.assertEqual(retrieved_doc["source"], "unit_test")

    def tearDown(self):
        self.collection.delete_one({"recommendationid": "test_id_999"})

if __name__ == '__main__':
    unittest.main()