import json
import unittest
from unittest.mock import patch, MagicMock
from monitor_booking_api import BookingMonitor

class TestMonitor(unittest.TestCase):
    
    def setUp(self):
        self.monitor = BookingMonitor("fake_token", "fake_chat_id", "fake_cookie", ["2026-03-11", "2026-03-12"])

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('monitor_booking_api.requests.get')
    @patch('monitor_booking_api.BookingMonitor.send_telegram_notification')
    def test_multi_date_detection(self, mock_notify, mock_get, mock_log):
        # Mock Capacity API response with multiple open dates
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "default": {
                "2026-03-11": {"status": "open", "times": {"18:00": [], "19:00": []}},
                "2026-03-12": {"status": "open", "times": {"12:00": []}},
                "2026-03-13": {"status": "full"}
            }
        }
        mock_get.return_value = mock_response
        
        # Run check
        result = self.monitor.check_booking_status()
        
        # Verify
        self.assertTrue(result)
        mock_notify.assert_called_once()
        self.assertIn("TARGET DATES OPEN", mock_notify.call_args[0][0])
        self.assertIn("2026-03-11", mock_notify.call_args[0][0])
        self.assertIn("2026-03-12", mock_notify.call_args[0][0])

    @patch('monitor_booking_api.BookingMonitor.log')
    @patch('monitor_booking_api.requests.get')
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
    @patch('monitor_booking_api.requests.get')
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
