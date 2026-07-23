"""Tests for all data collectors."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, call
from collectors.booking_collector import BookingCollector
from collectors.meta_collector import MetaCollector
from collectors.google_ads_collector import GoogleAdsCollector
from collectors.tiktok_collector import TikTokCollector


class TestBookingCollector:
    @pytest.fixture
    def collector(self):
        return BookingCollector()

    def test_hash_pii(self, collector):
        """Test PII hashing."""
        hashed = collector._hash_pii("guest123")
        assert hashed is not None
        assert len(hashed) == 16
        assert hashed == collector._hash_pii("guest123")

    def test_hash_pii_none(self, collector):
        """Test hashing None."""
        assert collector._hash_pii(None) is None
        assert collector._hash_pii("") is None

    @patch('collectors.booking_collector.requests.post')
    def test_authenticate_success(self, mock_post, collector):
        """Test successful authentication."""
        mock_post.return_value.json.return_value = {"token": "test_token_123"}
        result = collector._authenticate()
        assert result is True
        assert collector.auth_token == "test_token_123"

    @patch('collectors.booking_collector.requests.post')
    def test_authenticate_failure(self, mock_post, collector):
        """Test failed authentication."""
        mock_post.return_value.json.return_value = {}
        result = collector._authenticate()
        assert result is False

    def test_load_to_db_empty_dataframe(self, collector):
        """Test loading empty dataframe."""
        df = pd.DataFrame()
        result = collector.load_to_db(df)
        assert result == 0

    def test_load_to_db_with_data(self, collector):
        """Test loading data."""
        df = pd.DataFrame({
            "id": ["1"],
            "guest_name": ["John"],
            "booking_source": ["app"],
            "booking_status": ["confirmed"],
        })
        with patch.object(collector.db, 'insert_dataframe', return_value=1):
            result = collector.load_to_db(df)
            assert result == 1

    @patch('collectors.booking_collector.requests.post')
    @patch('collectors.booking_collector.requests.get')
    def test_fetch_live_success(self, mock_get, mock_post, collector):
        """Test fetching live booking data."""
        mock_post.return_value.json.return_value = {"token": "test_token"}
        mock_get.return_value.json.return_value = {
            "bookings": [
                {
                    "id": "booking1",
                    "guest_name": "Alice",
                    "status": "CONFIRMED",
                    "source": "app",
                    "price_aed": 100,
                }
            ]
        }
        df = collector._fetch_live()
        assert len(df) == 1
        assert df.iloc[0]["booking_source"] == "app"


class TestMetaCollector:
    @pytest.fixture
    def collector(self):
        return MetaCollector()

    def test_parse_iso8601_with_offset(self, collector):
        """Test parsing ISO8601 with +0000 offset."""
        result = collector._parse_iso8601("2024-01-15T10:30:00+0000")
        assert result is not None
        assert "2024-01-15" in result

    def test_parse_iso8601_invalid(self, collector):
        """Test parsing invalid timestamp."""
        result = collector._parse_iso8601("invalid")
        assert result == "invalid"

    def test_parse_iso8601_none(self, collector):
        """Test parsing None."""
        result = collector._parse_iso8601(None)
        assert result is None

    def test_load_to_db_empty_dataframe(self, collector):
        """Test loading empty dataframe."""
        df = pd.DataFrame()
        result = collector.load_to_db(df, "meta_ads_performance")
        assert result == 0

    @patch('collectors.meta_collector.requests.get')
    def test_fetch_meta_ads_success(self, mock_get, collector):
        """Test fetching Meta Ads."""
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "campaign_id": "123",
                    "campaign_name": "Campaign A",
                    "adset_id": "456",
                    "adset_name": "Adset A",
                    "ad_id": "789",
                    "ad_name": "Ad A",
                    "date_start": "2024-01-15",
                    "impressions": "1000",
                    "clicks": "50",
                    "spend": "500",
                    "cpc": "10",
                    "cpm": "5",
                    "ctr": "5.0",
                    "reach": "800",
                }
            ]
        }
        df = collector._fetch_meta_ads_insights()
        assert len(df) == 1
        assert df.iloc[0]["campaign_id"] == "123"

    @patch('collectors.meta_collector.requests.get')
    def test_fetch_meta_ads_empty(self, mock_get, collector):
        """Test fetching Meta Ads with no data."""
        mock_get.return_value.json.return_value = {"data": []}
        df = collector._fetch_meta_ads_insights()
        assert len(df) == 0


class TestGoogleAdsCollector:
    @pytest.fixture
    def collector(self):
        return GoogleAdsCollector()

    @patch('collectors.google_ads_collector.requests.post')
    def test_refresh_token_success(self, mock_post, collector):
        """Test token refresh."""
        mock_post.return_value.json.return_value = {"access_token": "new_token"}
        result = collector._refresh_access_token()
        assert result is True
        assert collector.access_token == "new_token"

    def test_load_to_db_empty_dataframe(self, collector):
        """Test loading empty dataframe."""
        df = pd.DataFrame()
        result = collector.load_to_db(df)
        assert result == 0

    @patch('collectors.google_ads_collector.requests.post')
    @patch('collectors.google_ads_collector.requests.post')
    def test_fetch_live_no_token(self, mock_refresh, mock_post, collector):
        """Test fetch with failed token refresh."""
        mock_refresh.return_value = False
        df = collector._fetch_live()
        assert len(df) == 0


class TestTikTokCollector:
    @pytest.fixture
    def collector(self):
        return TikTokCollector()

    @patch('collectors.tiktok_collector.requests.post')
    def test_refresh_token_success(self, mock_post, collector):
        """Test TikTok token refresh."""
        mock_post.return_value.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
        }
        result = collector._refresh_access_token()
        assert result is True

    def test_load_to_db_empty_dataframe(self, collector):
        """Test loading empty dataframe."""
        df = pd.DataFrame()
        result = collector.load_to_db(df)
        assert result == 0

    @patch('collectors.tiktok_collector.requests.post')
    @patch('collectors.tiktok_collector.requests.get')
    def test_fetch_live_success(self, mock_get, mock_post, collector):
        """Test fetching TikTok data."""
        mock_post.return_value.json.return_value = {"access_token": "token"}
        mock_get.return_value.json.return_value = {
            "data": {
                "videos": [
                    {
                        "id": "video123",
                        "video_description": "Test video",
                        "create_time": 1234567890,
                        "view_count": 1000,
                        "like_count": 100,
                        "comment_count": 20,
                        "share_count": 5,
                        "download_count": 10,
                        "video_duration": 60,
                    }
                ]
            }
        }
        df = collector._fetch_live()
        assert len(df) == 1
        assert df.iloc[0]["view_count"] == 1000
