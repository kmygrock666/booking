import json
import unittest
from unittest.mock import patch, MagicMock
from monitor_booking_api import BookingMonitor

class TestMonitor(unittest.TestCase):
    
    def setUp(self):
        self.monitor = BookingMonitor("fake_token", "fake_chat_id", "fake_cookie", ["2026-03-11", "2026-03-12"])

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_multi_date_detection(self, mock_notify, mock_get, mock_log):
        # Mock Capacity API response with multiple open dates
        # times 的值是該時段可訂的人數列表，需包含 2 (兩位) 才通知
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "default": {
                "2026-03-11": {"status": "open", "times": {"18:00": [2, 4], "19:00": [5]}},
                "2026-03-12": {"status": "open", "times": {"12:00": [2]}},
                "2026-03-13": {"status": "full"}
            }
        }
        mock_get.return_value = mock_response

        # Run check
        result = self.monitor.check_booking_status()

        # Verify
        self.assertTrue(result)
        mock_notify.assert_called_once()
        msg = mock_notify.call_args[0][0]
        self.assertIn("TARGET DATES OPEN", msg)
        self.assertIn("2026-03-11", msg)
        self.assertIn("2026-03-12", msg)
        self.assertIn("18:00", msg)
        # 19:00 只剩 5 位，不應列出
        self.assertNotIn("19:00", msg)

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_open_but_no_seats_for_two(self, mock_notify, mock_get, mock_log):
        # 日期開放但所有時段都沒有 2 位的位子 -> 不通知
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "default": {
                "2026-03-11": {"status": "open", "times": {"11:30": [], "12:00": [5, 6]}},
            }
        }
        mock_get.return_value = mock_response

        result = self.monitor.check_booking_status()

        self.assertFalse(result)
        mock_notify.assert_not_called()

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_no_open_slots(self, mock_notify, mock_get, mock_log):
        # Mock Capacity API response with no open slots
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "default": {
                "2026-03-01": {"status": "full"},
                "2026-03-11": {"status": "booking-off"}
            }
        }
        mock_get.return_value = mock_response
        
        # Run check
        result = self.monitor.check_booking_status()
        
        # Verify
        self.assertFalse(result)
        mock_notify.assert_not_called()

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_403_blocking_notification(self, mock_notify, mock_get, mock_log):
        # Mock 403 Forbidden
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        # Run check
        result = self.monitor.check_booking_status()
        
        # Verify
        self.assertFalse(result)
        mock_notify.assert_called_once()
        self.assertIn("API Blocked", mock_notify.call_args[0][0])

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_target_notification_dedup(self, mock_notify, mock_get, mock_log):
        # 目標日期持續開放且時段不變 -> 只響一次；時段變化 -> 再通知
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "default": {"2026-03-11": {"status": "open", "times": {"18:00": [2]}}}
        }
        mock_get.return_value = mock_response

        self.assertTrue(self.monitor.check_booking_status())
        self.assertTrue(self.monitor.check_booking_status())
        self.assertEqual(mock_notify.call_count, 1)

        mock_response.json.return_value = {
            "default": {"2026-03-11": {"status": "open", "times": {"18:00": [2], "19:00": [2]}}}
        }
        self.assertTrue(self.monitor.check_booking_status())
        self.assertEqual(mock_notify.call_count, 2)

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_error_notification_dedup_and_silent(self, mock_notify, mock_get, mock_log):
        # 連續相同錯誤只通知一次，且為靜音推送
        mock_get.side_effect = RuntimeError("boom")

        self.assertFalse(self.monitor.check_booking_status())
        self.assertFalse(self.monitor.check_booking_status())

        mock_notify.assert_called_once()
        self.assertTrue(mock_notify.call_args.kwargs.get("silent"))

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('curl_cffi.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_blocked_notification_survives_restart(self, mock_notify, mock_get, mock_log):
        # 封鎖期間重啟 (新的 monitor 實例 + 同一狀態檔) 不應重發 403 通知
        import tempfile, os
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp:
            state_file = os.path.join(tmp, "state.json")
            m1 = BookingMonitor("t", "c", state_file=state_file)
            m1.check_booking_status()
            mock_notify.assert_called_once()  # 第一次封鎖：通知

            m2 = BookingMonitor("t", "c", state_file=state_file)  # 模擬重啟
            m2.check_booking_status()
            mock_notify.assert_called_once()  # 重啟後仍被擋：不重發

    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_heartbeat(self, mock_notify):
        # Run heartbeat logic from main
        import monitor_booking_api
        with patch('sys.argv', ['monitor_booking_api.py', '--heartbeat']), \
             patch('os.getenv', side_effect=lambda k, default=None: "fake_val" if k in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"] else default):
            monitor_booking_api.main()
        
        # Verify
        mock_notify.assert_called_once()
        self.assertIn("Heartbeat", mock_notify.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
