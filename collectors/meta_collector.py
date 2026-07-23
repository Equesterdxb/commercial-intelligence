"""Collector for Meta Ads and Facebook/Instagram organic content."""

import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
from database.db import Database


class MetaCollector:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        self.facebook_page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.instagram_business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.base_url = "https://graph.instagram.com/v18.0"
        self.db = Database()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request to Meta Graph API."""
        try:
            if params is None:
                params = {}
            params["access_token"] = self.access_token

            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Meta API request failed: {e}")
            return None

    def _parse_iso8601(self, timestamp_str: str) -> Optional[str]:
        """Parse ISO8601 timestamp with +0000 offset."""
        if not timestamp_str:
            return None
        try:
            if timestamp_str.endswith("+0000"):
                timestamp_str = timestamp_str[:-5] + "Z"
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            return timestamp_str

    def _fetch_meta_ads_insights(self) -> pd.DataFrame:
        """Fetch Meta Ads performance data."""
        try:
            endpoint = f"/{self.ad_account_id}/insights"
            params = {
                "fields": "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,date_start,impressions,clicks,spend,cpc,cpm,ctr,reach",
                "level": "ad",
                "time_range": json.dumps({
                    "since": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "until": datetime.now().strftime("%Y-%m-%d"),
                }),
            }
            response = self._make_request(endpoint, params)
            if not response or "data" not in response:
                return pd.DataFrame()

            records = []
            for item in response["data"]:
                records.append({
                    "id": f"{item.get('campaign_id')}_{item.get('date_start')}",
                    "campaign_id": item.get("campaign_id"),
                    "campaign_name": item.get("campaign_name"),
                    "adset_id": item.get("adset_id"),
                    "adset_name": item.get("adset_name"),
                    "ad_id": item.get("ad_id"),
                    "ad_name": item.get("ad_name"),
                    "date": item.get("date_start"),
                    "impressions": int(item.get("impressions", 0)),
                    "clicks": int(item.get("clicks", 0)),
                    "spend_aed": float(item.get("spend", 0)),
                    "cpc_aed": float(item.get("cpc", 0)),
                    "cpm_aed": float(item.get("cpm", 0)),
                    "ctr": float(item.get("ctr", 0)),
                    "reach": int(item.get("reach", 0)),
                })
            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching Meta Ads: {e}")
            return pd.DataFrame()

    def _fetch_instagram_organic(self) -> pd.DataFrame:
        """Fetch Instagram organic content."""
        try:
            endpoint = f"/{self.instagram_business_account_id}/media"
            params = {
                "fields": "id,caption,media_type,timestamp,like_count,comments_count,shares,ig_id",
            }
            response = self._make_request(endpoint, params)
            if not response or "data" not in response:
                return pd.DataFrame()

            records = []
            for item in response["data"]:
                records.append({
                    "id": item.get("id"),
                    "post_id": item.get("id"),
                    "caption": item.get("caption", ""),
                    "media_type": item.get("media_type", ""),
                    "post_date": self._parse_iso8601(item.get("timestamp")),
                    "engagement_count": int(item.get("like_count", 0)) + int(item.get("comments_count", 0)),
                    "likes": int(item.get("like_count", 0)),
                    "comments": int(item.get("comments_count", 0)),
                    "shares": int(item.get("shares", 0)),
                    "saves": 0,
                    "profile_visits": 0,
                })
            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching Instagram organic: {e}")
            return pd.DataFrame()

    def _fetch_facebook_organic(self) -> pd.DataFrame:
        """Fetch Facebook page organic content."""
        try:
            endpoint = f"/{self.facebook_page_id}/posts"
            params = {
                "fields": "id,message,story,created_time,likes.limit(0).summary(true),comments.limit(0).summary(true),shares",
            }
            response = self._make_request(endpoint, params)
            if not response or "data" not in response:
                return pd.DataFrame()

            records = []
            for item in response["data"]:
                records.append({
                    "id": item.get("id"),
                    "post_id": item.get("id"),
                    "message": item.get("message", ""),
                    "story": item.get("story", ""),
                    "post_date": self._parse_iso8601(item.get("created_time")),
                    "engagement_count": item.get("likes", {}).get("summary", {}).get("total_count", 0),
                    "likes": item.get("likes", {}).get("summary", {}).get("total_count", 0),
                    "comments": item.get("comments", {}).get("summary", {}).get("total_count", 0),
                    "shares": item.get("shares", 0),
                    "reactions": 0,
                    "page_fans": 0,
                })
            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching Facebook organic: {e}")
            return pd.DataFrame()

    def load_to_db(self, df: pd.DataFrame, table_name: str) -> int:
        """Load dataframe to database."""
        if df.empty:
            return 0

        try:
            return self.db.insert_dataframe(df, table_name, if_exists="append")
        except Exception as e:
            print(f"Error loading {table_name} to database: {e}")
            return 0

    def fetch_and_load_all(self) -> Dict[str, tuple]:
        """Fetch and load all Meta data sources."""
        results = {}

        start = time.time()
        ads_df = self._fetch_meta_ads_insights()
        inserted = self.load_to_db(ads_df, "meta_ads_performance")
        results["meta_ads"] = (len(ads_df), inserted)
        self.db.log_pipeline_execution("meta_ads", len(ads_df), inserted, "success", execution_time=time.time()-start)

        start = time.time()
        ig_df = self._fetch_instagram_organic()
        inserted = self.load_to_db(ig_df, "instagram_organic")
        results["instagram"] = (len(ig_df), inserted)
        self.db.log_pipeline_execution("instagram_organic", len(ig_df), inserted, "success", execution_time=time.time()-start)

        start = time.time()
        fb_df = self._fetch_facebook_organic()
        inserted = self.load_to_db(fb_df, "facebook_organic")
        results["facebook"] = (len(fb_df), inserted)
        self.db.log_pipeline_execution("facebook_organic", len(fb_df), inserted, "success", execution_time=time.time()-start)

        return results
