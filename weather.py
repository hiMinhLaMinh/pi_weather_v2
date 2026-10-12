"""Lấy thời tiết hiện tại và dự báo bằng cùng API key của bài weather."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite

import requests


@dataclass(frozen=True)
class WeatherData:
    name: str
    temperature: float
    humidity: float
    rain_probability_percent: float
    forecast_time: datetime


def get_json(url, params):
    # Giữ cách gọi requests và timeout của bài weather.
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise ValueError("OpenWeather trả về dữ liệu JSON không hợp lệ.") from None
    except requests.RequestException as error:
        if error.response is not None and error.response.status_code == 401:
            raise ValueError(
                "API key OpenWeather không hợp lệ hoặc chưa được kích hoạt."
            ) from None
        raise ValueError("Không thể lấy dữ liệu từ OpenWeather.") from None


def get_weather(city, api_key):
    city = city.strip()
    if not city:
        raise ValueError("Vui lòng nhập tên thành phố.")

    locations = get_json(
        "https://api.openweathermap.org/geo/1.0/direct",
        {"q": city, "limit": 1, "appid": api_key},
    )
    if locations == []:
        raise ValueError("Không tìm thấy thành phố.")

    try:
        location = locations[0]
        name = location["name"]
        lat = float(location["lat"])
        lon = float(location["lon"])
        if not isinstance(name, str) or not name or not (
            -90 <= lat <= 90 and -180 <= lon <= 180
        ):
            raise ValueError
    except (KeyError, IndexError, TypeError, ValueError):
        raise ValueError("Dữ liệu thành phố từ OpenWeather không hợp lệ.") from None

    params = {"lat": lat, "lon": lon, "units": "metric", "appid": api_key}
    current = get_json("https://api.openweathermap.org/data/2.5/weather", params)
    forecast = get_json(
        "https://api.openweathermap.org/data/2.5/forecast",
        {**params, "cnt": 1},
    )

    try:
        temperature = float(current["main"]["temp"])
        humidity = float(current["main"]["humidity"])
        # pop là xác suất giáng thủy 0..1, không phải độ ẩm hay lượng mưa mm.
        next_forecast = forecast["list"][0]
        probability = float(next_forecast["pop"])
        city_timezone = timezone(timedelta(seconds=int(forecast["city"]["timezone"])))
        forecast_time = datetime.fromtimestamp(next_forecast["dt"], city_timezone)
        if not isfinite(temperature) or not (
            0 <= humidity <= 100 and 0 <= probability <= 1
        ):
            raise ValueError
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, OSError):
        raise ValueError("Dữ liệu thời tiết hoặc dự báo không hợp lệ.") from None

    return WeatherData(name, temperature, humidity, probability * 100, forecast_time)
