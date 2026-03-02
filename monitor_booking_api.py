import requests
import time
import json
import argparse
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration
API_URL = "https://inline.app/api/booking-capacitiesV3?companyId=-NeqTSgDQOAYi30lg4a7%3Ainline-live-3&branchId=-OUYVD5L8af9l-fOxBi5"

# --- 這裡可直接貼上您的資訊 (也可透過 .env 或 GitHub Secrets 設定) ---
# 如果您不想使用環境變數，可以直接在下面的引號內填入您的值
HARDCODED_COOKIE = "" 
HARDCODED_USER_AGENT = ""
HARDCODED_FINGERPRINT = ""
HARDCODED_SESSION_ID = ""
# -------------------------------------------------------------------

# Advanced Headers for Bot Protection (from User's Curl)
DEFAULT_HEADERS = {
    'accept': '*/*',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'referer': 'https://inline.app/booking/-NeqTSgDQOAYi30lg4a7:inline-live-3/-OUYVD5L8af9l-fOxBi5',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': os.getenv("USER_AGENT") or HARDCODED_USER_AGENT or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'x-client-fingerprint': os.getenv("X_CLIENT_FINGERPRINT") or HARDCODED_FINGERPRINT or 'cbc33eeaf2599371bbe02b27aa3f9c6c',
    'x-client-session-id': os.getenv("X_CLIENT_SESSION_ID") or HARDCODED_SESSION_ID or '237ca41d-280b-4960-8954-bf627980c87f',
}

class BookingMonitor:
    def __init__(self, bot_token, chat_id, cookie="", target_dates=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cookie = cookie
        self.target_dates = target_dates or ["2026-03-11"]
        self.debug_mode = False

    def log(self, message):
        print(f"[{datetime.now()}] {message}")

    def send_telegram_notification(self, message):
        self.log("Sending Telegram notification...")
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self.log("Notification sent successfully.")
        except Exception as e:
            self.log(f"Failed to send notification: {e}")

    def check_booking_status(self):
        self.log(f"Checking booking status for dates: {', '.join(self.target_dates)}")
        try:
            headers = DEFAULT_HEADERS.copy()
            if self.cookie:
                headers['Cookie'] = self.cookie
                
            response = requests.get(API_URL, headers=headers, timeout=15)

            if response.status_code == 403:
                error_msg = "<b>🚫 API Blocked (403)!</b>\nYour cookie might have expired. Please update INLINE_COOKIE in your .env file."
                self.log(error_msg.replace("<b>", "").replace("</b>", ""))
                self.send_telegram_notification(error_msg)
                return False
                
            response.raise_for_status()
            data = response.json()
            print(data)
            if self.debug_mode:
                self.log("DEBUG: Raw API Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # The API returns data nested under a 'default' key
            capacities = data.get("default", data)
            
            available_days = []
            for target_date in self.target_dates:
                info = capacities.get(target_date)
                if info and info.get("status") == "open":
                    times_list = list(info.get("times", {}).keys())
                    times_str = ", ".join(times_list) if times_list else "All Times"
                    available_days.append(f"📅 <b>{target_date}</b>\nSlots: {times_str}")
            
            if available_days:
                msg = (
                    f"<b>🎯 TARGET DATES OPEN!</b>\n\n"
                    + "\n\n".join(available_days) + "\n\n"
                    f'<a href="https://inline.app/booking/-NeqTSgDQOAYi30lg4a7:inline-live-3/-OUYVD5L8af9l-fOxBi5">👉 Book Now</a>'
                )
                self.log(f"Found {len(available_days)} target open days!")
                self.send_telegram_notification(msg)
                return True
            else:
                self.log("No target dates available.")
                return False
                
        except requests.exceptions.Timeout:
            error_msg = "<b>⚠️ Timeout Error:</b>\nAPI request timed out. Retrying later..."
            self.log(error_msg.replace("<b>", "").replace("</b>", ""))
            return False
        except requests.exceptions.ConnectionError:
            error_msg = "<b>⚠️ Connection Error:</b>\nFailed to connect to Inline API."
            self.log(error_msg.replace("<b>", "").replace("</b>", ""))
            return False
        except Exception as e:
            error_msg = f"<b>❌ Unexpected Error:</b>\n<code>{str(e)}</code>"
            self.log(error_msg.replace("<b>", "").replace("</b>", ""))
            self.send_telegram_notification(error_msg)
            return False

def main():
    parser = argparse.ArgumentParser(description="Monitor Inline Capacity API for slot availability.")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification and exit.")
    parser.add_argument("--once", action="store_true", help="Run the check once and exit.")
    parser.add_argument("--heartbeat", action="store_true", help="Send a heartbeat message and exit.")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60).")
    parser.add_argument("--dates", type=str, help="Comma-separated target dates (overrides .env).")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to show raw API response.")
    
    args = parser.parse_args()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    cookie = os.getenv("INLINE_COOKIE") or HARDCODED_COOKIE
    
    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    target_dates_str = args.dates or os.getenv("TARGET_DATES", "2026-03-11")
    target_dates = [d.strip() for d in target_dates_str.split(",") if d.strip()]
    
    monitor = BookingMonitor(bot_token, chat_id, cookie, target_dates)
    monitor.debug_mode = args.debug
    
    if args.test_notify:
        monitor.send_telegram_notification("<b>🔔 Test Notification</b>\nCapacity monitor is active.")
        return

    if args.heartbeat:
        monitor.send_telegram_notification("<b>💓 Heartbeat</b>\nCapacity monitor is running normally.")
        return

    if args.once:
        monitor.check_booking_status()
        return

    monitor.log(f"Starting monitor with {args.interval}s interval...")
    while True:
        monitor.check_booking_status()
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
