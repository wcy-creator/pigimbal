"""
PID controller and Kalman filter for gimbal tracking.
"""
import time
import numpy as np


class PIDController:
    """
    PID controller with anti-windup and output clamping.

    Usage:
        pid = PIDController(kp=0.06, ki=0.002, kd=0.01)
        while True:
            error = target - current
            cmd = pid.compute(error)
            servo.nudge(cmd)
    """

    def __init__(self, kp=0.06, ki=0.002, kd=0.01, imax=50, out_max=3.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.imax = imax
        self.out_max = out_max
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = 0.0

    def compute(self, error):
        now = time.time()
        dt = now - self.prev_time if self.prev_time > 0 else 0.001
        dt = max(dt, 0.0001)

        p = self.kp * error
        self.integral = max(-self.imax, min(self.imax, self.integral + error * dt))
        i = self.ki * self.integral
        d = self.kd * (error - self.prev_error) / dt if self.prev_time > 0 else 0

        self.prev_error = error
        self.prev_time = now

        return max(-self.out_max, min(self.out_max, p + i + d))

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = 0.0


class KalmanTracker:
    """
    2D Kalman filter for position + velocity estimation.

    Usage:
        kf = KalmanTracker()
        kf.update([x, y])          # feed measurement
        pred = kf.predict(0.1)     # predict 100ms ahead
        vx, vy = kf.get_velocity()
    """

    def __init__(self, dt=0.033):
        self.dt = dt
        self.x = np.zeros(4)  # [x, y, vx, vy]
        self.P = np.eye(4) * 500
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1,  0],
            [0, 0, 0,  1]
        ])
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        self.Q = np.eye(4) * 0.1
        self.R = np.eye(2) * 15.0
        self.initialized = False
        self.last_update = 0

    def update(self, z):
        if not self.initialized:
            self.x[:2] = z
            self.initialized = True
            self.last_update = time.time()
            return self.x[:2].copy()

        dt = time.time() - self.last_update
        if dt > 0:
            self.F[0, 2] = dt
            self.F[1, 3] = dt

        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

        z_arr = np.array(z, dtype=float)
        y = z_arr - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P

        self.last_update = time.time()
        return self.x[:2].copy()

    def predict(self, seconds_ahead=0.0):
        if not self.initialized:
            return None
        F = self.F.copy()
        F[0, 2] = seconds_ahead
        F[1, 3] = seconds_ahead
        x_pred = F @ self.x
        return x_pred[:2].copy()

    def get_velocity(self):
        return (float(self.x[2]), float(self.x[3]))

    def reset(self):
        self.x = np.zeros(4)
        self.P = np.eye(4) * 500
        self.initialized = False
