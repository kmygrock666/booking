import requests
import time
import json
import argparse
from datetime import datetime

import os

# Configuration
API_URL = "https://storage.inline.app/i18n/zh/-NeqTSgDQOAYi30lg4a7:inline-live-3-OUYVD5L8af9l-fOxBi5.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables must be set.")
    exit(1)

# Default "disabled" status content
DEFAULT_DISABLED_STATUS = {
    "caption": "抱歉！目前未開放預約，或線上訂位已額滿",
    "message": "如有任何問題，請透過島語Facebook粉絲專頁聯繫"
}

def send_telegram_notification(message):
    print(f"[{datetime.now()}] Sending Telegram notification...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"[{datetime.now()}] Notification sent successfully.")
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send notification: {e}")

def check_booking_status():
    print(f"[{datetime.now()}] Checking booking status...")
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        booking_page = data.get("bookingPage", {})
        disabled_status = booking_page.get("disabled", {})
        
        # Check if the content is different from the default
        if disabled_status != DEFAULT_DISABLED_STATUS:
            msg = (
                f"<b>🚨 Booking Status Changed!</b>\n\n"
                f"Current status:\n{json.dumps(disabled_status, indent=2, ensure_ascii=False)}\n\n"
                f"API URL: {API_URL}"
            )
            print(f"[{datetime.now()}] Status change detected!")
            send_telegram_notification(msg)
            return True
        else:
            print(f"[{datetime.now()}] No change detected. (Status: Disabled/Full)")
            return False
            
    except Exception as e:
        error_msg = f"<b>❌ Error checking status:</b>\n<code>{str(e)}</code>"
        print(f"[{datetime.now()}] {error_msg}")
        send_telegram_notification(error_msg)
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitor Inline Booking API for availability changes.")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification and exit.")
    parser.add_argument("--once", action="store_true", help="Run the check once and exit.")
    parser.add_argument("--heartbeat", action="store_true", help="Send a heartbeat message and exit.")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds (default: 5).")
    
    args = parser.parse_args()
    
    if args.test_notify:
        send_telegram_notification("<b>🔔 Test Notification</b>\nBooking monitor is active.")
        return

    if args.heartbeat:
        send_telegram_notification("<b>💓 Heartbeat</b>\nBooking monitor is running normally.")
        return

    if args.once:
        check_booking_status()
        return

    print(f"[{datetime.now()}] Starting monitor with {args.interval}s interval...")
    while True:
        check_booking_status()
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
