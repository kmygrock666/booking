# 訂位監控器 (Booking Monitor)

自動化爬蟲，用於監控 Inline 上的訂位可用性。

![監控狀態](https://github.com/ian-yu/booking/actions/workflows/monitor.yml/badge.svg)

## 功能特點
- 每 5 秒檢查一次 API，偵測可用性變動。
- 當可用性改變或發生錯誤時，發送 Telegram 通知。
- 每日發送「心跳 (Heartbeat)」訊息，確認系統正常執行中。

## 本地使用方法
```bash
# 發送測試通知
python3 monitor_booking_api.py --test-notify

# 執行單次檢查
python3 monitor_booking_api.py --once

# 執行心跳檢查
python3 monitor_booking_api.py --heartbeat
```
