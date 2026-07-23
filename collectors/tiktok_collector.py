"""Collector for TikTok organic content data."""

import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
from pathlib import Path
from typing import Dict, List, Optional
from database.db import Database


class TikTokCollector:
    def __init__(self):
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN")
        self.db = Database()
        self.access_token = None
        self.token_cache_file = ".tiktok_token_cache.json"
        self.base_url = "https://open.tiktokapis.com/v1"
        self._load_cached_token()

    def _load_cached_token(self):
        """Load cached access token if available."""
        try:
            if Path(self.token_cache_file).exists():
                with open(self.token_cache_file, "r") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token", self.refresh_token)
        except Exception:
            pass

    def _save_token_cache(self):
        """Save token to cache file."""
        try:
            with open(self.token_cache_file, "w") as f:
                json.dump({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                }, f)
        except Exception as e:
            print(f"Failed to cache token: {e}")

    def _refresh_access_token(self) -> bool:
        """Refresh OAuth access token."""
        try:
            url = "https://open.tiktokapis.com/v1/oauth/token/"
            data = {
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            self.access_token = result.get("access_token")
            if "refresh_token" in result:
                self.refresh_token = result.get("refresh_token")
            self._save_token_cache()
            return True
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    def _get_headers(self) -> Dict:
        """Get request headers with auth."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _fetch_live(self) -> pd.DataFrame:
        """Fetch TikTok organic content via Display API."""
        if not self._refresh_access_token():
            return pd.DataFrame()

        try:
            endpoint = f"{self.base_url}/video/list"
            headers = self._get_headers()
            params = {
                "fields": "id,create_time,video_description,like_count,comment_count,share_count,download_count,view_count,video_duration",
            }

            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("data", {}).get("videos"):
                return pd.DataFrame()

            records = []
            for video in data["data"]["videos"]:
                records.append({
                    "id": video.get("id"),
                    "video_id": video.get("id"),
                    "video_url": f"https://www.tiktok.com/@equester.ae/video/{video.get('id')}",
                    "description": video.get("video_description", ""),
                    "create_time": video.get("create_time"),
                    "view_count": int(video.get("view_count", 0)),
                    "like_count": int(video.get("like_count", 0)),
                    "comment_count": int(video.get("comment_count", 0)),
                    "share_count": int(video.get("share_count", 0)),
                    "download_count": int(video.get("download_count", 0)),
                    "video_duration_seconds": int(video.get("video_duration", 0)),
                    "hashtag_names": "",
                })

            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching TikTok data: {e}")
            return pd.DataFrame()

    def load_to_db(self, df: pd.DataFrame) -> int:
        """Load dataframe to database."""
        if df.empty:
            return 0

        try:
            return self.db.insert_dataframe(df, "tiktok_organic", if_exists="append")
        except Exception as e:
            print(f"Error loading TikTok to database: {e}")
            return 0

    def fetch_and_load(self) -> tuple:
        """Fetch and load TikTok data."""
        start_time = time.time()
        try:
            df = self._fetch_live()
            records_fetched = len(df)
            records_inserted = self.load_to_db(df)
            elapsed = time.time() - start_time

            self.db.log_pipeline_execution(
                "tiktok",
                records_fetched,
                records_inserted,
                "success",
                execution_time=elapsed
            )
            return records_fetched, records_inserted
        except Exception as e:
            elapsed = time.time() - start_time
            self.db.log_pipeline_execution(
                "tiktok",
                0,
                0,
                "failed",
                error=str(e),
                execution_time=elapsed
            )
            raise
