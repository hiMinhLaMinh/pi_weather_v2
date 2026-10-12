from datetime import datetime, timezone
import unittest
from unittest.mock import Mock, patch

from app import main, refresh
from weather import WeatherData


def reading(temperature=30, probability=71):
    return WeatherData(
        "Hanoi", temperature, 82, probability, datetime(2026, 10, 12, tzinfo=timezone.utc)
    )


class AppTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    @patch("app.WeatherDevices")
    def test_missing_key_does_not_initialize_hardware(self, device_type):
        with patch("builtins.print"):
            self.assertEqual(main([]), 1)
        device_type.assert_not_called()

    @patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test-key"})
    @patch("app.get_weather", side_effect=[reading(), reading(29, 70)])
    @patch("builtins.input", side_effect=["", "Hanoi,VN", "Da Nang,VN", "q"])
    @patch("app.WeatherDevices")
    def test_manual_mode_accepts_cities_and_ignores_empty_input(self, device_type, user_input, get):
        devices = device_type.return_value.__enter__.return_value
        devices.update.side_effect = [("thuận", 1, True), ("nghịch", 0.4, False)]
        with patch("builtins.print"):
            self.assertEqual(main([]), 0)
        self.assertEqual([call.args[0] for call in get.call_args_list], ["Hanoi,VN", "Da Nang,VN"])
        self.assertEqual([call.args for call in devices.update.call_args_list], [(30, 71), (29, 70)])
        device_type.return_value.__exit__.assert_called_once()

    @patch("app.get_weather", side_effect=ValueError("Mất mạng"))
    def test_api_error_stops_devices_and_reports_error(self, get):
        devices = Mock()
        with patch("builtins.print") as output:
            self.assertFalse(refresh("Hanoi,VN", "test-key", devices))
        devices.stop.assert_called_once()
        devices.update.assert_not_called()
        self.assertIn("Mất mạng", output.call_args_list[0].args[0])

    @patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test-key"})
    @patch("app.sleep", side_effect=[None, None, KeyboardInterrupt])
    @patch("app.get_weather", side_effect=[reading(), ValueError("Mất mạng"), reading(29, 0)])
    @patch("builtins.input", return_value="Hanoi,VN")
    @patch("app.WeatherDevices")
    def test_watch_retries_after_error_and_exits_on_ctrl_c(self, device_type, user_input, get, wait):
        devices = device_type.return_value.__enter__.return_value
        devices.update.side_effect = [("thuận", 1, True), ("nghịch", 0.4, False)]
        with patch("builtins.print"):
            self.assertEqual(main(["--watch", "--interval", "1"]), 0)
        self.assertEqual(get.call_count, 3)
        user_input.assert_called_once()
        devices.stop.assert_called_once()
        device_type.return_value.__exit__.assert_called_once()

    @patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test-key"})
    @patch("builtins.input", side_effect=EOFError)
    @patch("app.WeatherDevices")
    def test_end_of_input_releases_devices(self, device_type, user_input):
        with patch("builtins.print"):
            self.assertEqual(main([]), 0)
        device_type.return_value.__exit__.assert_called_once()

    @patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test-key"})
    @patch("builtins.input", return_value="q")
    @patch("app.WeatherDevices")
    def test_mock_mode_uses_pwm_capable_fake_gpio(self, device_type, user_input):
        from gpiozero.pins.mock import MockFactory, MockPWMPin

        with patch("builtins.print"):
            self.assertEqual(main(["--mock"]), 0)
        factory = device_type.call_args.kwargs["pin_factory"]
        self.assertIsInstance(factory, MockFactory)
        self.assertIsInstance(factory.pin(18), MockPWMPin)
        factory.close()

    def test_invalid_refresh_interval_is_rejected_before_gpio_setup(self):
        for interval in ("0", "-1", "abc"):
            with self.subTest(interval=interval):
                with patch("sys.stderr"), self.assertRaises(SystemExit) as caught:
                    main(["--watch", "--interval", interval])
                self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
