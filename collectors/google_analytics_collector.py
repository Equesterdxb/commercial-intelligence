"""Collector for Google Analytics 4 website traffic data."""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
from pathlib import Path
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange,
)
from google.oauth2.service_account import Credentials
from database.db import Database


class GoogleAnalyticsCollector:
    def __init__(self):
        self.property_id = os.getenv("GA4_PROPERTY_ID")
        self.service_account_json_path = os.getenv("GA4_SERVICE_ACCOUNT_JSON_PATH", "credentials/ga4-service-account.json")
        self.db = Database()
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize GA4 Analytics Data API client."""
        try:
            if not Path(self.service_account_json_path).exists():
                print(f"Service account JSON not found at {self.service_account_json_path}")
                return None

            credentials = Credentials.from_service_account_file(self.service_account_json_path)
            scoped_credentials = credentials.with_scopes(
                ["https://www.googleapis.com/auth/analytics.readonly"]
            )
            return BetaAnalyticsDataClient(credentials=scoped_credentials)
        except Exception as e:
            print(f"Failed to initialize GA4 client: {e}")
            return None

    def _fetch_live(self) -> pd.DataFrame:
        """Fetch GA4 website traffic data."""
        if not self.client or not self.property_id:
            return pd.DataFrame()

        try:
            date_range = DateRange(
                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
            )

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[date_range],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionDefaultChannelGroup"),
                ],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="newUsers"),
                    Metric(name="sessions"),
                    Metric(name="engagementRate"),
                    Metric(name="bounceRate"),
                    Metric(name="screenPageViews"),
                    Metric(name="totalUsers"),
                ],
            )

            response = self.client.run_report(request)

            records = []
            for row in response.rows:
                records.append({
                    "id": f"{row.dimension_values[0].value}_{row.dimension_values[1].value}",
                    "date": row.dimension_values[0].value,
                    "users": int(row.metric_values[0].value or 0),
                    "new_users": int(row.metric_values[1].value or 0),
                    "sessions": int(row.metric_values[2].value or 0),
                    "engagement_rate": float(row.metric_values[3].value or 0),
                    "bounce_rate": float(row.metric_values[4].value or 0),
                    "pageviews": int(row.metric_values[5].value or 0),
                    "events": int(row.metric_values[5].value or 0),
                    "goal_completions": 0,
                    "goal_conversion_rate": 0.0,
                    "revenue_aed": 0.0,
                    "user_acquisition_source": row.dimension_values[1].value,
                })

            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching GA4 data: {e}")
            return pd.DataFrame()

    def load_to_db(self, df: pd.DataFrame) -> int:
        """Load dataframe to database."""
        if df.empty:
            return 0

        try:
            return self.db.insert_dataframe(df, "ga4_website", if_exists="append")
        except Exception as e:
            print(f"Error loading GA4 to database: {e}")
            return 0

    def fetch_and_load(self) -> tuple:
        """Fetch and load GA4 data."""
        start_time = time.time()
        try:
            df = self._fetch_live()
            records_fetched = len(df)
            records_inserted = self.load_to_db(df)
            elapsed = time.time() - start_time

            self.db.log_pipeline_execution(
                "ga4",
                records_fetched,
                records_inserted,
                "success",
                execution_time=elapsed
            )
            return records_fetched, records_inserted
        except Exception as e:
            elapsed = time.time() - start_time
            self.db.log_pipeline_execution(
                "ga4",
                0,
                0,
                "failed",
                error=str(e),
                execution_time=elapsed
            )
            raise
