"""
PiGimbal - Smart Gimbal Control for Raspberry Pi
PID tracking, Kalman filtering, multi-servo support.
"""

__version__ = "1.0.0"
__author__ = "W-cy"

from .servo import ServoPWM, ServoUART, ServoEmulator
from .gimbal import Gimbal
from .tracker import PIDController, KalmanTracker
from .camera import Camera
from .detector import ColorDetector

__all__ = [
    "Gimbal", "Camera", "ColorDetector",
    "ServoPWM", "ServoUART", "ServoEmulator",
    "PIDController", "KalmanTracker",
]
