"""
Simple Visual Demo for Face Tracking Service
Shows real-time face tracking with visual feedback - NO termination, just pure visualization.
"""

import sys
from pathlib import Path
import time
import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.face_tracking_service import FaceTrackingService


def draw_demo_ui(frame, metrics, service, fps):
    """Draw simple, clear UI for demo."""
    h, w = frame.shape[:2]
    
    # Draw face landmarks if detected
    if metrics.is_face_detected and metrics.head_pose:
        pitch, yaw, roll = metrics.head_pose
        
        # Draw center crosshair
        center_x, center_y = w // 2, h // 2
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)
        
        # Draw head pose arrows
        arrow_length = 100
        
        # Yaw (left-right) - horizontal arrow
        yaw_end_x = int(center_x + arrow_length * np.sin(np.radians(yaw)))
        cv2.arrowedLine(frame, (center_x, center_y), (yaw_end_x, center_y), (255, 0, 0), 3)
        
        # Pitch (up-down) - vertical arrow
        pitch_end_y = int(center_y - arrow_length * np.sin(np.radians(pitch)))
        cv2.arrowedLine(frame, (center_x, center_y), (center_x, pitch_end_y), (0, 255, 0), 3)
        
        # Status box
        box_h = 200
        cv2.rectangle(frame, (10, 10), (350, box_h), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (350, box_h), (255, 255, 255), 2)
        
        # Face status
        cv2.putText(frame, "FACE: DETECTED", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Head angles
        cv2.putText(frame, f"YAW:   {yaw:6.1f}deg", (20, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"PITCH: {pitch:6.1f}deg", (20, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"ROLL:  {roll:6.1f}deg", (20, 135),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Looking status
        if metrics.is_looking_away:
            cv2.putText(frame, "STATUS: LOOKING AWAY", (20, 170),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            # Red border
            cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 0, 255), 5)
        else:
            cv2.putText(frame, "STATUS: LOOKING GOOD", (20, 170),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            # Green border
            cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 255, 0), 5)
    else:
        # No face detected
        cv2.rectangle(frame, (10, 10), (350, 100), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (350, 100), (255, 255, 255), 2)
        cv2.putText(frame, "FACE: NOT DETECTED", (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # Red border
        cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 0, 255), 5)
    
    # FPS counter (bottom right)
    cv2.putText(frame, f"FPS: {fps:.1f}", (w - 150, h - 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    # Instructions (bottom left)
    cv2.putText(frame, "Press 'Q' to quit", (20, h - 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return frame


def run_visual_demo():
    """Run visual demo - no termination, just visualization."""
    print("\n" + "=" * 70)
    print("🎥 FACE TRACKING VISUAL DEMO")
    print("=" * 70)
    print("\nThis demo shows real-time face tracking visualization.")
    print("The window will show:")
    print("  • Green border = Looking at camera")
    print("  • Red border = Looking away")
    print("  • Blue arrow = Horizontal head rotation (yaw)")
    print("  • Green arrow = Vertical head rotation (pitch)")
    print("\nPress 'Q' to quit")
    print("=" * 70)
    
    # Initialize service with high threshold so it doesn't terminate
    service = FaceTrackingService(
        max_violations=999,  # Won't terminate
        look_away_threshold=60.0
    )
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not access webcam")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("\n✅ Webcam opened successfully!")
    print("🎬 Starting demo in 2 seconds...\n")
    time.sleep(2)
    
    frame_times = []
    fps = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame")
            break
        
        # Mirror for natural interaction
        frame = cv2.flip(frame, 1)
        
        # Process frame
        start_time = time.time()
        metrics = service.process_frame(frame)
        
        # Calculate FPS
        frame_times.append(time.time())
        if len(frame_times) > 30:
            frame_times.pop(0)
        if len(frame_times) > 1:
            time_diff = frame_times[-1] - frame_times[0]
            if time_diff > 0:
                fps = (len(frame_times) - 1) / time_diff
        
        # Draw UI
        display_frame = draw_demo_ui(frame, metrics, service, fps)
        
        # Show frame
        cv2.imshow('Face Tracking Demo - Press Q to Quit', display_frame)
        
        # Handle key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\n⏹ Demo stopped")
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 70)
    print("✅ Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        run_visual_demo()
    except KeyboardInterrupt:
        print("\n\n⏹ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure you have installed:")
        print("   pip install mediapipe opencv-python numpy")
