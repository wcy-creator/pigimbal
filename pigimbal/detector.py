"""
Color-based object detector with EMA smoothing.
"""
import numpy as np
import cv2


class ColorDetector:
    """
    HSV color-based object detection.

    Usage:
        det = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))
        cx, cy, area = det.detect(frame)  # or None
    """

    def __init__(self, lower=(0, 100, 100), upper=(10, 255, 255),
                 min_area=200, ema_alpha=0.5):
        self.lower = np.array(lower, dtype=np.uint8)
        self.upper = np.array(upper, dtype=np.uint8)
        self.min_area = min_area
        self.ema_alpha = ema_alpha
        self._ema = None

    def detect(self, bgr):
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            self._ema = None
            return None

        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area < self.min_area:
            self._ema = None
            return None

        M = cv2.moments(c)
        if M["m00"] == 0:
            return None
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        if self._ema is None:
            self._ema = (cx, cy)
        else:
            a = self.ema_alpha
            self._ema = (int(a * cx + (1 - a) * self._ema[0]),
                         int(a * cy + (1 - a) * self._ema[1]))

        return (self._ema[0], self._ema[1], int(area))

    def detect_multi(self, bgr, max_targets=5):
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        results = []
        for c in sorted(contours, key=cv2.contourArea, reverse=True)[:max_targets]:
            area = cv2.contourArea(c)
            if area < self.min_area:
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            results.append((cx, cy, int(area)))
        return results


# Preset color ranges
PRESETS = {
    "red":    ((0, 100, 100),   (10, 255, 255)),
    "blue":   ((100, 100, 100), (130, 255, 255)),
    "green":  ((35, 100, 100),  (85, 255, 255)),
    "yellow": ((20, 100, 100),  (35, 255, 255)),
    "orange": ((10, 100, 100),  (20, 255, 255)),
    "purple": ((130, 50, 50),   (170, 255, 255)),
}


def create_detector(color="red", **kwargs):
    """Create detector with preset color."""
    if color not in PRESETS:
        raise ValueError("Unknown color: %s (available: %s)" % (color, list(PRESETS.keys())))
    lower, upper = PRESETS[color]
    return ColorDetector(lower=lower, upper=upper, **kwargs)
