"""Color tracking demo with web view."""
from pigimbal import Gimbal, Camera, ColorDetector
from pigimbal.stream import serve

gimbal = Gimbal()
camera = Camera()
detector = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))

gimbal.track_start(detector)

import threading
t = threading.Thread(target=serve, args=(camera, gimbal), daemon=True)
t.start()

print("Web: http://0.0.0.0:8080")
print("Tracking red object... Ctrl+C to stop")

try:
    import cv2
    while True:
        frame = camera.read()
        if frame is not None:
            gimbal.track_step(frame)
            cv2.imshow("PiGimbal", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
except KeyboardInterrupt:
    pass

gimbal.close()
camera.close()
cv2.destroyAllWindows()
