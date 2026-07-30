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
HARDCODED_COOKIE = "_pxhd=2d4eab4365748ed1b4e9ff9bdac561a12fa2025ca6a8243a0e777bc3ba1b4a3a:cc3babde-768e-11f1-b569-6bb2d43e9ebc; _ga=GA1.1.1374540555.1783049112; _fbp=fb.1.1783049111569.926599769444611741; _pxvid=cc3babde-768e-11f1-b569-6bb2d43e9ebc; _clck=1ccv9yu%5E2%5Eg7u%5E0%5E2375; cf_clearance=bj3QWMWgMOC_lWVto4XqlK9aIovTlQh6tC13Ks2JBW4-1784380521-1.2.1.1-9kIS4oxdOV489tLX_ROjUgzLJ1t2zlkITxcDCq5LUVzVPoK_cXOr7RTyLo1BA8evo1CrcsXF.DdvQ_YmkG.dY17SLxXFpdxOM0WROETm3zPOkHhHtOeFFCC1tx0VSRBypf1t9s9FDpNNL4kLFYGrkmXCUp3SrfetKxBo0IyMNDweCtRZYsr3RSTxSde7D3YKMyJA.29h.ZOAr7XttndrevHMJVG7FB.SuVB_TG.vXntEr9T3XuHzCIXpBoGZHSbfIKB9U2VEYHMBLIOnyOepMbpadLijfNGgUwXOKVHZHzTIHzNaglP9h8zWHC4DbkmxVC8KSbQjK9nqzSlQmfPJXA; _clsk=xnjlvi%5E1784380522651%5E2%5E1%5Ej.clarity.ms%2Fcollect; _px3=f52f1986faa88fe0020ad37b211a83c77c5f83e14c40c4655bc5e00844bf1b5f:JEDELZAkBnnxR8JtjoYY8jsJPUm+PbQvaQsXRmfkmlyj9IeWwIk+qJ9pubKzYHpTFle0r+Z/UWN6qXEGjJAPFg==:1000:Ml0srSeqfR0LMYgIUSAy2olTV8QmGQNkjEFJq4MHKtzDfaIznvShQ2Gu1RggMdZLTW/RAIpTzErqpzMLSYQZnUhqYnUU1WeaJEm7K2paE24CvwqlsxMS++XPrwUmT/7VYjveF9V7qa7TxiWjTsMaq3rCGtiPSLVE2qGw4+CCCt574AflZhO1HgzS6Mfylj1boxIeVhVIgcrw0SE2FtmGRIpSvHFMmOWM2pAFbZmjVGBZ6/tDTbpUxR/z/zsa+v8nIKRTrduAEQddUDMPkB18/KhCtUJP2SvnDz8hp034NxZOvNw/sIDwTSf6w6Ky71FQQlnBhUcsH9q04vHMXTY8SEH07QtXuHZNJ58wp1B3ccrWe0Zr1hWc2mHWqyL1adN+h6yCcOViY20nlI2rVV3S7lJxQQYOPOlVgFnTsg+E1/WJbfSWH7lVHejYsvGfh1iZ3j5b0OH3PeV0rUFW38os3V8F5UfH4ejnuEWNg7u7sSu00sF8AdZXeH6vE2xT5+Ch; mp_c153a2e7d8ab430d4f6087e52e535ee8_mixpanel=%7B%22distinct_id%22%3A%22%24device%3A501a0c71-8d09-481f-9725-f148ce54e6c4%22%2C%22%24device_id%22%3A%22501a0c71-8d09-481f-9725-f148ce54e6c4%22%2C%22%24initial_referrer%22%3A%22%24direct%22%2C%22%24initial_referring_domain%22%3A%22%24direct%22%2C%22__mps%22%3A%7B%7D%2C%22__mpso%22%3A%7B%22%24initial_referrer%22%3A%22%24direct%22%2C%22%24initial_referring_domain%22%3A%22%24direct%22%7D%2C%22__mpus%22%3A%7B%7D%2C%22__mpa%22%3A%7B%7D%2C%22__mpu%22%3A%7B%7D%2C%22__mpr%22%3A%5B%5D%2C%22__mpap%22%3A%5B%5D%7D; pxcts=g0If5HnOjNZ/va7TN1XK-kcLr255akqUcIZZgg3wYC0=:G7rI3GZtXmO0ZR5TSTQIvuyGVg7JHvAdPPS6-5EmXINPW33spUE9r7l9VS/aOQZgLRcv8jsSYbYiSOjMJA8HoEaGv/LYYGuDMu1l86FSMITeQxjU4ZrFX6-xapJpAXeGPj/7ifzn9Mjho7Jryz6-5fA1PPOVkaTcg/EaUOEEUPgPE-nhaJexT8LldYx0GTMB; _ga_6EKTQH8DYH=GS2.1.s1784380521$o15$g1$t1784380550$j31$l0$h0; _ga_NJJ9CTT701=GS2.1.s1784380521$o15$g1$t1784380550$j31$l0$h0; _ga_LQ2HBGK93X=GS2.1.s1784380521$o15$g1$t1784380550$j31$l0$h685808772; _gcl_au=1.1.1433409852.1783049111.-.-.1784304504.2131055413.1784304504.1784380550"
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
    def __init__(self, bot_token, chat_id, cookie="", target_dates=None, user_agent=None, fingerprint=None, session_id=None, state_file=None, party_size=2, latest_time=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cookie = cookie
        self.target_dates = target_dates or ["2026-10-09", "2026-10-10", "2026-10-11"]
        self.party_size = party_size  # 只在時段可訂這個人數時才通知
        self.latest_time = latest_time  # 只通知早於此時間的時段 (HH:MM，如 "15:00" 代表只要午餐)，None 表示不限
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
        # 時段字串為零填充 HH:MM，字典序即時間先後，可直接比較篩出午餐/晚餐
        return sorted(
            t for t, sizes in times.items()
            if self.party_size in (sizes or [])
            and (self.latest_time is None or t < self.latest_time)
        )

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
            # 附上快照時間並提醒：這是抓取當下的狀態，位子可能在你打開前就被搶走
            snapshot_note = f'⏱ 抓取時間 {datetime.now():%m-%d %H:%M:%S}（狀態為當下快照，位子可能已被搶，請儘速確認）'

            if available_days:
                self.log(f"Found {len(available_days)} target open days! (all open: {len(all_open_dates)})")
                # 時段內容和上次響鈴通知相同就不再響，避免持續開放期間每輪都轟炸
                if target_slots != self.notified_target_slots:
                    msg = (
                        f"<b>🎯 TARGET DATES OPEN!</b>\n\n"
                        + "\n\n".join(available_days) + "\n\n"
                        + all_open_section + "\n\n"
                        + booking_link + "\n\n"
                        + snapshot_note
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
                    self.send_telegram_notification(all_open_section + "\n\n" + booking_link + "\n\n" + snapshot_note)
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
    parser.add_argument("--party-size", type=int, default=int(os.getenv("PARTY_SIZE", "4")), help="Notify only when a slot can seat this many people (default: 4).")
    parser.add_argument("--latest-time", type=str, default=os.getenv("LATEST_TIME", "15:00"), help="Only notify for slots earlier than this HH:MM (default: 15:00 for lunch; set to 24:00 for all day).")
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
    
    target_dates_str = args.dates or os.getenv("TARGET_DATES", "2026-10-09,2026-10-10,2026-10-11")
    target_dates = [d.strip() for d in target_dates_str.split(",") if d.strip()]

    monitor = BookingMonitor(bot_token, chat_id, cookie, target_dates, user_agent, fingerprint, session_id, state_file=args.state_file, party_size=args.party_size, latest_time=args.latest_time)
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
