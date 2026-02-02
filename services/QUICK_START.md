# Face Tracking Service - Quick Start Guide

## 🎯 Just Want to See It Working?

Run the **visual demo** - it shows face tracking in real-time with clear visual feedback:

```bash
python services/demo_face_tracking.py
```

### What You'll See:
- **🟢 Green border** = You're looking at the camera (good!)
- **🔴 Red border** = You're looking away
- **Blue arrow** = Shows horizontal head rotation (left/right)
- **Green arrow** = Shows vertical head rotation (up/down)
- **Live angles** = Pitch, Yaw, Roll values
- **FPS counter** = Performance indicator

**Press 'Q' to quit**

---

## 🧪 Full Testing Suite

For comprehensive testing with violation tracking and termination:

```bash
python services/test_face_tracking.py
```

Choose from:
1. **Quick Test** - Unlimited duration, test until you quit
2. **Timed Test** - 30-second session
3. **Custom Configuration** - Set your own parameters

### Features:
- Violation counter with progress bar
- Pause/Resume (SPACE)
- Screenshot capture (S)
- Reset violations (R)
- Auto-termination when max violations reached

---

## 📝 Understanding the Output

### Terminal Output
The terminal shows:
- Initialization messages
- Violation warnings
- Final statistics

### Video Window (THIS IS THE IMPORTANT PART!)
**Look at the video window that opens** - this shows:
- Your webcam feed
- Real-time tracking overlay
- Visual indicators
- Status information

> **Note:** If violations happen too quickly, it means the camera detected you looking away at startup. The demo mode (`demo_face_tracking.py`) won't terminate and is better for just seeing if it works.

---

## 🔧 Troubleshooting

### "Webcam not accessible"
- Make sure your webcam is connected
- Close other apps using the webcam (Zoom, Teams, etc.)
- Try a different camera index in the code

### "Too many violations immediately"
- Use the demo mode instead: `python services/demo_face_tracking.py`
- Or increase the threshold in custom configuration (e.g., 45 degrees instead of 30)
- Or increase max violations (e.g., 20 instead of 7)

### "No video window appears"
- The window might be behind other windows
- Check your taskbar for "Face Tracking Demo"
- Make sure OpenCV is installed: `pip install opencv-python`

---

## 🎮 Controls Summary

### Demo Mode (`demo_face_tracking.py`)
- **Q** - Quit

### Full Test Mode (`test_face_tracking.py`)
- **Q** - Quit
- **R** - Reset violation counter
- **S** - Save screenshot
- **SPACE** - Pause/Resume

---

## 💡 Tips

1. **Start with demo mode** to verify everything works
2. **Look at the video window**, not just the terminal
3. **Position yourself** so your face is clearly visible before starting
4. **Good lighting** helps with detection accuracy
5. **Sit at normal distance** from camera (not too close, not too far)
