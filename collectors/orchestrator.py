"""Pipeline orchestrator - runs all collectors in sequence."""

import sys
import time
import os
from pathlib import Path
from typing import Dict, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.booking_collector import BookingCollector
from collectors.google_analytics_collector import GoogleAnalyticsCollector


class CommercialIntelligencePipeline:
    def __init__(self):
        self.results = {}
        self.total_records = 0
        self.total_inserted = 0

    def run_all(self) -> Dict:
        """Run all data collectors."""
        print("\n" + "="*60)
        print("COMMERCIAL INTELLIGENCE PIPELINE - START")
        print("="*60 + "\n")

        pipeline_start = time.time()

        # Bookings
        print("[1/2] Fetching bookings...")
        try:
            collector = BookingCollector()
            fetched, inserted = collector.fetch_and_load()
            self.results["bookings"] = (fetched, inserted)
            self.total_records += fetched
            self.total_inserted += inserted
            print(f"  ✓ Bookings: {fetched} fetched, {inserted} inserted\n")
        except Exception as e:
            print(f"  ✗ Bookings failed: {e}\n")
            self.results["bookings"] = (0, 0)

        # GA4
        print("[2/2] Fetching Google Analytics 4...")
        try:
            collector = GoogleAnalyticsCollector()
            fetched, inserted = collector.fetch_and_load()
            self.results["ga4"] = (fetched, inserted)
            self.total_records += fetched
            self.total_inserted += inserted
            print(f"  ✓ GA4: {fetched} fetched, {inserted} inserted\n")
        except Exception as e:
            print(f"  ✗ GA4 failed: {e}\n")
            self.results["ga4"] = (0, 0)

        elapsed = time.time() - pipeline_start

        print("="*60)
        print("PIPELINE SUMMARY")
        print("="*60)
        print(f"Total records fetched: {self.total_records}")
        print(f"Total records inserted: {self.total_inserted}")
        print(f"Execution time: {elapsed:.2f}s")
        print("="*60 + "\n")

        return self.results


if __name__ == "__main__":
    pipeline = CommercialIntelligencePipeline()
    pipeline.run_all()
