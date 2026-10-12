"""Điều khiển LED và một động cơ DC qua kênh A của L298N."""

from contextlib import ExitStack
from time import sleep

from gpiozero import LED, Motor, PWMOutputDevice

import config


def motor_settings(temperature):
    if temperature >= config.TEMP_THRESHOLD_C:
        return "forward", config.FAST_SPEED
    return "backward", config.SLOW_SPEED


def should_light_led(rain_probability_percent):
    # Đúng 70% vẫn tắt; đề bài yêu cầu TRÊN 70%.
    return rain_probability_percent > config.RAIN_THRESHOLD_PERCENT


class WeatherDevices:
    def __init__(self, pin_factory=None):
        self._stack = ExitStack()
        self._direction = None
        self._closed = False
        try:
            self.led = self._stack.enter_context(
                LED(config.LED_PIN, pin_factory=pin_factory)
            )
            self.motor = self._stack.enter_context(
                Motor(
                    forward=config.MOTOR_FORWARD_PIN,
                    backward=config.MOTOR_BACKWARD_PIN,
                    pwm=False,
                    pin_factory=pin_factory,
                )
            )
            self.enable = self._stack.enter_context(
                PWMOutputDevice(
                    config.MOTOR_ENABLE_PIN,
                    initial_value=0,
                    frequency=config.PWM_FREQUENCY_HZ,
                    pin_factory=pin_factory,
                )
            )
        except BaseException:
            self._stack.close()
            raise

    def update(self, temperature, rain_probability_percent):
        direction, speed = motor_settings(temperature)
        if self._direction is not None and self._direction != direction:
            # Ngắt ENA và dừng trước khi đổi chiều quay.
            self.enable.off()
            self.motor.stop()
            sleep(config.REVERSAL_PAUSE_SECONDS)

        if direction == "forward":
            self.motor.forward()
            direction_name = "thuận"
        else:
            self.motor.backward()
            direction_name = "nghịch"
        self.enable.value = speed
        self._direction = direction

        light_on = should_light_led(rain_probability_percent)
        if light_on:
            self.led.on()
        else:
            self.led.off()
        return direction_name, speed, light_on

    def stop(self):
        self.enable.off()
        self.motor.stop()
        self.led.off()
        self._direction = None

    def close(self):
        if not self._closed:
            try:
                self.stop()
            finally:
                self._stack.close()
                self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
