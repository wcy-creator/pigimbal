"""Quick start - 10 lines to control your gimbal."""
from pigimbal import Gimbal, Camera, ColorDetector

# Initialize
gimbal = Gimbal()
camera = Camera()
detector = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))  # Red

# Move gimbal
gimbal.move_to(pan=30, tilt=15)
print("Position:", gimbal.query())

# Auto-track
gimbal.track_start(detector)
for _ in range(300):
    frame = camera.read()
    if frame is not None:
        result = gimbal.track_step(frame)
        if result:
            print("Tracking: (%d, %d) area=%d" % result)

gimbal.close()
camera.close()
