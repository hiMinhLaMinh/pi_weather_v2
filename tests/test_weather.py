import copy
import unittest
from unittest.mock import Mock, patch

import requests

from weather import get_weather


class WeatherTests(unittest.TestCase):
    def setUp(self):
        self.payloads = [
            [{"name": "Hanoi", "lat": 21.0, "lon": 105.8}],
            {"main": {"temp": 30, "humidity": 82}},
            {
                "list": [{"pop": 0.71, "dt": 1791781200}],
                "city": {"timezone": 25200},
            },
        ]

    def mock_responses(self, get, payloads=None):
        get.side_effect = [
            Mock(json=Mock(return_value=data))
            for data in (self.payloads if payloads is None else payloads)
        ]

    @patch("weather.requests.get")
    def test_reuses_key_and_coordinates_for_current_weather_and_forecast(self, get):
        self.mock_responses(get)
        data = get_weather(" Hanoi,VN ", "test-key")
        self.assertEqual(data.name, "Hanoi")
        self.assertEqual(data.temperature, 30)
        self.assertEqual(data.humidity, 82)
        self.assertEqual(data.rain_probability_percent, 71)
        self.assertEqual(data.forecast_time.utcoffset().total_seconds(), 25200)
        self.assertEqual(data.forecast_time.timestamp(), 1791781200)
        self.assertEqual(get.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in get.call_args_list],
            [
                "https://api.openweathermap.org/geo/1.0/direct",
                "https://api.openweathermap.org/data/2.5/weather",
                "https://api.openweathermap.org/data/2.5/forecast",
            ],
        )
        for call in get.call_args_list:
            self.assertEqual(call.kwargs["params"]["appid"], "test-key")
            self.assertEqual(call.kwargs["timeout"], 10)
        self.assertEqual(get.call_args_list[0].kwargs["params"]["q"], "Hanoi,VN")
        for call in get.call_args_list[1:]:
            self.assertEqual(call.kwargs["params"]["lat"], 21.0)
            self.assertEqual(call.kwargs["params"]["lon"], 105.8)
            self.assertEqual(call.kwargs["params"]["units"], "metric")
        self.assertEqual(get.call_args_list[2].kwargs["params"]["cnt"], 1)

    @patch("weather.requests.get")
    def test_empty_city_does_not_call_api(self, get):
        with self.assertRaisesRegex(ValueError, "nhập tên thành phố"):
            get_weather("   ", "test-key")
        get.assert_not_called()

    @patch("weather.requests.get")
    def test_unknown_city_does_not_fetch_weather(self, get):
        self.mock_responses(get, [[]])
        with self.assertRaisesRegex(ValueError, "Không tìm thấy thành phố"):
            get_weather("Unknown", "test-key")
        self.assertEqual(get.call_count, 1)

    @patch("weather.requests.get")
    def test_bad_geocoding_is_a_friendly_error(self, get):
        for location in (None, {}, [{}], [{"name": "X", "lat": 100, "lon": 1}]):
            with self.subTest(location=location):
                self.mock_responses(get, [location])
                with self.assertRaisesRegex(ValueError, "Dữ liệu thành phố"):
                    get_weather("X", "test-key")

    @patch("weather.requests.get")
    def test_unauthorized_error_does_not_reveal_key(self, get):
        response = Mock(status_code=401)
        response.raise_for_status.side_effect = requests.HTTPError(
            "401 URL containing secret-key", response=response
        )
        get.return_value = response
        with self.assertRaises(ValueError) as caught:
            get_weather("Hanoi,VN", "secret-key")
        self.assertIn("API key", str(caught.exception))
        self.assertNotIn("secret-key", str(caught.exception))

    @patch("weather.requests.get", side_effect=requests.Timeout("secret-key"))
    def test_timeout_does_not_reveal_key(self, get):
        with self.assertRaisesRegex(ValueError, "Không thể lấy dữ liệu") as caught:
            get_weather("Hanoi,VN", "secret-key")
        self.assertNotIn("secret-key", str(caught.exception))

    @patch("weather.requests.get")
    def test_invalid_json_is_a_friendly_error(self, get):
        get.return_value.json.side_effect = requests.exceptions.JSONDecodeError(
            "Invalid JSON", "not json", 0
        )
        with self.assertRaisesRegex(ValueError, "JSON không hợp lệ"):
            get_weather("Hanoi,VN", "test-key")

    @patch("weather.requests.get")
    def test_missing_forecast_is_not_treated_as_zero_probability(self, get):
        for forecast in (None, {}, {"list": []}, {"list": [{"dt": 1791781200}]}):
            with self.subTest(forecast=forecast):
                self.mock_responses(get, [*self.payloads[:2], forecast])
                with self.assertRaisesRegex(ValueError, "dự báo không hợp lệ"):
                    get_weather("Hanoi,VN", "test-key")

    @patch("weather.requests.get")
    def test_invalid_probability_is_rejected(self, get):
        for probability in (-0.1, 1.1, None, float("nan")):
            with self.subTest(probability=probability):
                payloads = copy.deepcopy(self.payloads)
                payloads[2]["list"][0]["pop"] = probability
                self.mock_responses(get, payloads)
                with self.assertRaisesRegex(ValueError, "dự báo không hợp lệ"):
                    get_weather("Hanoi,VN", "test-key")

    @patch("weather.requests.get")
    def test_invalid_temperature_and_humidity_are_rejected(self, get):
        for field, value in (
            ("temp", float("nan")),
            ("temp", float("inf")),
            ("humidity", -1),
            ("humidity", 101),
        ):
            with self.subTest(field=field, value=value):
                payloads = copy.deepcopy(self.payloads)
                payloads[1]["main"][field] = value
                self.mock_responses(get, payloads)
                with self.assertRaises(ValueError):
                    get_weather("Hanoi,VN", "test-key")


if __name__ == "__main__":
    unittest.main()
