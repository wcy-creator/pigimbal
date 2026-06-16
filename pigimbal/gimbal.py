"""
High-level Gimbal controller: combines servo + PID + Kalman + detector.
"""
import time
import json
import os
from .servo import ServoEmulator, auto_detect_servo
from .tracker import PIDController, KalmanTracker


class Gimbal:
    """
    Two-axis gimbal with auto-tracking.

    Usage:
        g = Gimbal()
        g.move_to(pan=30, tilt=15)
        print(g.query())
        g.track_start(detector)
        g.track_stop()
        g.close()
    """

    def __init__(self, pan_servo=None, tilt_servo=None, config=None):
        cfg = config or {}

        # Pan servo
        if pan_servo:
            self.pan = pan_servo
        else:
            self.pan = auto_detect_servo(
                min_angle=cfg.get("pan_min", -90),
                max_angle=cfg.get("pan_max", 90),
                home=cfg.get("pan_home", 0)
            )

        # Tilt servo
        if tilt_servo:
            self.tilt = tilt_servo
        else:
            self.tilt = auto_detect_servo(
                min_angle=cfg.get("tilt_min", -60),
                max_angle=cfg.get("tilt_max", 60),
                home=cfg.get("tilt_home", 0)
            )

        # PID
        pid_cfg = cfg.get("pid", {})
        self.pid_pan = PIDController(
            kp=pid_cfg.get("kp_pan", 0.06),
            ki=pid_cfg.get("ki_pan", 0.002),
            kd=pid_cfg.get("kd_pan", 0.01),
            out_max=pid_cfg.get("out_max_pan", 3.0)
        )
        self.pid_tilt = PIDController(
            kp=pid_cfg.get("kp_tilt", 0.05),
            ki=pid_cfg.get("ki_tilt", 0.001),
            kd=pid_cfg.get("kd_tilt", 0.008),
            out_max=pid_cfg.get("out_max_tilt", 2.5)
        )

        # Kalman
        self.kalman = KalmanTracker()

        # State
        self._tracking = False
        self._detector = None
        self._frame_w = cfg.get("frame_width", 640)
        self._frame_h = cfg.get("frame_height", 480)
        self._center_x = self._frame_w // 2
        self._center_y = self._frame_h // 2
        self._deadzone = cfg.get("deadzone", 20)

    @classmethod
    def from_config(cls, path):
        with open(path) as f:
            cfg = json.load(f)
        return cls(config=cfg.get("gimbal", cfg))

    def move_to(self, pan=None, tilt=None):
        if pan is not None:
            self.pan.move_to(pan)
        if tilt is not None:
            self.tilt.move_to(tilt)

    def nudge(self, dpan=0, dtilt=0):
        new_pan = self.pan.angle + dpan
        new_tilt = self.tilt.angle + dtilt
        self.move_to(pan=new_pan, tilt=new_tilt)

    def query(self):
        return (self.pan.query(), self.tilt.query())

    def center(self):
        self.pan.center()
        self.tilt.center()
        self.pid_pan.reset()
        self.pid_tilt.reset()
        self.kalman.reset()

    def track_start(self, detector):
        self._tracking = True
        self._detector = detector
        self.kalman.reset()
        self.pid_pan.reset()
        self.pid_tilt.reset()

    def track_stop(self):
        self._tracking = False

    def track_step(self, frame):
        """One tracking step. Returns detection result or None."""
        if not self._tracking or not self._detector:
            return None

        result = self._detector.detect(frame)
        if result:
            cx, cy, area = result
            self.kalman.update([cx, cy])
            err_x = cx - self._center_x
            err_y = cy - self._center_y

            if abs(err_x) > self._deadzone or abs(err_y) > self._deadzone:
                dpan = self.pid_pan.compute(err_x)
                dtilt = self.pid_tilt.compute(err_y)
                self.nudge(dpan, dtilt)
            return result
        else:
            # Predict with Kalman
            if self.kalman.initialized:
                pred = self.kalman.predict(0.15)
                if pred is not None:
                    err_x = pred[0] - self._center_x
                    err_y = pred[1] - self._center_y
                    dpan = self.pid_pan.compute(err_x) * 0.5
                    dtilt = self.pid_tilt.compute(err_y) * 0.5
                    self.nudge(dpan, dtilt)
            return None

    def status(self):
        pan, tilt = self.query()
        vx, vy = self.kalman.get_velocity()
        return {
            "pan": round(pan, 1),
            "tilt": round(tilt, 1),
            "tracking": self._tracking,
            "velocity": (round(vx, 1), round(vy, 1)),
            "kalman_initialized": self.kalman.initialized,
        }

    def close(self):
        self.center()
        self.pan.close()
        self.tilt.close()
