"""Chân GPIO theo BCM và thông số điều khiển của bài weather_v2."""

LED_PIN = 17
MOTOR_FORWARD_PIN = 27  # IN1 của L298N
MOTOR_BACKWARD_PIN = 22  # IN2 của L298N
MOTOR_ENABLE_PIN = 18  # ENA của L298N; tháo jumper ENA trước khi nối

TEMP_THRESHOLD_C = 30.0
RAIN_THRESHOLD_PERCENT = 70.0
FAST_SPEED = 1.0  # PWM 100%
SLOW_SPEED = 0.4  # PWM 40%; có thể tăng nếu động cơ không khởi động được
PWM_FREQUENCY_HZ = 1000
REVERSAL_PAUSE_SECONDS = 0.2
UPDATE_INTERVAL_SECONDS = 300
