<div align="center">

# PiGimbal

**Smart Gimbal Control for Raspberry Pi**

PID tracking · Kalman filtering · Multi-servo support · Web control

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-00ff88?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi-A22866?style=flat-square&logo=raspberrypi&logoColor=white)](https://raspberrypi.org)
[![Tests](https://img.shields.io/badge/Tests-21%2F21-00ff88?style=flat-square)](tests/)

</div>

---

## What is PiGimbal?

PiGimbal is a **3-line Python library** for controlling gimbals on Raspberry Pi. It handles servo control, target tracking, and web streaming — so you can focus on your project, not the plumbing.

```python
from pigimbal import Gimbal, Camera, ColorDetector

gimbal = Gimbal()
camera = Camera()
detector = ColorDetector("red")

gimbal.track_start(detector)
while True:
    frame = camera.read()
    gimbal.track_step(frame)  # Auto-tracks red objects!
```

## Features

| Feature | Description |
|---------|-------------|
| **PID Tracking** | Smooth auto-tracking with anti-windup PID controller |
| **Kalman Filter** | Predicts target position when temporarily lost |
| **Multi-Servo** | SG90 (PWM), CLB-S25 (UART), or Emulator (no hardware) |
| **Auto-Detect** | Finds camera and servo automatically |
| **Web Control** | Built-in MJPEG stream + control panel |
| **Cross-Platform** | Linux / Windows / macOS (with emulator mode) |
| **Zero Config** | Works out of the box, no calibration needed |

## Installation

```bash
# Basic (no hardware required)
pip install pigimbal

# With hardware support (Raspberry Pi)
pip install pigimbal[hardware]

# Full (includes web server)
pip install pigimbal[full]

# Dev
git clone https://github.com/wcy-creator/pigimbal
cd pigimbal
pip install -e ".[dev]"
pytest tests/ -v
```

## Quick Start

### Control Gimbal
```python
from pigimbal import Gimbal

gimbal = Gimbal()
gimbal.move_to(pan=30, tilt=15)
print(gimbal.query())   # (30.0, 15.0)
gimbal.nudge(5, -3)
gimbal.center()
gimbal.close()
```

### Auto-Track Objects
```python
from pigimbal import Gimbal, Camera, ColorDetector

gimbal = Gimbal()
camera = Camera()
detector = ColorDetector(lower=(0, 100, 100), upper=(10, 255, 255))

gimbal.track_start(detector)
for _ in range(300):
    frame = camera.read()
    if frame is not None:
        result = gimbal.track_step(frame)
        if result:
            print("Tracking:", result)  # (cx, cy, area)
gimbal.close()
```

### Web Control Panel
```python
from pigimbal import Gimbal
from pigimbal.stream import serve

gimbal = Gimbal()
serve(gimbal=gimbal, port=8080)  # Open http://<pi-ip>:8080
```

## Color Presets

```python
from pigimbal import create_detector

red_det = create_detector("red")
blue_det = create_detector("blue")
green_det = create_detector("green")
# Available: red, blue, green, yellow, orange, purple
```

## Hardware Setup

| Servo Type | Connection | Pin |
|------------|-----------|-----|
| SG90 (PWM) | Signal → GPIO18 | Pin 12 |
| SG90 (PWM) | Signal → GPIO19 | Pin 35 |
| CLB-S25 (UART) | UC01 USB adapter | /dev/ttyUSB0 |

> **Power**: Always use external 5V supply (≥2A) for servos.

## PID Tuning

```python
gimbal = Gimbal(config={
    "pid": {
        "kp_pan": 0.06,    # Proportional (responsiveness)
        "ki_pan": 0.002,   # Integral (steady-state error)
        "kd_pan": 0.01,    # Derivative (damping)
        "out_max_pan": 3.0, # Max output (speed limit)
    }
})
```

| Parameter | Too High | Too Low |
|-----------|----------|---------|
| kp | Oscillation | Slow tracking |
| ki | Overshoot | Never reaches target |
| kd | Lag | Oscillation |

## Architecture

```
┌──────────────────────────────────────────┐
│              PiGimbal Library            │
├──────────┬──────────┬──────────┬─────────┤
│ Gimbal   │ Tracker  │ Camera   │ Stream  │
│ (servo)  │ (PID +   │ (V4L2 /  │ (MJPEG  │
│          │  Kalman) │  Direct) │  + API) │
├──────────┴──────────┴──────────┴─────────┤
│          Servo Abstraction Layer         │
│  SG90(PWM) │ CLB-S25(UART) │ Emulator   │
└──────────────────────────────────────────┘
```

## Project Structure

```
pigimbal/
├── pigimbal/
│   ├── __init__.py      # Package entry
│   ├── gimbal.py        # High-level controller
│   ├── servo.py         # Servo drivers
│   ├── tracker.py       # PID + Kalman
│   ├── camera.py        # Camera auto-detect
│   ├── detector.py      # Color detection
│   └── stream.py        # Web server
├── examples/
│   ├── quick_start.py   # 10-line demo
│   ├── track_color.py   # Color tracking
│   └── web_control.py   # Web panel
├── tests/               # 21 tests
├── pyproject.toml
└── README.md
```

## Related Projects

- **[MedVision](https://github.com/wcy-creator/medvision)** — Surgical instrument tracking system
- **[VisionAgent](https://github.com/wcy-creator/visionagent)** — LLM-powered visual agent

## License

MIT License

## Author

**W-cy** — Robotics engineer building intelligent robotic systems.

- GitHub: [@wcy-creator](https://github.com/wcy-creator)
- Projects: [MedVision](https://github.com/wcy-creator/medvision) | [VisionAgent](https://github.com/wcy-creator/visionagent)

---

If you find PiGimbal useful, please give it a ⭐!
