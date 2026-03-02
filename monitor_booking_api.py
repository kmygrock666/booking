from curl_cffi import requests
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
# [重要] 如果您在 GitHub Actions 遇到 403，請將資訊填入下方並將 STRICT_HARDCODE 設為 True
STRICT_HARDCODE = True # 設為 True 則完全忽略環境變數，強制使用下方填寫的值
HARDCODED_COOKIE = "" 
HARDCODED_USER_AGENT = ""
HARDCODED_FINGERPRINT = ""
HARDCODED_SESSION_ID = ""
# -------------------------------------------------------------------

def get_header_value(env_name, hardcoded_val, default=""):
    if STRICT_HARDCODE:
        return hardcoded_val or default
    return os.getenv(env_name) or hardcoded_val or default

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
}

class BookingMonitor:
    def __init__(self, bot_token, chat_id, cookie="", target_dates=None, user_agent=None, fingerprint=None, session_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cookie = cookie
        self.target_dates = target_dates or ["2026-03-11"]
        self.user_agent = user_agent
        self.fingerprint = fingerprint
        self.session_id = session_id
        self.debug_mode = False

    def log(self, message):
        print(f"[{datetime.now()}] {message}")

    def mask_string(self, s, visible=10):
        if not s or len(s) <= visible * 2:
            return "*****"
        return f"{s[:visible]}...{s[-visible:]}"

    def send_telegram_notification(self, message):
        self.log("Sending Telegram notification...")
        # Since we use curl_cffi for the main request, we can still use it here or stick to its requests
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            # Telegram API is usually fine with standard requests, but curl_cffi works too
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
            if self.user_agent:
                headers['user-agent'] = self.user_agent
            if self.fingerprint:
                headers['x-client-fingerprint'] = self.fingerprint
            if self.session_id:
                headers['x-client-session-id'] = self.session_id
            
            if self.debug_mode:
                self.log("DEBUG: Sent Headers (Masked):")
                debug_headers = {k: (self.mask_string(v) if k.lower() in ['cookie', 'user-agent', 'x-client-fingerprint', 'x-client-session-id'] else v) for k, v in headers.items()}
                print(json.dumps(debug_headers, indent=2))
            
            # Use impersonate="chrome" to bypass TLS fingerprinting blocks
            response = requests.get(API_URL, headers=headers, timeout=15, impersonate="chrome")
            
            if response.status_code == 403:
                error_msg = "<b>🚫 API Blocked (403)!</b>\nTLS 指紋偽裝失敗或 Cookie 已過期。\n來源: " + ("Hardcoded" if STRICT_HARDCODE else "Env/Hardcoded Mixed")
                self.log(error_msg.replace("<b>", "").replace("</b>", ""))
                self.send_telegram_notification(error_msg)
                return False
                
            response.raise_for_status()
            data = response.json()
            
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
                
        except Exception as e:
            # curl_cffi exceptions might be different, catching all for simplicity in monitoring
            error_msg = f"<b>❌ Error:</b>\n<code>{str(e)}</code>"
            self.log(error_msg.replace("<b>", "").replace("</b>", ""))
            # If it's a 403 or similar caught here
            if "403" in str(e):
                self.send_telegram_notification("<b>🚫 API Blocked (403)!</b>\n連線被拒絕，請檢查 Cookie 與 Headers。")
            else:
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
    
    # Use os.getenv because curl_cffi doesn't provide it, we use it for secrets
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    cookie = get_header_value("INLINE_COOKIE", HARDCODED_COOKIE)
    user_agent = get_header_value("USER_AGENT", HARDCODED_USER_AGENT)
    fingerprint = get_header_value("X_CLIENT_FINGERPRINT", HARDCODED_FINGERPRINT)
    session_id = get_header_value("X_CLIENT_SESSION_ID", HARDCODED_SESSION_ID)
    
    target_dates_str = args.dates or os.getenv("TARGET_DATES", "2026-03-11")
    target_dates = [d.strip() for d in target_dates_str.split(",") if d.strip()]
    
    monitor = BookingMonitor(bot_token, chat_id, cookie, target_dates, user_agent, fingerprint, session_id)
    monitor.debug_mode = args.debug
    
    if args.test_notify:
        monitor.send_telegram_notification("<b>🔔 Test Notification</b>\nCapacity monitor is active (impersonating Chrome).")
        return

    if args.heartbeat:
        monitor.send_telegram_notification("<b>💓 Heartbeat</b>\nCapacity monitor is running normally (impersonating Chrome).")
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
