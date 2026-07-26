#!/usr/bin/env python3
"""Refresh OAuth credentials for collectors."""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

load_dotenv()

def refresh_google_ads_token():
    """Refresh Google Ads OAuth access token."""
    print("\n[Google Ads] Refreshing access token...")

    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("❌ Missing Google Ads credentials")
        return False

    try:
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        r = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=10)
        r.raise_for_status()

        access_token = r.json()["access_token"]
        print(f"✅ Google Ads token refreshed successfully")
        print(f"   New token: {access_token[:30]}...")
        return True
    except Exception as e:
        print(f"❌ Google Ads refresh failed: {e}")
        return False


def manual_meta_reminder():
    """Remind user to manually refresh Meta token."""
    print("\n[Meta] Manual refresh required")
    print("⚠️  Meta app tokens expire after 1-2 days and cannot be auto-refreshed.")
    print("\nTo refresh:")
    print("1. Go to: https://developers.facebook.com/tools/explorer")
    print("2. Select your 'Equester' app")
    print("3. Click 'Get App Token'")
    print("4. Copy the full token")
    print("5. Update .env: META_ACCESS_TOKEN=<token>")
    print("6. Run: git add .env && git commit && git push")
    print("\nNext refresh needed: " + datetime.now().isoformat())


if __name__ == "__main__":
    print("="*60)
    print("CREDENTIAL REFRESH")
    print("="*60)

    google_ok = refresh_google_ads_token()
    manual_meta_reminder()

    print("\n" + "="*60)
    if google_ok:
        print("✅ Google Ads: Refreshed")
    else:
        print("❌ Google Ads: Failed")
    print("⚠️  Meta: Manual refresh needed")
    print("="*60 + "\n")
