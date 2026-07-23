# Equester Commercial Intelligence Pipeline

A comprehensive data collection and analytics pipeline for the Equester Horse Riding Simulator business. Integrates live data from 6 sources: bookings, Meta Ads, Google Ads, Google Analytics 4, TikTok, and social media platforms.

## Features

- ✅ **Live API Integration** — Real-time data from 6 sources
- ✅ **SQLite Database** — Local data warehouse with normalized schema
- ✅ **Retry Logic** — Robust error handling and automatic retries
- ✅ **PII Protection** — Hashing and anonymization of sensitive data
- ✅ **Comprehensive Testing** — 76 unit and integration tests
- ✅ **Weekly Reports** — Automated HTML report generation
- ✅ **Analytics Dashboard** — ROI, booking trends, social engagement metrics

## Data Sources

| Source | Type | Data | Status |
|--------|------|------|--------|
| **Bookings** | API | Session bookings, revenue, sources | ✅ Live |
| **Meta Ads** | API | Ad spend, impressions, clicks | ✅ Live |
| **Google Ads** | API | Campaign performance, conversions | ✅ Live |
| **GA4** | API | Website traffic, user behavior | ✅ Live |
| **TikTok** | API | Video performance, engagement | ✅ Live |
| **Social (FB/IG)** | API | Organic posts, engagement metrics | ✅ Live |

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and populate with your credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Add Google Cloud Service Account

Download your GA4 service account JSON from Google Cloud Console and save it:

```
credentials/ga4-service-account.json
```

### 4. Run the Pipeline

```bash
python -m collectors.orchestrator
```

## Project Structure

```
commercial-intelligence/
├── config/
│   └── data-sources.yaml          # Source configuration
├── collectors/
│   ├── booking_collector.py       # Equester API
│   ├── meta_collector.py          # Meta Ads + Facebook/Instagram
│   ├── google_ads_collector.py    # Google Ads
│   ├── google_analytics_collector.py  # GA4
│   ├── tiktok_collector.py        # TikTok
│   └── orchestrator.py            # Pipeline orchestration
├── database/
│   ├── schema.sql                 # SQLite schema
│   └── db.py                      # Database management
├── analytics/
│   └── analyzer.py                # Analytics queries
├── reports/
│   └── report_generator.py        # Weekly report generation
├── tests/
│   ├── test_collectors.py         # Collector tests
│   └── test_database.py           # Database tests
├── .env                           # Credentials (gitignored)
├── .env.example                   # Credentials template
└── requirements.txt               # Python dependencies
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=collectors --cov=database --cov=analytics

# Run specific test file
pytest tests/test_collectors.py -v
```

## Database Schema

The SQLite database includes normalized tables for:

- **bookings** — Session reservations with booking source tracking
- **meta_ads_performance** — Ads spend and engagement
- **instagram_organic** — Instagram posts and engagement
- **facebook_organic** — Facebook page posts and engagement
- **google_ads_performance** — Campaign metrics
- **ga4_website** — Website traffic data
- **tiktok_organic** — Video performance
- **pipeline_log** — Execution history and errors

All tables include `fetched_at` timestamps and CHECK constraints for data validation.

## Credential Management

Credentials are stored in `.env` (gitignored) with a template at `.env.example`.

**Important:**
- Never commit `.env` to git
- Keep credentials secure
- Rotate tokens regularly
- Use environment-specific values for prod/staging

## Authentication Details

### Equester Booking API
- Base URL: `https://api.equester.ae`
- Auth: Email/password → Bearer token
- Endpoint: `/admin/auth/sign-in/`

### Meta Graph API
- System User token with Insights permissions
- Covers both Ad Insights API and Instagram Business API

### Google Ads
- OAuth 2.0 with refresh token
- REST API (v23) with GAQL queries
- Manager account for multi-account access

### Google Analytics 4
- Service account JSON authentication
- Data API for historical analytics

### TikTok Display API
- OAuth consent flow
- Refresh token with rotating cache

## Weekly Report

Generate automated weekly reports:

```bash
python reports/report_generator.py
```

Reports include:
- Booking trends
- Ad performance and ROI
- Social media engagement
- Revenue attribution

## Troubleshooting

**Empty data returned?**
- Check credentials in `.env`
- Verify date ranges in collector queries
- Check pipeline logs for specific errors

**API errors?**
- Token may have expired — refresh via collector
- Rate limits — check API quotas
- Network issues — retry logic will handle

**Database issues?**
- Delete `equester_commercial.db` to reinitialize schema
- Check database file permissions
- Verify SQLite installation

## Performance

- Typical full pipeline: 5-10 seconds
- Data retention: 365 days by default
- Recommended frequency: Daily or hourly

## API Rate Limits

- Meta Graph API: 600 calls/10 min
- Google Ads: 10,000 requests/day
- Google Analytics 4: 10M events/month
- TikTok Display API: 500 calls/min

## Future Enhancements

- Real-time Kafka streaming
- Predictive analytics
- Custom dashboard UI
- Email report delivery
- Slack integration
- Data quality monitoring

## License

Proprietary — Equester
