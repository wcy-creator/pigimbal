"""
Servo control: PWM (SG90) + UART (CLB-S25) + Emulator (demo).
"""
import time
import math
import json
import os


class ServoBase:
    """Base class for all servo types."""

    def __init__(self, min_angle=-90, max_angle=90, home=0):
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.angle = home
        self.home = home

    def _clamp(self, angle):
        return max(self.min_angle, min(self.max_angle, angle))

    def move_to(self, angle):
        raise NotImplementedError

    def query(self):
        return self.angle

    def center(self):
        self.move_to(self.home)

    def close(self):
        pass


class ServoPWM(ServoBase):
    """
    PWM servo via RPi.GPIO (SG90, MG90S, etc).

    Usage:
        servo = ServoPWM(pin=18)
        servo.move_to(45)   # 45 degrees
        servo.center()
    """

    def __init__(self, pin=18, min_angle=-90, max_angle=90, home=0,
                 min_pulse=500, max_pulse=2500):
        super().__init__(min_angle, max_angle, home)
        self.pin = pin
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self._gpio = None
        self._setup()

    def _setup(self):
        try:
            import RPi.GPIO as GPIO
            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            self._pwm = GPIO.PWM(self.pin, 50)  # 50Hz
            self._pwm.start(0)
        except (ImportError, RuntimeError):
            print("[ServoPWM] RPi.GPIO not available, using emulator")
            self.__class__ = ServoEmulator

    def _angle_to_duty(self, angle):
        angle = self._clamp(angle)
        us = self.min_pulse + (self.max_pulse - self.min_pulse) * (angle - self.min_angle) / (self.max_angle - self.min_angle)
        return (us / 20000) * 100  # 50Hz = 20ms period

    def move_to(self, angle):
        angle = self._clamp(angle)
        if self._gpio:
            self._pwm.ChangeDutyCycle(self._angle_to_duty(angle))
            time.sleep(0.3)
            self._pwm.ChangeDutyCycle(0)
        self.angle = angle

    def close(self):
        if hasattr(self, '_pwm'):
            self._pwm.stop()
        if self._gpio:
            self._gpio.cleanup(self.pin)


class ServoUART(ServoBase):
    """
    UART bus servo (FashionStar CLB-S25, etc).

    Usage:
        servo = ServoUART(port='/dev/ttyUSB0', servo_id=0)
        servo.move_to(30)
        print(servo.query())
    """

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, servo_id=0,
                 min_angle=-135, max_angle=135, home=0):
        super().__init__(min_angle, max_angle, home)
        self.port = port
        self.baudrate = baudrate
        self.servo_id = servo_id
        self._ser = None
        self._setup()

    def _setup(self):
        try:
            import serial
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(0.1)
        except Exception as e:
            print("[ServoUART] Cannot open %s: %s" % (self.port, e))

    def _send(self, cmd_id, params=b''):
        if not self._ser:
            return None
        data = bytes([0x55, 0x55, len(params) + 3, cmd_id]) + params
        self._ser.write(data)
        time.sleep(0.01)
        return self._ser.read(20) if self._ser.in_waiting else None

    def move_to(self, angle):
        angle = self._clamp(angle)
        pos = int((angle + 135) / 270 * 1000)
        pos = max(0, min(1000, pos))
        params = bytes([self.servo_id]) + pos.to_bytes(2, 'little')
        self._send(0x01, params)
        self.angle = angle
        time.sleep(0.05)

    def nudge(self, delta):
        self.move_to(self.angle + delta)

    def query(self):
        resp = self._send(0x02, bytes([self.servo_id]))
        if resp and len(resp) >= 6:
            pos = resp[4] | (resp[5] << 8)
            angle = pos / 1000 * 270 - 135
            self.angle = angle
        return self.angle

    def close(self):
        if self._ser:
            self._ser.close()


class ServoEmulator(ServoBase):
    """
    Software emulator for testing without hardware.

    Usage:
        servo = ServoEmulator()
        servo.move_to(45)
        print(servo.query())  # 45
    """

    def __init__(self, min_angle=-90, max_angle=90, home=0, latency=0.01):
        super().__init__(min_angle, max_angle, home)
        self.latency = latency
        self._log = []

    def move_to(self, angle):
        angle = self._clamp(angle)
        time.sleep(self.latency)
        self.angle = angle
        self._log.append(('move', angle, time.time()))

    def nudge(self, delta):
        self.move_to(self.angle + delta)

    def close(self):
        pass


def auto_detect_servo(**kwargs):
    """Auto-detect and return the best available servo.

    Priority: UART > PWM > Emulator
    """
    import glob
    # Try UART
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    if ports:
        try:
            s = ServoUART(port=ports[0], **kwargs)
            if s._ser:
                print("[Auto] Found UART servo on %s" % ports[0])
                return s
        except Exception:
            pass

    # Try PWM
    try:
        import RPi.GPIO
        s = ServoPWM(**kwargs)
        print("[Auto] Using PWM servo")
        return s
    except (ImportError, RuntimeError):
        pass

    # Fallback
    print("[Auto] No hardware, using emulator")
    return ServoEmulator(**kwargs)
