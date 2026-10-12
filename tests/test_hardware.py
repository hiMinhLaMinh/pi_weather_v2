import unittest
from unittest.mock import patch

from gpiozero import LED, Motor
from gpiozero.pins.mock import MockFactory, MockPWMPin

import config
from hardware import WeatherDevices


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.factory = MockFactory(pin_class=MockPWMPin)
        self.devices = WeatherDevices(pin_factory=self.factory)
        self.addCleanup(self.factory.close)
        self.addCleanup(self.devices.close)

    def test_temperature_at_or_above_30_runs_forward_at_full_speed(self):
        for temperature in (30, 30.1, 40):
            with self.subTest(temperature=temperature):
                self.devices.update(temperature, 0)
                self.assertEqual(self.factory.pin(config.MOTOR_FORWARD_PIN).state, 1)
                self.assertEqual(self.factory.pin(config.MOTOR_BACKWARD_PIN).state, 0)
                self.assertEqual(self.factory.pin(config.MOTOR_ENABLE_PIN).state, 1)

    def test_temperature_below_30_runs_backward_slowly(self):
        self.devices.update(29.9, 80)
        self.assertEqual(self.factory.pin(config.MOTOR_FORWARD_PIN).state, 0)
        self.assertEqual(self.factory.pin(config.MOTOR_BACKWARD_PIN).state, 1)
        self.assertEqual(self.factory.pin(config.MOTOR_ENABLE_PIN).state, 0.4)

    def test_led_is_on_only_above_70_percent(self):
        for probability, expected in ((0, 0), (69.9, 0), (70, 0), (70.1, 1), (100, 1)):
            with self.subTest(probability=probability):
                self.devices.update(30, probability)
                self.assertEqual(self.factory.pin(config.LED_PIN).state, expected)

    def test_temperature_and_led_rules_are_independent(self):
        self.devices.update(35, 80)
        self.assertEqual(self.devices.motor.value, 1)
        self.assertEqual(self.devices.led.value, 1)
        with patch("hardware.sleep"):
            self.devices.update(25, 20)
        self.assertEqual(self.devices.motor.value, -1)
        self.assertEqual(self.devices.enable.value, 0.4)
        self.assertEqual(self.devices.led.value, 0)

    def test_reversal_disables_power_and_stops_before_waiting(self):
        self.devices.update(31, 80)

        def check_stopped(seconds):
            self.assertEqual(seconds, config.REVERSAL_PAUSE_SECONDS)
            self.assertEqual(self.devices.enable.value, 0)
            self.assertEqual(self.devices.motor.value, 0)

        with patch("hardware.sleep", side_effect=check_stopped) as wait:
            self.devices.update(29, 80)
        wait.assert_called_once()
        self.assertEqual(self.devices.motor.value, -1)
        self.assertEqual(self.devices.enable.value, 0.4)

    def test_repeated_update_in_same_direction_does_not_pause(self):
        with patch("hardware.sleep") as wait:
            self.devices.update(31, 0)
            self.devices.update(32, 80)
        wait.assert_not_called()

    def test_stop_turns_all_outputs_off(self):
        self.devices.update(31, 80)
        self.devices.stop()
        for pin in (
            config.LED_PIN,
            config.MOTOR_FORWARD_PIN,
            config.MOTOR_BACKWARD_PIN,
            config.MOTOR_ENABLE_PIN,
        ):
            self.assertEqual(self.factory.pin(pin).state, 0)

    def test_exception_in_context_closes_every_device(self):
        with self.assertRaises(RuntimeError):
            with self.devices:
                self.devices.update(31, 80)
                raise RuntimeError("test")
        self.assertTrue(self.devices.led.closed)
        self.assertTrue(self.devices.motor.closed)
        self.assertTrue(self.devices.enable.closed)

    def test_partial_initialization_releases_allocated_gpio(self):
        self.devices.close()
        with patch("hardware.PWMOutputDevice", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                WeatherDevices(pin_factory=self.factory)
        # Nếu pin đã được giải phóng, có thể mở lại mà không gặp GPIOPinInUse.
        with LED(config.LED_PIN, pin_factory=self.factory):
            with Motor(
                config.MOTOR_FORWARD_PIN,
                config.MOTOR_BACKWARD_PIN,
                pwm=False,
                pin_factory=self.factory,
            ):
                pass


if __name__ == "__main__":
    unittest.main()
