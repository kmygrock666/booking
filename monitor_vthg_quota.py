from curl_cffi import requests
import html
import json
import time
import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
FORM_ID = "69ccda2890cd33cdce4aa50e"
API_URL = f"https://be.vthginbound.com/api/forms/quota/{FORM_ID}"
SITE_URL = "https://vthginbound.com/"

# 不帶 if-none-match，避免拿到 304 沒有 body
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
    'origin': 'https://vthginbound.com',
    'priority': 'u=1, i',
    'referer': 'https://vthginbound.com/',
    'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
}


class QuotaMonitor:
    def __init__(self, bot_token, chat_id, state_file=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.state_file = state_file  # 讓 --once 模式也能跨執行去重
        state = self._load_state()
        self.notified_open = state.get("notified_open", False)  # 已通知過名額開放，滿了之後才會重置再通知
        self.last_error = state.get("last_error")  # 連續相同錯誤只通知一次

    def _load_state(self):
        if not self.state_file or not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: failed to load state file: {e}")
            return {}

    def _save_state(self):
        if not self.state_file:
            return
        try:
            with open(self.state_file, "w") as f:
                json.dump({
                    "notified_open": self.notified_open,
                    "last_error": self.last_error,
                }, f)
        except Exception as e:
            print(f"Warning: failed to save state file: {e}")

    def log(self, message):
        print(f"[{datetime.now()}] {message}")

    def send_telegram_notification(self, message, silent=False):
        # silent=True 為靜音推送，維運類訊息不響鈴，讓響鈴專屬於名額開放通知
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

    def check(self):
        self.log("Checking quota...")
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=15, impersonate="chrome")
            response.raise_for_status()
            data = response.json()
            is_full = (data.get("data") or {}).get("isFull")
            self.log(f"isFull = {is_full}")

            if self.last_error:
                self.last_error = None
                self._save_state()

            if is_full is not True:
                if not self.notified_open:
                    snapshot_note = f"⏱ 抓取時間 {datetime.now():%m-%d %H:%M:%S}（狀態為當下快照，名額可能已被搶，請儘速確認）"
                    self.send_telegram_notification(
                        "<b>🎯 VTHG 名額開放了！(isFull ≠ true)</b>\n\n"
                        f"isFull = <code>{is_full}</code>\n\n"
                        f'<a href="{SITE_URL}">👉 立即前往報名</a>\n\n'
                        + snapshot_note
                    )
                    self.notified_open = True
                    self._save_state()
                else:
                    self.log("Already notified while open; skipping.")
                return True

            # 滿額時重置通知旗標，下次再開放才會重新響鈴
            if self.notified_open:
                self.notified_open = False
                self._save_state()
                self.log("Quota full again; notification re-armed.")
            return False

        except Exception as e:
            self.log(f"Error: {e}")
            if str(e) != self.last_error:
                self.send_telegram_notification(
                    f"<b>❌ VTHG Monitor Error:</b>\n<code>{html.escape(str(e))}</code>", silent=True
                )
                self.last_error = str(e)
                self._save_state()
            else:
                self.log("Same error as last notification; skipping.")
            return False


def main():
    parser = argparse.ArgumentParser(description="Monitor VTHG form quota; notify when isFull is not true.")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification and exit.")
    parser.add_argument("--once", action="store_true", help="Run the check once and exit.")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60).")
    parser.add_argument("--state-file", type=str, default=".vthg_quota_state.json", help="Path to a JSON file for persisting notification state across runs/restarts.")

    args = parser.parse_args()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    monitor = QuotaMonitor(bot_token, chat_id, state_file=args.state_file)

    if args.test_notify:
        monitor.send_telegram_notification("<b>🔔 Test Notification</b>\nVTHG quota monitor is active.")
        return

    if args.once:
        monitor.check()
        return

    monitor.log(f"Starting VTHG quota monitor with {args.interval}s interval...")
    while True:
        monitor.check()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
