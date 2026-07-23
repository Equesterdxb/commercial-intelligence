-- Commercial Intelligence Database Schema for Equester

-- Bookings from simulator API
CREATE TABLE IF NOT EXISTS bookings (
  id TEXT PRIMARY KEY,
  guest_name TEXT,
  guest_email TEXT,
  guest_phone TEXT,
  guest_id_hash TEXT,
  package_id TEXT,
  package_name TEXT,
  session_date DATE,
  session_time TEXT,
  duration_minutes INTEGER,
  price_aed REAL,
  booking_source TEXT CHECK(booking_source IN ('app', 'website', 'walk_in', 'phone', 'instagram', 'meta_ads', 'google_ads', 'tiktok', 'partner_referral')),
  booking_status TEXT CHECK(booking_status IN ('confirmed', 'pending', 'completed', 'cancelled', 'no_show')),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meta Ads performance data
CREATE TABLE IF NOT EXISTS meta_ads_performance (
  id TEXT PRIMARY KEY,
  campaign_id TEXT,
  campaign_name TEXT,
  adset_id TEXT,
  adset_name TEXT,
  ad_id TEXT,
  ad_name TEXT,
  date DATE,
  impressions INTEGER,
  clicks INTEGER,
  spend_aed REAL,
  cpc_aed REAL,
  cpm_aed REAL,
  ctr REAL,
  reach INTEGER,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Instagram organic content (via Meta)
CREATE TABLE IF NOT EXISTS instagram_organic (
  id TEXT PRIMARY KEY,
  post_id TEXT,
  caption TEXT,
  media_type TEXT,
  post_date TIMESTAMP,
  engagement_count INTEGER,
  likes INTEGER,
  comments INTEGER,
  shares INTEGER,
  saves INTEGER,
  profile_visits INTEGER,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Facebook page organic content
CREATE TABLE IF NOT EXISTS facebook_organic (
  id TEXT PRIMARY KEY,
  post_id TEXT,
  message TEXT,
  story TEXT,
  post_date TIMESTAMP,
  engagement_count INTEGER,
  likes INTEGER,
  comments INTEGER,
  shares INTEGER,
  reactions INTEGER,
  page_fans INTEGER,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Google Ads campaign performance
CREATE TABLE IF NOT EXISTS google_ads_performance (
  id TEXT PRIMARY KEY,
  campaign_id TEXT,
  campaign_name TEXT,
  adgroup_id TEXT,
  adgroup_name TEXT,
  ad_id TEXT,
  ad_headline TEXT,
  date DATE,
  impressions INTEGER,
  clicks INTEGER,
  cost_aed REAL,
  avg_cpc_aed REAL,
  ctr REAL,
  conversions INTEGER,
  conversion_value_aed REAL,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Google Analytics 4 (website traffic)
CREATE TABLE IF NOT EXISTS ga4_website (
  id TEXT PRIMARY KEY,
  date DATE,
  users INTEGER,
  new_users INTEGER,
  sessions INTEGER,
  engagement_rate REAL,
  bounce_rate REAL,
  pageviews INTEGER,
  events INTEGER,
  goal_completions INTEGER,
  goal_conversion_rate REAL,
  revenue_aed REAL,
  user_acquisition_source TEXT,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TikTok organic content
CREATE TABLE IF NOT EXISTS tiktok_organic (
  id TEXT PRIMARY KEY,
  video_id TEXT,
  video_url TEXT,
  description TEXT,
  create_time TIMESTAMP,
  view_count INTEGER,
  like_count INTEGER,
  comment_count INTEGER,
  share_count INTEGER,
  download_count INTEGER,
  video_duration_seconds INTEGER,
  hashtag_names TEXT,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline execution log
CREATE TABLE IF NOT EXISTS pipeline_log (
  id TEXT PRIMARY KEY,
  execution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  source_name TEXT,
  records_fetched INTEGER,
  records_inserted INTEGER,
  records_updated INTEGER,
  status TEXT CHECK(status IN ('success', 'partial', 'failed')),
  error_message TEXT,
  execution_time_seconds REAL
);

-- Data quality metrics
CREATE TABLE IF NOT EXISTS data_quality (
  id TEXT PRIMARY KEY,
  check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  source_name TEXT,
  total_records INTEGER,
  null_count INTEGER,
  duplicate_count INTEGER,
  invalid_records INTEGER,
  quality_score REAL
);

CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(session_date);
CREATE INDEX IF NOT EXISTS idx_bookings_source ON bookings(booking_source);
CREATE INDEX IF NOT EXISTS idx_meta_ads_date ON meta_ads_performance(date);
CREATE INDEX IF NOT EXISTS idx_google_ads_date ON google_ads_performance(date);
CREATE INDEX IF NOT EXISTS idx_ga4_date ON ga4_website(date);
CREATE INDEX IF NOT EXISTS idx_pipeline_source ON pipeline_log(source_name);
