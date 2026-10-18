from curl_cffi import requests
import html
import json
import re
import time
import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration — 田馥甄 2026 台北小巨蛋，場次與區域由參數指定
EVENT_ID = "af2bd66d8fe65d78963cbb5bdc85771c"
DEFAULT_SESSION_ID = "5f56e43c4c02a92b92a701ad89f88784"  # 12/20 場次
# 區域名稱如 "特1區5200"，預設只監控 特1 ~ 特8
DEFAULT_AREA_REGEX = r"^特[1-8]區"
# 身障區需資格才能購買，預設排除
EXCLUDE_AREA_REGEX = r"身障"

S3_URL = "https://apis.ticketplus.com.tw/config/api/v1/getS3"
STATUS_URL = "https://apis.ticketplus.com.tw/config/api/v1/get"

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'origin': 'https://ticketplus.com.tw',
    'referer': 'https://ticketplus.com.tw/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
}


def get_json(url, params):
    response = requests.get(url, params=params, headers=HEADERS, timeout=15, impersonate="chrome")
    response.raise_for_status()
    data = response.json()
    if data.get("errCode") not in (None, "00"):
        raise RuntimeError(f"API error {data.get('errCode')}: {data.get('errMsg')} {data.get('errDetail')}")
    return data


def load_target_area_ids(session_id, area_regex):
    data = get_json(S3_URL, {"path": f"event/{EVENT_ID}/ticketAreas.json"})
    ids = [
        area["ticketAreaId"] for area in data["ticketAreas"]
        if area["sessionId"] == session_id
        and re.search(area_regex, area["name"])
        and not re.search(EXCLUDE_AREA_REGEX, area["name"])
    ]
    if not ids:
        raise RuntimeError(f"找不到符合 {area_regex} 的 ticketAreaId")
    return ids


def is_on_sale_now(area):
    try:
        start = datetime.fromisoformat(area["saleStart"])
        end = datetime.fromisoformat(area["saleEnd"])
    except (KeyError, TypeError, ValueError):
        return True  # 沒有販售時間資訊時只看 status
    now = datetime.now(start.tzinfo)
    return start <= now <= end


class TicketMonitor:
    def __init__(self, bot_token, chat_id, session_id, area_regex, label, state_file=None):
        self.session_id = session_id
        self.area_regex = area_regex
        self.label = label
        self.order_url = f"https://ticketplus.com.tw/order/{EVENT_ID}/{session_id}"
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.state_file = state_file
        state = self._load_state()
        self.notified_areas = set(state.get("notified_areas", []))  # 已通知有票的區域，回到 soldout 才重置
        self.sale_windows = state.get("sale_windows", {})  # 區域 -> "saleStart~saleEnd"，變動代表主辦重新開賣
        self.last_error = state.get("last_error")
        self.area_ids = None

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
                    "notified_areas": sorted(self.notified_areas),
                    "sale_windows": self.sale_windows,
                    "last_error": self.last_error,
                }, f, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: failed to save state file: {e}")

    def log(self, message):
        print(f"[{datetime.now()}] {message}", flush=True)

    def send_telegram_notification(self, message, silent=False):
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
        try:
            if self.area_ids is None:
                self.area_ids = load_target_area_ids(self.session_id, self.area_regex)
            data = get_json(STATUS_URL, {
                "ticketAreaId": ",".join(self.area_ids),
                "_": int(time.time() * 1000),
            })
            areas = sorted(data["result"]["ticketArea"], key=lambda a: a.get("sortedIndex", 0))
            self.log(" ".join(f"{a['ticketAreaName'].split('區')[0]}={a['status']}" for a in areas))

            if self.last_error:
                self.last_error = None
                self._save_state()

            available, rescheduled = [], []
            for area in areas:
                area_id = area["id"]
                window = f"{area.get('saleStart')}~{area.get('saleEnd')}"
                if area_id in self.sale_windows and self.sale_windows[area_id] != window:
                    rescheduled.append((area, window))
                self.sale_windows[area_id] = window

                if area["status"] != "soldout" and is_on_sale_now(area):
                    if area_id not in self.notified_areas:
                        available.append(area)
                        self.notified_areas.add(area_id)
                elif area_id in self.notified_areas:
                    self.notified_areas.discard(area_id)
                    self.log(f"{area['ticketAreaName']} sold out again; notification re-armed.")

            snapshot_note = f"⏱ 抓取時間 {datetime.now():%m-%d %H:%M:%S}（狀態為當下快照，票可能已被搶，請儘速確認）"
            if available:
                lines = "\n".join(
                    f"• {html.escape(a['ticketAreaName'])} — <code>{html.escape(a['status'])}</code>" for a in available
                )
                self.send_telegram_notification(
                    f"<b>🎫 {html.escape(self.label)} 有票釋出！</b>\n\n"
                    f"{lines}\n\n"
                    f'<a href="{self.order_url}">👉 立即前往購票</a>\n\n'
                    + snapshot_note
                )
            if rescheduled:
                lines = "\n".join(
                    f"• {html.escape(a['ticketAreaName'])}：<code>{html.escape(w)}</code>" for a, w in rescheduled
                )
                self.send_telegram_notification(
                    f"<b>📢 {html.escape(self.label)} 販售時間變更（可能要再釋票）</b>\n\n"
                    f"{lines}\n\n"
                    f'<a href="{self.order_url}">👉 購票頁</a>'
                )
            self._save_state()
            return bool(available)

        except Exception as e:
            self.log(f"Error: {e}")
            if str(e) != self.last_error:
                self.send_telegram_notification(
                    f"<b>❌ Ticketplus Monitor Error ({html.escape(self.label)}):</b>\n<code>{html.escape(str(e))}</code>", silent=True
                )
                self.last_error = str(e)
                self._save_state()
            else:
                self.log("Same error as last notification; skipping.")
            return False


def main():
    parser = argparse.ArgumentParser(description="Monitor Ticketplus 特1~特8 areas; notify when tickets are released.")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification and exit.")
    parser.add_argument("--once", action="store_true", help="Run the check once and exit.")
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds (default: 10).")
    parser.add_argument("--session-id", type=str, default=DEFAULT_SESSION_ID, help="Ticketplus sessionId (last segment of the order URL).")
    parser.add_argument("--area-regex", type=str, default=DEFAULT_AREA_REGEX, help="Regex on area name; use '.' for all areas.")
    parser.add_argument("--label", type=str, default="田馥甄 12/20 特1~特8", help="Name shown in notifications.")
    parser.add_argument("--state-file", type=str, default=".ticketplus_state.json", help="Path to a JSON file for persisting notification state across runs/restarts.")

    args = parser.parse_args()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        sys.exit(1)

    monitor = TicketMonitor(bot_token, chat_id, args.session_id, args.area_regex, args.label, state_file=args.state_file)

    if args.test_notify:
        monitor.send_telegram_notification(f"<b>🔔 Test Notification</b>\n{html.escape(args.label)} 監控已啟動。\n{monitor.order_url}")
        return

    if args.once:
        monitor.check()
        return

    monitor.log(f"Starting Ticketplus monitor [{args.label}] with {args.interval}s interval...")
    while True:
        monitor.check()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
