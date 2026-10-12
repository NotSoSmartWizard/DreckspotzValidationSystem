import unittest
import pandas as pd
import os
from io import StringIO
from app.code.clearduplicates import parse_date, is_within_radius, remove_duplicates, clearduplicates_logger

clearduplicates_logger.disabled = True

class TestDuplicateRemoval(unittest.TestCase):

    def setUp(self):
        clearduplicates_logger.disabled = True

    def test_parse_date(self):
        """Test various date formats for correct parsing."""
        self.assertEqual(parse_date("2024-01-15 09:19:00"), pd.Timestamp("2024-01-15 09:19:00"))
        self.assertEqual(parse_date("15.01.2024 09:19"), pd.Timestamp("2024-01-15 09:19:00"))
        self.assertTrue(pd.isna(parse_date("invalid-date-string")))

    def test_within_radius(self):
        """Test points within the radius."""
        self.assertTrue(is_within_radius(52.5200, 13.4050, 52.5201, 13.4051, radius=15))

    def test_outside_radius(self):
        """Test points outside the radius."""
        self.assertFalse(is_within_radius(52.5200, 13.4050, 52.5300, 13.4150, radius=500))

    def test_on_radius(self):
        """Test points exactly on the radius."""
        self.assertTrue(is_within_radius(52.5200, 13.4050, 52.5201, 13.4051, radius=14.25))

    def test_zero_radius(self):
        """Test points with radius 0."""
        self.assertTrue(is_within_radius(52.5200, 13.4050, 52.5200, 13.4050, radius=0))
        self.assertFalse(is_within_radius(52.5200, 13.4050, 52.5201, 13.4051, radius=0))

    def test_remove_duplicates_time_filter(self):
        """Test duplicate removal with different time duration parameters."""
        csv_data = """ID,LATITUDE,LONGITUDE,SPOTTED_AT,LITTER_CATEGORY_PRESELECT,LITTER_CATEGORY,IMAGE
        1,40.748817,-73.985428,2024-01-15 09:19:00,Plastic,Bottle,http://example.com/image1.jpg
        2,40.748817,-73.985428,2024-01-15 09:20:00,Plastic,Bottle,http://example.com/image2.jpg
        3,40.748817,-73.985428,2024-01-15 09:30:00,Plastic,Bottle,http://example.com/image3.jpg
        4,40.748817,-73.985428,2024-01-15 10:05:00,Metal,Can,http://example.com/image4.jpg
        5,40.748817,-73.985428,2024-01-15 10:05:00,Plastic,Bottle,http://example.com/image5.jpg
        """
        df = pd.read_csv(StringIO(csv_data))
        output_path = "cleaned_test_time_filter.csv"

        # Test with 10 minutes duration
        remove_duplicates(df, output_path, duration_minutes=10, radius_meters=1)
        cleaned_df = pd.read_csv(output_path)
        self.assertEqual(len(cleaned_df), 4)
        self.assertIn(1, cleaned_df['ID'].values)
        self.assertIn(3, cleaned_df['ID'].values)
        self.assertIn(4, cleaned_df['ID'].values)
        self.assertIn(5, cleaned_df['ID'].values)

        # Test with 60 minutes duration
        remove_duplicates(cleaned_df, output_path, duration_minutes=60, radius_meters=1)
        cleaned_df_new = pd.read_csv(output_path)
        self.assertEqual(len(cleaned_df_new), 2)
        self.assertIn(1, cleaned_df_new['ID'].values)
        self.assertIn(4, cleaned_df_new['ID'].values)

        # Remove test file
        if os.path.exists(output_path):
            os.remove(output_path)

    def test_remove_duplicates_radius_filter(self):
        """Test duplicate removal with different radius parameters."""
        csv_data = """ID,LATITUDE,LONGITUDE,SPOTTED_AT,LITTER_CATEGORY_PRESELECT,LITTER_CATEGORY,IMAGE
        1,40.748817,-73.985428,2024-01-15 09:19:00,Plastic,Bottle,http://example.com/image1.jpg
        2,40.748999,-73.985428,2024-01-15 09:20:00,Plastic,Bottle,http://example.com/image2.jpg
        3,40.749350,-73.985428,2024-01-15 09:30:00,Plastic,Bottle,http://example.com/image3.jpg
        4,40.748817,-73.985428,2024-01-15 10:05:00,Metal,Can,http://example.com/image4.jpg
        """
        df = pd.read_csv(StringIO(csv_data))
        output_path = "cleaned_test_radius_filter.csv"

        # Test with 1000 meters radius
        remove_duplicates(df, output_path, duration_minutes=1000, radius_meters=1000)
        cleaned_df = pd.read_csv(output_path)
        self.assertEqual(len(cleaned_df), 2)
        self.assertIn(1, cleaned_df['ID'].values)
        self.assertIn(4, cleaned_df['ID'].values)

        # Test with 30 meters radius
        df = pd.read_csv(StringIO(csv_data))
        remove_duplicates(df, output_path, duration_minutes=1000, radius_meters=30)
        cleaned_df = pd.read_csv(output_path)
        self.assertEqual(len(cleaned_df), 3)
        self.assertIn(1, cleaned_df['ID'].values)
        self.assertIn(3, cleaned_df['ID'].values)
        self.assertIn(4, cleaned_df['ID'].values)

        # Remove test file
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == '__main__':
    unittest.main()
