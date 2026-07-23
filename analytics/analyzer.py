"""Analytics module for commercial intelligence insights."""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict
from database.db import Database


class CommercialAnalyzer:
    def __init__(self):
        self.db = Database()

    def get_booking_trends(self, days: int = 30) -> pd.DataFrame:
        """Get booking trends over time."""
        query = """
            SELECT DATE(session_date) as date, COUNT(*) as bookings, SUM(price_aed) as revenue_aed
            FROM bookings
            WHERE session_date >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(session_date)
            ORDER BY date DESC
        """
        return pd.read_sql_query(query, self.db.get_connection(), params=(days,))

    def get_booking_sources(self) -> pd.DataFrame:
        """Get booking distribution by source."""
        query = """
            SELECT booking_source, COUNT(*) as count, SUM(price_aed) as revenue_aed
            FROM bookings
            GROUP BY booking_source
            ORDER BY count DESC
        """
        return pd.read_sql_query(query, self.db.get_connection())

    def get_ad_performance(self, days: int = 30) -> Dict:
        """Get combined ad performance."""
        meta_query = """
            SELECT SUM(spend_aed) as spend, SUM(clicks) as clicks, SUM(impressions) as impressions
            FROM meta_ads_performance
            WHERE date >= datetime('now', '-' || ? || ' days')
        """
        google_query = """
            SELECT SUM(cost_aed) as spend, SUM(clicks) as clicks, SUM(impressions) as impressions
            FROM google_ads_performance
            WHERE date >= datetime('now', '-' || ? || ' days')
        """

        meta_df = pd.read_sql_query(meta_query, self.db.get_connection(), params=(days,))
        google_df = pd.read_sql_query(google_query, self.db.get_connection(), params=(days,))

        return {
            "meta_ads": meta_df.to_dict("records")[0] if not meta_df.empty else {},
            "google_ads": google_df.to_dict("records")[0] if not google_df.empty else {},
        }

    def get_social_engagement(self) -> Dict:
        """Get social media engagement metrics."""
        ig_query = """
            SELECT COUNT(*) as posts, SUM(engagement_count) as total_engagement, AVG(engagement_count) as avg_engagement
            FROM instagram_organic
        """
        fb_query = """
            SELECT COUNT(*) as posts, SUM(engagement_count) as total_engagement, AVG(engagement_count) as avg_engagement
            FROM facebook_organic
        """
        tk_query = """
            SELECT COUNT(*) as videos, SUM(view_count) as total_views, AVG(view_count) as avg_views
            FROM tiktok_organic
        """

        ig_df = pd.read_sql_query(ig_query, self.db.get_connection())
        fb_df = pd.read_sql_query(fb_query, self.db.get_connection())
        tk_df = pd.read_sql_query(tk_query, self.db.get_connection())

        return {
            "instagram": ig_df.to_dict("records")[0] if not ig_df.empty else {},
            "facebook": fb_df.to_dict("records")[0] if not fb_df.empty else {},
            "tiktok": tk_df.to_dict("records")[0] if not tk_df.empty else {},
        }

    def get_roi_summary(self, days: int = 30) -> Dict:
        """Calculate ROI from ads to bookings."""
        ad_spend_query = """
            SELECT COALESCE(SUM(spend_aed), 0) as total_spend FROM (
                SELECT SUM(spend_aed) as spend_aed FROM meta_ads_performance WHERE date >= datetime('now', '-' || ? || ' days')
                UNION ALL
                SELECT SUM(cost_aed) FROM google_ads_performance WHERE date >= datetime('now', '-' || ? || ' days')
            )
        """
        booking_revenue_query = """
            SELECT COALESCE(SUM(price_aed), 0) as total_revenue
            FROM bookings
            WHERE booking_source IN ('meta_ads', 'google_ads')
            AND session_date >= datetime('now', '-' || ? || ' days')
        """

        spend_df = pd.read_sql_query(ad_spend_query, self.db.get_connection(), params=(days, days))
        revenue_df = pd.read_sql_query(booking_revenue_query, self.db.get_connection(), params=(days,))

        total_spend = spend_df.iloc[0]["total_spend"] if not spend_df.empty else 0
        total_revenue = revenue_df.iloc[0]["total_revenue"] if not revenue_df.empty else 0

        return {
            "total_ad_spend_aed": total_spend,
            "attributed_revenue_aed": total_revenue,
            "roi": ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0,
        }
