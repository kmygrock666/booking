from curl_cffi import requests
import html
import time
import json
import argparse
from datetime import datetime
from urllib.parse import quote
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration
COMPANY_ID = "-NeqTSgDQOAYi30lg4a7%3Ainline-live-3"
BRANCH_ID = "-OuaB8PT0YWMRAavQhfS"  # 島語-台中漢神洲際店 (舊: -OUYVD5L8af9l-fOxBi5)
API_URL = f"https://inline.app/api/booking-capacitiesV3?companyId={quote(COMPANY_ID, safe='')}&branchId={BRANCH_ID}"
BOOKING_URL = f"https://inline.app/booking/{COMPANY_ID}/{BRANCH_ID}"

# --- 這裡可直接貼上您的資訊 (也可透過 .env 或 GitHub Secrets 設定) ---
# [重要] 如果您在 GitHub Actions 遇到 403，請將資訊填入下方並將 STRICT_HARDCODE 設為 True
STRICT_HARDCODE = True # 設為 True 則完全忽略環境變數，強制使用下方填寫的值
HARDCODED_COOKIE = "_pxhd=2d4eab4365748ed1b4e9ff9bdac561a12fa2025ca6a8243a0e777bc3ba1b4a3a:cc3babde-768e-11f1-b569-6bb2d43e9ebc; _gcl_au=1.1.1433409852.1783049111; _ga=GA1.1.1374540555.1783049112; _fbp=fb.1.1783049111569.926599769444611741; _pxvid=cc3babde-768e-11f1-b569-6bb2d43e9ebc; _clck=1ccv9yu%5E2%5Eg7m%5E0%5E2375; mp_c153a2e7d8ab430d4f6087e52e535ee8_mixpanel=%7B%22distinct_id%22%3A%22%24device%3A501a0c71-8d09-481f-9725-f148ce54e6c4%22%2C%22%24device_id%22%3A%22501a0c71-8d09-481f-9725-f148ce54e6c4%22%2C%22%24initial_referrer%22%3A%22%24direct%22%2C%22%24initial_referring_domain%22%3A%22%24direct%22%2C%22__mps%22%3A%7B%7D%2C%22__mpso%22%3A%7B%22%24initial_referrer%22%3A%22%24direct%22%2C%22%24initial_referring_domain%22%3A%22%24direct%22%7D%2C%22__mpus%22%3A%7B%7D%2C%22__mpa%22%3A%7B%7D%2C%22__mpu%22%3A%7B%7D%2C%22__mpr%22%3A%5B%5D%2C%22__mpap%22%3A%5B%5D%7D; cf_clearance=6Y8SkRnfyawDAlslqu75GgzeeGXTnQKalA46uXNBzTs-1783695962-1.2.1.1-3aU7r1LZ6JVDQbouHgTEfuDdmwpUD8_j2B6yz0Wvek4G_YYGcndH0bQYRiF_o3swSqGbzRvCR4wvtSRSUyR02mRMluVoJ7xE_CJ1jwgRmcZofnRlhTniwbyYoL46z999JRbkcCpsQ.BwdrqSAt02sAH29hKXaEa4ZvEfHdfmHW_mirD5eWq_M..YUxU6or.kSzjSv5ttXfxn48Vg8JROcebH9O077NFZ59HWc0eTPVHLHjIlEpAtwiY9eikzfks8YkQJZY96qBSp0S_oX12WZTWpL_wyHgkb4lSLNZU7AfPrrOOOG48cIRrRfQ0RFEqVFWjufa1yxrBI.NMT6pmpsQ; _ga_6EKTQH8DYH=GS2.1.s1783695962$o8$g1$t1783695963$j59$l0$h0; _ga_NJJ9CTT701=GS2.1.s1783695962$o8$g1$t1783695963$j59$l0$h0; _ga_LQ2HBGK93X=GS2.1.s1783695962$o8$g1$t1783695963$j59$l0$h2070140270; _clsk=1phizwz%5E1783695963605%5E2%5E0%5Ej.clarity.ms%2Fcollect; _px3=03e88fcaf2341f08a95d3ef99844beda8b32c6bb23b60bf93e82284507f1b289:Q2oNx47wMjSTGgGa2fRbaDAGEUWRHA8WAjXken2WWahKtpmkKCfyymrEitIF9Asao4zLobUiytT0oH1UETJBXg==:1000:45DulcQo6MUyVpwRFW8JCsIVpo53y3SymLR9u2bICui1+57LAVM6/pkY56sD5jkHu53OLjqef7P/YH791WGfLcXTYxmIID0elO9F7YA1HIaVr5lIdzWaM/KdrD/izUt5lZVQbLiWxGEPGN1wui9wXEf+f3ivC7FixHAy1o9TzpTEFwAeAfpDt3udEkPIWyibsVqJrHQKMwFY/HVDUb+ZDZvz2qlaCcrvV4lUuv4H2hyabv3DrDujvbbYX9Ceflqth6o9lKIBi9v4N/Nuco5Pp/0I8zwOR3v5ZsoetF5FOp/0xntlOGUJxgNExncjBzC/MHZJOdVs7Ym7rQiDR4aitPPbSfNxr8lxj5yrfNgPs7TWw9IXidEsKGc9oSfdD+VtacxQ8OZ+IcWZ5h0AMeXfs/fLpyTbhsgItruY2OUCCT+2bIzvoKclF1y4M0hhyGrB4gvnzdwzuHpnz3PhkZJOWdEyfQLLNUxneUaviitJVpl1jF7AINiXjGJM6P2Jcx5gcD/J7Tf2Wv21nMQjmCRS9g==; pxcts=HXNRmaHvUAzGLNWKUGeBMyEDTf9xbLtry2rY30FSZ/g=:rUUrHdR1m67PfvoaAqs6Cv1JevWNi5cx7fh1j-2KqMi3fr-AYPPBkQV2R1hlW-Wxc4GHKM55zLkjh9f/Ie5AjVxza7zdKgqksZQ4ty8OVcd8I6D5YdDA1uZs/J3ABVjPlCzJGYteh1v8BoERZ2-E8OOrj7IfZj8dnhooh1/0vbz1ZAipq997SS08rXpUxJ-Q"
HARDCODED_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
HARDCODED_FINGERPRINT = "cbc33eeaf2599371bbe02b27aa3f9c6c"
HARDCODED_SESSION_ID = "97ac085d-0786-493f-8fcc-03b9d8ecef3b"
# -------------------------------------------------------------------

def get_header_value(env_name, hardcoded_val, default=""):
    if STRICT_HARDCODE:
        return hardcoded_val or default
    return os.getenv(env_name) or hardcoded_val or default

# 連續 403 達到此次數才視為真的被封鎖並通知；偶發的單次 403 (間歇性挑戰) 只記 log
BLOCK_NOTIFY_THRESHOLD = 3

# Advanced Headers for Bot Protection (from User's Curl)
DEFAULT_HEADERS = {
    'accept': '*/*',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
    'priority': 'u=1, i',
    'referer': BOOKING_URL,
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

class BookingMonitor:
    def __init__(self, bot_token, chat_id, cookie="", target_dates=None, user_agent=None, fingerprint=None, session_id=None, state_file=None, party_size=2):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cookie = cookie
        self.target_dates = target_dates or ["2026-08-15"]
        self.party_size = party_size  # 只在時段可訂這個人數時才通知
        self.user_agent = user_agent
        self.fingerprint = fingerprint
        self.session_id = session_id
        self.debug_mode = False
        self.state_file = state_file  # 用檔案保存狀態，讓 --once 模式 (如 GitHub Actions) 也能跨執行去重
        state = self._load_state()
        self.last_open_dates = state.get("open_dates")  # 上次檢查到的開放日期集合 (None 表示尚無狀態)
        self.notified_target_slots = state.get("target_slots") or {}  # 上次響鈴通知過的目標日期時段，內容沒變就不再響
        # 連續被擋 (403) 的次數，用於通知去重與退避；已通知過封鎖則直接從門檻起算，重啟後不再重發
        self.blocked_streak = BLOCK_NOTIFY_THRESHOLD if state.get("blocked_notified") else 0
        self.last_error = None  # 上次通知過的錯誤訊息，連續相同錯誤只通知一次

    def _load_state(self):
        if not self.state_file or not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file) as f:
                raw = json.load(f)
            state = {
                "target_slots": raw.get("target_slots") or {},
                "blocked_notified": raw.get("blocked_notified", False),
            }
            if "open_dates" in raw:
                state["open_dates"] = set(raw["open_dates"])
            return state
        except Exception as e:
            print(f"Warning: failed to load state file: {e}")
            return {}

    def _save_state(self):
        if not self.state_file:
            return
        try:
            with open(self.state_file, "w") as f:
                json.dump({
                    "open_dates": sorted(self.last_open_dates or []),
                    "target_slots": self.notified_target_slots,
                    "blocked_notified": self.blocked_streak >= BLOCK_NOTIFY_THRESHOLD,
                }, f)
        except Exception as e:
            print(f"Warning: failed to save state file: {e}")

    def log(self, message):
        print(f"[{datetime.now()}] {message}")

    def mask_string(self, s, visible=10):
        if not s or len(s) <= visible * 2:
            return "*****"
        return f"{s[:visible]}...{s[-visible:]}"

    def send_telegram_notification(self, message, silent=False):
        # silent=True 為靜音推送 (手機不響鈴不震動)，用於維運類訊息，讓響鈴專屬於真正的空位通知
        self.log(f"Sending Telegram notification{' (silent)' if silent else ''}...")
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_notification": silent,
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self.log("Notification sent successfully.")
        except Exception as e:
            self.log(f"Failed to send notification: {e}")

    def _build_headers(self):
        headers = DEFAULT_HEADERS.copy()
        sensitive = {
            'Cookie': self.cookie,
            'user-agent': self.user_agent,
            'x-client-fingerprint': self.fingerprint,
            'x-client-session-id': self.session_id,
        }
        headers.update({k: v for k, v in sensitive.items() if v})

        if self.debug_mode:
            self.log("DEBUG: Sent Headers (Masked):")
            sensitive_keys = {k.lower() for k in sensitive}
            debug_headers = {k: (self.mask_string(v) if k.lower() in sensitive_keys else v) for k, v in headers.items()}
            print(json.dumps(debug_headers, indent=2))
        return headers

    def _bookable_times(self, info):
        # times 的值是該時段可訂的人數列表，例如 {"12:00": [5, 6]} 表示只開放 5、6 位
        # 回傳可訂 party_size 位的時段清單；日期未開放或沒位子時回傳空清單
        if not isinstance(info, dict) or info.get("status") != "open":
            return []
        times = info.get("times") or {}
        return sorted(t for t, sizes in times.items() if self.party_size in (sizes or []))

    def check_booking_status(self):
        self.log(f"Checking booking status for dates: {', '.join(self.target_dates)}")
        try:
            # Use impersonate="chrome" to bypass TLS fingerprinting blocks
            response = requests.get(API_URL, headers=self._build_headers(), timeout=15, impersonate="chrome")
            
            if response.status_code == 403:
                if self.debug_mode:
                    self.log(f"DEBUG: 403 Body Snippet: {response.text[:500]}")
                self._handle_blocked()
                return False

            response.raise_for_status()
            if self.blocked_streak >= BLOCK_NOTIFY_THRESHOLD:
                # 只在真的通知過封鎖時才發解除訊息；偶發 403 恢復時保持安靜
                self.send_telegram_notification("<b>✅ 解除封鎖</b>\nAPI 已恢復正常存取。", silent=True)
            elif self.blocked_streak:
                self.log(f"Recovered after {self.blocked_streak} transient 403(s).")
            self.blocked_streak = 0
            self.last_error = None
            data = response.json()
            print(f"API Response Status: {response.status_code}")
            if self.debug_mode:
                self.log("DEBUG: Raw API Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # The API returns data nested under a 'default' key
            capacities = data.get("default", data)
            
            # 收集 API 回傳中所有開放、且有 party_size 位子的日期
            all_open_dates = [
                date_str for date_str in sorted(capacities)
                if self._bookable_times(capacities[date_str])
            ]

            target_slots = {}
            for target_date in self.target_dates:
                times_list = self._bookable_times(capacities.get(target_date))
                if times_list:
                    target_slots[target_date] = times_list
            available_days = [
                f"📅 <b>{d}</b>\nSlots ({self.party_size}位): {', '.join(t)}"
                for d, t in sorted(target_slots.items())
            ]

            open_set = set(all_open_dates)
            open_changed = self.last_open_dates is None or open_set != self.last_open_dates
            self.last_open_dates = open_set

            all_open_section = (
                f"<b>📋 所有可訂 {self.party_size} 位的日期:</b>\n" + "\n".join(f"• {d}" for d in all_open_dates)
                if all_open_dates else f"<b>📋 目前沒有可訂 {self.party_size} 位的日期</b>"
            )
            booking_link = f'<a href="{BOOKING_URL}">👉 Book Now</a>'

            if available_days:
                self.log(f"Found {len(available_days)} target open days! (all open: {len(all_open_dates)})")
                # 時段內容和上次響鈴通知相同就不再響，避免持續開放期間每輪都轟炸
                if target_slots != self.notified_target_slots:
                    msg = (
                        f"<b>🎯 TARGET DATES OPEN!</b>\n\n"
                        + "\n\n".join(available_days) + "\n\n"
                        + all_open_section + "\n\n"
                        + booking_link
                    )
                    self.send_telegram_notification(msg)
                else:
                    self.log("Target slots unchanged since last notification; skipping.")
                self.notified_target_slots = target_slots
                self._save_state()
                return True
            else:
                self.log(f"No target dates available. All open dates: {', '.join(all_open_dates) or 'none'}")
                # 開放日期清單有變化時才通知，避免重複轟炸
                if open_changed and all_open_dates:
                    self.send_telegram_notification(all_open_section + "\n\n" + booking_link)
                self.notified_target_slots = {}
                self._save_state()
                return False
                
        except Exception as e:
            self.log(f"Error: {e}")
            if "403" in str(e):
                self._handle_blocked()
            elif str(e) != self.last_error:
                # 連續相同錯誤只通知第一次；escape 例外內容，避免其中的 < / & 讓 Telegram HTML 解析失敗
                self.send_telegram_notification(f"<b>❌ Error:</b>\n<code>{html.escape(str(e))}</code>", silent=True)
                self.last_error = str(e)
            else:
                self.log("Same error as last notification; skipping.")
            return False

    def _handle_blocked(self):
        # 連續 403 達門檻才通知一次；偶發的間歇性 403 只記 log，避免「被擋/解除」成對刷屏
        self.blocked_streak += 1
        self._save_state()  # 持久化封鎖狀態，重啟後不重發通知
        self.log(f"🚫 API Blocked (403)! (連續第 {self.blocked_streak} 次)")
        if self.blocked_streak == BLOCK_NOTIFY_THRESHOLD:
            self.send_telegram_notification(
                "<b>🚫 API Blocked (403)!</b>\n連續多次被擋，身份可能過期，請重新抓取 Cookie。封鎖期間將自動退避並暫停重複通知。",
                silent=True,
            )

    def next_delay(self, base_interval):
        # 被擋時指數退避 (最長 30 分鐘)，降低持續觸發防護而延長封鎖的機率
        if not self.blocked_streak:
            return base_interval
        return min(base_interval * (2 ** self.blocked_streak), 1800)

def main():
    parser = argparse.ArgumentParser(description="Monitor Inline Capacity API for slot availability.")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification and exit.")
    parser.add_argument("--once", action="store_true", help="Run the check once and exit.")
    parser.add_argument("--heartbeat", action="store_true", help="Send a heartbeat message and exit.")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60).")
    parser.add_argument("--dates", type=str, help="Comma-separated target dates (overrides .env).")
    parser.add_argument("--party-size", type=int, default=int(os.getenv("PARTY_SIZE", "2")), help="Notify only when a slot can seat this many people (default: 2).")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to show raw API response.")
    parser.add_argument("--state-file", type=str, default=os.getenv("STATE_FILE") or ".booking_state.json", help="Path to a JSON file for persisting notification state across runs/restarts.")
    
    args = parser.parse_args()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    cookie = get_header_value("INLINE_COOKIE", HARDCODED_COOKIE)
    user_agent = get_header_value("USER_AGENT", HARDCODED_USER_AGENT)
    fingerprint = get_header_value("X_CLIENT_FINGERPRINT", HARDCODED_FINGERPRINT)
    session_id = get_header_value("X_CLIENT_SESSION_ID", HARDCODED_SESSION_ID)
    
    target_dates_str = args.dates or os.getenv("TARGET_DATES", "2026-08-15")
    target_dates = [d.strip() for d in target_dates_str.split(",") if d.strip()]
    
    monitor = BookingMonitor(bot_token, chat_id, cookie, target_dates, user_agent, fingerprint, session_id, state_file=args.state_file, party_size=args.party_size)
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
        delay = monitor.next_delay(args.interval)
        if delay != args.interval:
            monitor.log(f"被擋中，退避 {delay}s 後重試...")
        time.sleep(delay)

if __name__ == "__main__":
    main()
