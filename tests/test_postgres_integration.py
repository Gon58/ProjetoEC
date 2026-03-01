"""
Test Suite for PostgreSQL Integration Logic
===========================================
This test suite validates the data processing pipeline for the Counter-Strike skin market analysis:
1. Utility functions: Decimal conversion and Base64 decoding.
2. API integration: Mocked Skinport API responses.
3. Dataset processing: Mocked Kaggle folder structure and CSV reading.
4. DB ingestion: Full SQLAlchemy flow using in-memory SQLite and temporary CSV files.
5. Real data check: Verifies the integrity of 'combined_data.csv' if present.
"""

import csv
import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from postgres_connection import (
    Base,
    Skin,
    fetch_skinport_data,
    get_kaggle_processed_data,
    load_from_csv_to_db,
)
from utils import decode_base64, to_decimal_2



class TestPostgresIntegration(unittest.TestCase):

    def test_to_decimal_2(self):
        """Test conversion to Decimal with 2 decimal places."""
        self.assertEqual(to_decimal_2(10.555), Decimal("10.56"))
        self.assertEqual(to_decimal_2(None), Decimal("0.00"))
        self.assertEqual(to_decimal_2("12.3"), Decimal("12.30"))
        self.assertEqual(to_decimal_2(float("nan")), Decimal("0.00"))

    def test_decode_base64(self):
        """Test Base64 decoding."""
        # "VGVzdA==" is "Test" in base64
        self.assertEqual(decode_base64("VGVzdA=="), "Test")
        # Should return original string if invalid
        self.assertEqual(decode_base64("Invalid!"), "Invalid!")

    @patch("requests.get")
    def test_fetch_skinport_data_success(self, mock_get):
        """Test fetching data from Skinport API with success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "market_hash_name": "AK-47 | Redline",
                "currency": "USD",
                "min_price": 10.5,
                "max_price": 20.0,
                "mean_price": 15.0,
                "median_price": 14.5,
                "quantity": 100,
            }
        ]
        mock_get.return_value = mock_response

        data = fetch_skinport_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["market_hash_name"], "AK-47 | Redline")
        self.assertEqual(data[0]["quantity_sold"], 100)

    @patch("requests.get")
    def test_fetch_skinport_data_failure(self, mock_get):
        """Test Skinport API failure handling."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        data = fetch_skinport_data()
        self.assertEqual(data, [])

    @patch("os.path.exists")
    @patch("pandas.read_csv")
    def test_get_kaggle_processed_data(self, mock_read_csv, mock_exists):
        """Test processing Kaggle dataset files."""
        # Mock existence of index file and one item file
        mock_exists.side_effect = lambda x: True

        # Mock index file content
        df_index = pd.DataFrame(
            {
                "item_hash_name_base64": ["QUstNDcgfCBSZWRsaW5l"],  # "AK-47 | Redline"
                "file_name": ["item1.csv"],
            }
        )

        # Mock item file content
        df_item = pd.DataFrame({"price_dollar": [10.0, 20.0, 15.0], "sells": [1, 2, 3]})

        mock_read_csv.side_effect = [df_index, df_item]

        data = get_kaggle_processed_data("fake_dir")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["market_hash_name"], "AK-47 | Redline")
        self.assertEqual(data[0]["min_price"], 10.0)
        self.assertEqual(data[0]["max_price"], 20.0)
        self.assertEqual(data[0]["quantity_sold"], 6)  # 1+2+3

    def test_load_from_csv_to_db(self):
        """Test loading CSV data into the database."""
        # Use SQLite in-memory for testing the SQLAlchemy part
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()

        # Create a temporary CSV
        temp_csv = "temp_test_db.csv"
        csv_content = [
            ["market_hash_name", "currency", "min_price", "max_price", "mean_price", "median_price", "quantity_sold"],
            ["AK-47 | Redline", "USD", "10.5", "20.0", "15.0", "14.5", "100"],
        ]

        with open(temp_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_content)

        try:
            load_from_csv_to_db(temp_csv, session)

            # Verify data in DB
            skin = session.query(Skin).filter_by(name="AK-47 | Redline").first()
            self.assertIsNotNone(skin)
            self.assertEqual(skin.currency, "USD")
            self.assertEqual(skin.min_price, Decimal("10.50"))
            self.assertEqual(skin.max_price, Decimal("20.00"))
            self.assertEqual(skin.quantity_sold, 100)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
            session.close()


    def test_combined_data_csv_structure(self):
        """Verifies if combined_data.csv exists and has the expected columns."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data_scripts", "combined_data.csv")

        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, nrows=5)
            expected_columns = [
                "market_hash_name",
                "currency",
                "min_price",
                "max_price",
                "mean_price",
                "median_price",
                "quantity_sold",
            ]
            for col in expected_columns:
                self.assertIn(col, df.columns, f"Column {col} missing in combined_data.csv")
            print(f"\n[INFO] Validated structure of existing {csv_path}")
        else:
            self.skipTest("combined_data.csv not found, skipping real data structure test.")


if __name__ == "__main__":
    unittest.main()
