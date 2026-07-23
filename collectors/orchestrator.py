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
from collectors.meta_collector import MetaCollector
from collectors.google_ads_collector import GoogleAdsCollector
from collectors.google_analytics_collector import GoogleAnalyticsCollector
from collectors.tiktok_collector import TikTokCollector


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
        print("[1/6] Fetching bookings...")
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

        # Meta (Ads + Organic)
        print("[2/6] Fetching Meta Ads...")
        try:
            collector = MetaCollector()
            results = collector.fetch_and_load_all()
            meta_total_fetched = sum(r[0] for r in results.values())
            meta_total_inserted = sum(r[1] for r in results.values())
            self.results["meta"] = results
            self.total_records += meta_total_fetched
            self.total_inserted += meta_total_inserted
            for source, (fetched, inserted) in results.items():
                print(f"  ✓ {source}: {fetched} fetched, {inserted} inserted")
            print()
        except Exception as e:
            print(f"  ✗ Meta failed: {e}\n")
            self.results["meta"] = {}

        # Google Ads
        print("[3/6] Fetching Google Ads...")
        try:
            collector = GoogleAdsCollector()
            fetched, inserted = collector.fetch_and_load()
            self.results["google_ads"] = (fetched, inserted)
            self.total_records += fetched
            self.total_inserted += inserted
            print(f"  ✓ Google Ads: {fetched} fetched, {inserted} inserted\n")
        except Exception as e:
            print(f"  ✗ Google Ads failed: {e}\n")
            self.results["google_ads"] = (0, 0)

        # GA4
        print("[4/6] Fetching Google Analytics 4...")
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

        # TikTok
        print("[5/6] Fetching TikTok...")
        try:
            collector = TikTokCollector()
            fetched, inserted = collector.fetch_and_load()
            self.results["tiktok"] = (fetched, inserted)
            self.total_records += fetched
            self.total_inserted += inserted
            print(f"  ✓ TikTok: {fetched} fetched, {inserted} inserted\n")
        except Exception as e:
            print(f"  ✗ TikTok failed: {e}\n")
            self.results["tiktok"] = (0, 0)

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
