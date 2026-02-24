import json
import unittest
from unittest.mock import patch, MagicMock
import monitor_booking_api

class TestMonitor(unittest.TestCase):
    
    @patch('monitor_booking_api.requests.get')
    @patch('monitor_booking_api.send_telegram_notification')
    def test_status_change_detection(self, mock_notify, mock_get):
        # Mock API response with changed status
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "bookingPage": {
                "disabled": {
                    "caption": "SUCCESS!",
                    "message": "Booking is open!"
                }
            }
        }
        mock_get.return_value = mock_response
        
        # Run check
        result = monitor_booking_api.check_booking_status()
        
        # Verify
        self.assertTrue(result)
        mock_notify.assert_called_once()
        self.assertIn("SUCCESS!", mock_notify.call_args[0][0])

    @patch('monitor_booking_api.requests.get')
    @patch('monitor_booking_api.send_telegram_notification')
    def test_no_change_detection(self, mock_notify, mock_get):
        # Mock API response with default status
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "bookingPage": {
                "disabled": monitor_booking_api.DEFAULT_DISABLED_STATUS
            }
        }
        mock_get.return_value = mock_response
        
        # Run check
        result = monitor_booking_api.check_booking_status()
        
        # Verify
        self.assertFalse(result)
        mock_notify.assert_not_called()

    @patch('monitor_booking_api.requests.get')
    @patch('monitor_booking_api.send_telegram_notification')
    def test_error_notification(self, mock_notify, mock_get):
        # Mock API error
        mock_get.side_effect = Exception("Connection Timeout")
        
        # Run check
        result = monitor_booking_api.check_booking_status()
        
        # Verify
        self.assertFalse(result)
        mock_notify.assert_called_once()
        self.assertIn("Error checking status", mock_notify.call_args[0][0])
        self.assertIn("Connection Timeout", mock_notify.call_args[0][0])

    @patch('monitor_booking_api.send_telegram_notification')
    def test_heartbeat(self, mock_notify):
        # Run heartbeat logic from main
        with patch('sys.argv', ['monitor_booking_api.py', '--heartbeat']):
            monitor_booking_api.main()
        
        # Verify
        mock_notify.assert_called_once()
        self.assertIn("Heartbeat", mock_notify.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
