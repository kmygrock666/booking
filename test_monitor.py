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
