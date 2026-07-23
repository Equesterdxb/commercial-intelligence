"""Weekly report generation for commercial intelligence."""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.analyzer import CommercialAnalyzer


class WeeklyReportGenerator:
    def __init__(self):
        self.analyzer = CommercialAnalyzer()
        self.report_date = datetime.now().strftime("%Y-%m-%d")

    def generate_html_report(self) -> str:
        """Generate HTML weekly report."""
        # Default values
        bookings = pd.DataFrame()
        sources = pd.DataFrame()
        ads = {"meta_ads": {}, "google_ads": {}}
        social = {"instagram": {}, "facebook": {}, "tiktok": {}}
        roi = {"total_ad_spend_aed": 0, "attributed_revenue_aed": 0, "roi": 0}

        try:
            bookings = self.analyzer.get_booking_trends(days=7) or pd.DataFrame()
            sources = self.analyzer.get_booking_sources() or pd.DataFrame()
            ads = self.analyzer.get_ad_performance(days=7) or ads
            social = self.analyzer.get_social_engagement() or social
            roi = self.analyzer.get_roi_summary(days=7) or roi
        except Exception:
            pass

        # Safe getters for optional data
        def safe_get(d, key, default=0):
            if not d:
                return default
            val = d.get(key, default)
            return val if val is not None else default

        num_bookings = len(bookings) if bookings is not None and not bookings.empty else 0
        meta_spend = safe_get(ads.get("meta_ads"), "spend", 0) if ads else 0
        google_spend = safe_get(ads.get("google_ads"), "spend", 0) if ads else 0
        ig_posts = safe_get(social.get("instagram"), "posts", 0) if social else 0
        fb_posts = safe_get(social.get("facebook"), "posts", 0) if social else 0
        tk_videos = safe_get(social.get("tiktok"), "videos", 0) if social else 0
        roi_pct = safe_get(roi, "roi", 0) if roi else 0

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Equester Commercial Intelligence Report - {self.report_date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; border-left: 4px solid #007bff; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Equester Commercial Intelligence Report</h1>
        <p>Generated: {self.report_date}</p>

        <h2>💰 Revenue & Bookings</h2>
        <div>
            <div class="metric">
                <div class="metric-value">{num_bookings}</div>
                <div class="metric-label">Bookings (7 days)</div>
            </div>
        </div>

        <h2>📢 Advertising Performance</h2>
        <div>
            <div class="metric">
                <div class="metric-value">AED {meta_spend:.2f}</div>
                <div class="metric-label">Meta Ad Spend</div>
            </div>
            <div class="metric">
                <div class="metric-value">AED {google_spend:.2f}</div>
                <div class="metric-label">Google Ad Spend</div>
            </div>
            <div class="metric">
                <div class="metric-value">{roi_pct:.1f}%</div>
                <div class="metric-label">ROI (7 days)</div>
            </div>
        </div>

        <h2>📱 Social Media Engagement</h2>
        <div>
            <div class="metric">
                <div class="metric-value">{ig_posts}</div>
                <div class="metric-label">Instagram Posts</div>
            </div>
            <div class="metric">
                <div class="metric-value">{fb_posts}</div>
                <div class="metric-label">Facebook Posts</div>
            </div>
            <div class="metric">
                <div class="metric-value">{tk_videos}</div>
                <div class="metric-label">TikTok Videos</div>
            </div>
        </div>

        <h2>Booking Sources</h2>"""

        if not sources.empty:
            html += """<table>
                <tr>
                    <th>Source</th>
                    <th>Bookings</th>
                    <th>Revenue (AED)</th>
                </tr>"""
            for _, row in sources.iterrows():
                source = row.get('booking_source', 'Unknown')
                count = row.get('count', 0)
                revenue = row.get('revenue_aed', 0)
                html += f"<tr><td>{source}</td><td>{count}</td><td>AED {revenue:.2f}</td></tr>"
            html += "</table>"
        else:
            html += "<p>No booking data available yet.</p>"

        html += """
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            This report was automatically generated by the Equester Commercial Intelligence Pipeline.
        </p>
    </div>
</body>
</html>
"""
        return html

    def save_report(self, filename: str = None) -> str:
        """Save report to file."""
        if filename is None:
            filename = f"report_{self.report_date}.html"

        report_dir = Path(__file__).parent
        filepath = report_dir / filename

        html_content = self.generate_html_report()
        with open(filepath, "w") as f:
            f.write(html_content)

        print(f"Report saved to {filepath}")
        return str(filepath)


if __name__ == "__main__":
    generator = WeeklyReportGenerator()
    generator.save_report()
