"""Nhập thành phố, xem thời tiết và điều khiển thiết bị theo yêu cầu bài 2."""

import argparse
import os
from time import sleep

import config
from hardware import WeatherDevices
from weather import get_weather


def positive_seconds(value):
    try:
        seconds = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Chu kỳ phải là số nguyên dương.") from None
    if seconds <= 0:
        raise argparse.ArgumentTypeError("Chu kỳ phải lớn hơn 0 giây.")
    return seconds


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mock", action="store_true", help="Mô phỏng GPIO; vẫn gọi API thời tiết thật."
    )
    parser.add_argument(
        "--watch", action="store_true", help="Tự cập nhật thành phố đã nhập; Ctrl+C để thoát."
    )
    parser.add_argument(
        "--interval",
        type=positive_seconds,
        default=config.UPDATE_INTERVAL_SECONDS,
        metavar="SECONDS",
        help="Chu kỳ cập nhật khi dùng --watch (mặc định: 300 giây).",
    )
    return parser.parse_args(argv)


def refresh(city, api_key, devices):
    try:
        data = get_weather(city, api_key)
    except ValueError as error:
        devices.stop()
        print(f"Lỗi: {error}")
        print("Động cơ dừng, LED tắt; chưa có dữ liệu hợp lệ để điều khiển.")
        return False

    direction, speed, light_on = devices.update(
        data.temperature, data.rain_probability_percent
    )
    print(f"{data.name}: {data.temperature:.1f} °C, độ ẩm {data.humidity:g}%")
    print(
        f"Xác suất mưa/giáng thủy: {data.rain_probability_percent:g}% "
        f"(kỳ dự báo 3 giờ gần nhất, lúc {data.forecast_time:%d/%m/%Y %H:%M %z})"
    )
    speed_name = "nhanh" if direction == "thuận" else "chậm"
    print(f"Động cơ DC quay {direction}, {speed_name} (PWM {speed:.0%})")
    print(
        f"LED {'bật' if light_on else 'tắt'} "
        f"(bật khi xác suất > {config.RAIN_THRESHOLD_PERCENT:g}%)"
    )
    print("-" * 30)
    return True


def main(argv=None):
    args = parse_args(argv)
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        print("Lỗi: Chưa đặt OPENWEATHER_API_KEY. Hãy nạp config.sh trước khi chạy.")
        return 1

    pin_factory = None
    if args.mock:
        from gpiozero.pins.mock import MockFactory, MockPWMPin

        pin_factory = MockFactory(pin_class=MockPWMPin)
        print("Chế độ mô phỏng GPIO; dữ liệu thời tiết được lấy từ API thật.")

    try:
        with WeatherDevices(pin_factory=pin_factory) as devices:
            while True:
                city = input("Nhập thành phố (hoặc nhập 'q' để thoát): ").strip()
                if city.lower() == "q":
                    break
                if not city:
                    print("Vui lòng nhập tên thành phố.")
                    continue

                success = refresh(city, api_key, devices)
                if args.watch and success:
                    print(f"Theo dõi {city} mỗi {args.interval} giây. Ctrl+C để thoát.")
                    while True:
                        sleep(args.interval)
                        refresh(city, api_key, devices)
    except (KeyboardInterrupt, EOFError):
        print("\nĐã dừng chương trình, tắt LED và động cơ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
