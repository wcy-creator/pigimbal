"""PiGimbal test suite - all tests use emulators (no hardware needed)."""
import sys, time, numpy as np, pytest
sys.path.insert(0, ".")
from pigimbal import Gimbal, Camera, ColorDetector, ServoEmulator, PIDController, KalmanTracker


# ── Servo Tests ──

def test_servo_emulator_move():
    s = ServoEmulator()
    s.move_to(45)
    assert s.angle == 45

def test_servo_emulator_clamp():
    s = ServoEmulator(min_angle=-90, max_angle=90)
    s.move_to(200)
    assert s.angle == 90
    s.move_to(-200)
    assert s.angle == -90

def test_servo_emulator_center():
    s = ServoEmulator(home=0)
    s.move_to(45)
    s.center()
    assert s.angle == 0

def test_servo_emulator_nudge():
    s = ServoEmulator()
    s.move_to(10)
    s.nudge(5)
    assert s.angle == 15
    s.nudge(-20)
    assert s.angle == -5


# ── PID Tests ──

def test_pid_proportional():
    pid = PIDController(kp=0.1, ki=0, kd=0, out_max=20)
    out = pid.compute(100)
    assert out == pytest.approx(10.0, abs=0.2)

def test_pid_clamping():
    pid = PIDController(kp=0.1, ki=0, kd=0, out_max=3)
    out = pid.compute(1000)
    assert out == 3.0

def test_pid_integral():
    pid = PIDController(kp=0, ki=0.1, kd=0, out_max=100, imax=10)
    for _ in range(100):
        pid.compute(10)
    assert abs(pid.integral) <= 10

def test_pid_reset():
    pid = PIDController(kp=0.1, ki=0.1, kd=0.01)
    pid.compute(50)
    pid.reset()
    assert pid.integral == 0


# ── Kalman Tests ──

def test_kalman_init():
    kf = KalmanTracker()
    pos = kf.update([100, 200])
    assert kf.initialized
    assert abs(pos[0] - 100) < 1

def test_kalman_predict():
    kf = KalmanTracker()
    for x, y in [(100, 100), (120, 100), (140, 100)]:
        time.sleep(0.02)
        kf.update([x, y])
    pred = kf.predict(0.1)
    assert pred is not None
    assert pred[0] > 120, "Should predict forward: %.1f" % pred[0]

def test_kalman_velocity():
    kf = KalmanTracker()
    for x, y in [(0, 0), (10, 0), (20, 0)]:
        time.sleep(0.01)
        kf.update([x, y])
    vx, vy = kf.get_velocity()
    assert vx > 0

def test_kalman_reset():
    kf = KalmanTracker()
    kf.update([100, 200])
    kf.reset()
    assert not kf.initialized


# ── Detector Tests ──

def test_detector_red():
    det = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    import cv2
    cv2.circle(img, (320, 240), 40, (0, 0, 200), -1)
    result = det.detect(img)
    assert result is not None
    cx, cy, area = result
    assert abs(cx - 320) < 20

def test_detector_nothing():
    det = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    result = det.detect(img)
    assert result is None

def test_detector_multi():
    det = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    import cv2
    cv2.circle(img, (100, 100), 20, (0, 0, 200), -1)
    cv2.circle(img, (400, 300), 30, (0, 0, 200), -1)
    results = det.detect_multi(img)
    assert len(results) == 2


# ── Gimbal Integration Tests ──

def test_gimbal_move():
    g = Gimbal()
    g.move_to(pan=30, tilt=15)
    pan, tilt = g.query()
    assert abs(pan - 30) < 1
    assert abs(tilt - 15) < 1
    g.close()

def test_gimbal_center():
    g = Gimbal()
    g.move_to(pan=40, tilt=20)
    g.center()
    pan, tilt = g.query()
    assert abs(pan) < 1
    assert abs(tilt) < 1

def test_gimbal_nudge():
    g = Gimbal()
    g.move_to(pan=0, tilt=0)
    g.nudge(10, 5)
    pan, tilt = g.query()
    assert abs(pan - 10) < 1
    assert abs(tilt - 5) < 1
    g.close()

def test_gimbal_track():
    g = Gimbal()
    det = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))
    g.track_start(det)
    assert g._tracking
    g.track_stop()
    assert not g._tracking
    g.close()

def test_gimbal_status():
    g = Gimbal()
    s = g.status()
    assert "pan" in s
    assert "tilt" in s
    assert "tracking" in s
    g.close()


# ── Camera Emulator Test ──

def test_camera_emulator():
    cam = Camera()
    frame = cam.read()
    assert frame is not None
    assert frame.shape == (480, 640, 3)
    cam.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
