"""Collector for Google Ads campaign performance data."""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
from database.db import Database

_DEFAULT_GOOGLE_ADS_API_VERSION = "v23"


class GoogleAdsCollector:
    def __init__(self):
        self.developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        self.db = Database()
        self.access_token = None
        self.base_url = f"https://googleads.googleapis.com/{_DEFAULT_GOOGLE_ADS_API_VERSION}"

    def _refresh_access_token(self) -> bool:
        """Refresh OAuth access token."""
        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            return True
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    def _get_headers(self) -> Dict:
        """Get request headers with auth."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "developer-token": self.developer_token,
            "login-customer-id": self.login_customer_id.replace("-", ""),
            "Content-Type": "application/json",
        }

    def _fetch_live(self) -> pd.DataFrame:
        """Fetch Google Ads campaign data via REST API."""
        if not self._refresh_access_token():
            return pd.DataFrame()

        try:
            customer_id_clean = self.customer_id.replace("-", "")
            endpoint = f"{self.base_url}/customers/{customer_id_clean}/googleAds:searchStream"
            headers = self._get_headers()

            since_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    ad_group.id,
                    ad_group.name,
                    ad_group_ad.ad.id,
                    ad_group_ad.ad.expanded_text_ad.headline_part1,
                    segments.date,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.average_cpc,
                    metrics.ctr,
                    metrics.conversions,
                    metrics.conversion_value_micros
                FROM ad_group_ad
                WHERE segments.date >= '{since_date}'
                AND campaign.status = ENABLED
            """

            payload = {"query": query}
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            records = []
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = response.json() if response.text else {}
                    if "results" in chunk:
                        for result in chunk["results"]:
                            row = result.get("googleAdsRow", {})
                            if not row:
                                continue

                            campaign = row.get("campaign", {})
                            ad_group = row.get("adGroup", {})
                            ad = row.get("adGroupAd", {}).get("ad", {})
                            metrics = row.get("metrics", {})
                            segments = row.get("segments", {})

                            records.append({
                                "id": f"{campaign.get('id')}_{segments.get('date')}",
                                "campaign_id": campaign.get("id"),
                                "campaign_name": campaign.get("name"),
                                "adgroup_id": ad_group.get("id"),
                                "adgroup_name": ad_group.get("name"),
                                "ad_id": ad.get("id"),
                                "ad_headline": ad.get("expandedTextAd", {}).get("headlinePart1", ""),
                                "date": segments.get("date"),
                                "impressions": int(metrics.get("impressions", 0)),
                                "clicks": int(metrics.get("clicks", 0)),
                                "cost_aed": float(metrics.get("costMicros", 0)) / 1_000_000,
                                "avg_cpc_aed": float(metrics.get("averageCpc", 0)) / 1_000_000,
                                "ctr": float(metrics.get("ctr", 0)),
                                "conversions": int(metrics.get("conversions", 0)),
                                "conversion_value_aed": float(metrics.get("conversionValueMicros", 0)) / 1_000_000,
                            })
                except (ValueError, KeyError):
                    continue

            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching Google Ads: {e}")
            return pd.DataFrame()

    def load_to_db(self, df: pd.DataFrame) -> int:
        """Load dataframe to database."""
        if df.empty:
            return 0

        try:
            return self.db.insert_dataframe(df, "google_ads_performance", if_exists="append")
        except Exception as e:
            print(f"Error loading Google Ads to database: {e}")
            return 0

    def fetch_and_load(self) -> tuple:
        """Fetch and load Google Ads data."""
        start_time = time.time()
        try:
            df = self._fetch_live()
            records_fetched = len(df)
            records_inserted = self.load_to_db(df)
            elapsed = time.time() - start_time

            self.db.log_pipeline_execution(
                "google_ads",
                records_fetched,
                records_inserted,
                "success",
                execution_time=elapsed
            )
            return records_fetched, records_inserted
        except Exception as e:
            elapsed = time.time() - start_time
            self.db.log_pipeline_execution(
                "google_ads",
                0,
                0,
                "failed",
                error=str(e),
                execution_time=elapsed
            )
            raise
