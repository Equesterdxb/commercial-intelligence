"""Collector for Equester simulator booking data."""

import os
import requests
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
from database.db import Database

_STATUS_MAP = {
    "CONFIRMED": "confirmed",
    "PENDING": "pending",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled",
    "NO_SHOW": "no_show",
}

_EXCLUDED_STATUSES = {"NEED_CONFIRMATION"}


class BookingCollector:
    def __init__(self):
        self.base_url = os.getenv("BOOKING_API_BASE_URL", "https://api.equester.ae")
        self.admin_email = os.getenv("BOOKING_ADMIN_EMAIL")
        self.admin_password = os.getenv("BOOKING_ADMIN_PASSWORD")
        self.db = Database()
        self.session = None
        self.auth_token = None

    def _post_with_retry(self, url: str, data: Dict, max_retries: int = 3) -> Optional[Dict]:
        """POST request with retry logic for non-JSON responses."""
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=data, timeout=10)
                response.raise_for_status()
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

    def _authenticate(self) -> bool:
        """Authenticate with booking API."""
        try:
            auth_url = f"{self.base_url}/admin/auth/sign-in/"
            auth_data = {
                "email": self.admin_email,
                "password": self.admin_password,
            }
            response = self._post_with_retry(auth_url, auth_data)
            if response and "token" in response:
                self.auth_token = response["token"]
                return True
            return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def _get_headers(self) -> Dict:
        """Get request headers with auth token."""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def _fetch_live(self) -> pd.DataFrame:
        """Fetch live booking data from API."""
        if not self._authenticate():
            return pd.DataFrame()

        try:
            url = f"{self.base_url}/bookings/"
            headers = self._get_headers()

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            bookings = data.get("bookings", [])
            if not bookings:
                return pd.DataFrame()

            records = []
            for booking in bookings:
                if booking.get("status") in _EXCLUDED_STATUSES:
                    continue

                guest_id_hash = self._hash_pii(booking.get("guest_id", ""))
                records.append({
                    "id": booking.get("id"),
                    "guest_name": booking.get("guest_name"),
                    "guest_email": booking.get("guest_email"),
                    "guest_phone": booking.get("guest_phone"),
                    "guest_id_hash": guest_id_hash,
                    "package_id": booking.get("package_id"),
                    "package_name": booking.get("package_name"),
                    "session_date": booking.get("session_date"),
                    "session_time": booking.get("session_time"),
                    "duration_minutes": booking.get("duration_minutes", 60),
                    "price_aed": booking.get("price_aed", 0),
                    "booking_source": booking.get("source", "app"),
                    "booking_status": _STATUS_MAP.get(booking.get("status", "PENDING"), "pending"),
                    "created_at": booking.get("created_at"),
                    "updated_at": booking.get("updated_at"),
                })

            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error fetching bookings: {e}")
            return pd.DataFrame()

    def _hash_pii(self, value: str) -> Optional[str]:
        """Hash PII values like guest IDs."""
        if not value:
            return None
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def load_to_db(self, df: pd.DataFrame) -> int:
        """Load dataframe to database."""
        if df.empty:
            return 0

        try:
            return self.db.insert_dataframe(df, "bookings", if_exists="append")
        except Exception as e:
            print(f"Error loading bookings to database: {e}")
            return 0

    def fetch_and_load(self) -> tuple:
        """Fetch and load booking data."""
        start_time = time.time()
        try:
            df = self._fetch_live()
            records_fetched = len(df)
            records_inserted = self.load_to_db(df)
            elapsed = time.time() - start_time

            self.db.log_pipeline_execution(
                "bookings",
                records_fetched,
                records_inserted,
                "success",
                execution_time=elapsed
            )
            return records_fetched, records_inserted
        except Exception as e:
            elapsed = time.time() - start_time
            self.db.log_pipeline_execution(
                "bookings",
                0,
                0,
                "failed",
                error=str(e),
                execution_time=elapsed
            )
            raise
