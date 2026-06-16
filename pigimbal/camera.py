"""
Cross-platform camera abstraction: V4L2 / DirectShow / AVFoundation / Emulator.
"""
import time
import sys


class Camera:
    """
    Auto-detect and use available camera.

    Usage:
        cam = Camera()
        frame = cam.read()     # BGR numpy array
        cam.close()
    """

    def __init__(self, device=None, width=640, height=480):
        self.width = width
        self.height = height
        self.cap = None
        self._backend = None
        self._frame_count = 0
        self._open(device)

    def _open(self, device):
        import cv2

        if device is not None:
            self.cap = cv2.VideoCapture(device)
            if self.cap.isOpened():
                self._backend = "direct"
                self._configure()
                return

        # Auto-detect backend
        if sys.platform == "linux":
            backends = [
                (cv2.CAP_V4L2, "V4L2"),
                (cv2.CAP_GSTREAMER, "GStreamer"),
                (cv2.CAP_FFMPEG, "FFmpeg"),
            ]
        elif sys.platform == "win32":
            backends = [
                (cv2.CAP_DSHOW, "DirectShow"),
                (cv2.CAP_MSMF, "MediaFoundation"),
                (cv2.CAP_FFMPEG, "FFmpeg"),
            ]
        else:  # macOS
            backends = [
                (cv2.CAP_AVFOUNDATION, "AVFoundation"),
                (cv2.CAP_FFMPEG, "FFmpeg"),
            ]

        for backend_id, name in backends:
            for dev_id in range(4):
                try:
                    cap = cv2.VideoCapture(dev_id, backend_id)
                    if cap.isOpened():
                        self.cap = cap
                        self._backend = name
                        self._configure()
                        print("[Camera] Using %s (device %d)" % (name, dev_id))
                        return
                except Exception:
                    continue

        # Last resort
        for dev_id in range(4):
            cap = cv2.VideoCapture(dev_id)
            if cap.isOpened():
                self.cap = cap
                self._backend = "default"
                self._configure()
                print("[Camera] Using default (device %d)" % dev_id)
                return

        print("[Camera] WARNING: No camera found, using emulator")
        self._backend = "emulator"

    def _configure(self):
        if self.cap:
            self.cap.set(3, self.width)
            self.cap.set(4, self.height)

    def read(self):
        if self._backend == "emulator":
            return self._emulator_frame()
        ret, frame = self.cap.read()
        if ret:
            self._frame_count += 1
        return frame if ret else None

    def is_open(self):
        return self.cap is not None and self.cap.isOpened() or self._backend == "emulator"

    def get_fps(self):
        return self._fps if hasattr(self, '_fps') else 0

    def _emulator_frame(self):
        import numpy as np
        import cv2
        self._frame_count += 1
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.circle(img, (self.width // 2, self.height // 2), 30, (0, 0, 200), -1)
        cv2.putText(img, "EMU", (self.width // 2 - 20, self.height // 2 + 60),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        time.sleep(0.03)
        return img

    def close(self):
        if self.cap:
            self.cap.release()
