"""Web-only control panel (no OpenCV GUI needed)."""
from pigimbal import Gimbal
from pigimbal.stream import serve

gimbal = Gimbal()
print("Pan: %.1f  Tilt: %.1f" % gimbal.query())
print("Open http://<pi-ip>:8080 in browser")

serve(gimbal=gimbal, port=8080)
