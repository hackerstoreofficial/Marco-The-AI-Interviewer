"""
Real-Time Face Proctoring with Head Pose Estimation
Uses OpenCV DNN for face detection and dlib for facial landmarks.

REQUIRED MODELS:
1. Download OpenCV DNN face detector:
   - deploy.prototxt: https://github.com/opencv/opencv/blob/master/samples/dnn/face_detector/deploy.prototxt
   - res10_300x300_ssd_iter_140000.caffemodel: https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
   
2. Download dlib shape predictor:
   - shape_predictor_68_face_landmarks.dat: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
   (Extract the .bz2 file to get the .dat file)

Place all model files in: d:/aii final/services/models/

INSTALLATION:
pip install opencv-python dlib numpy

USAGE:
python services/headpose_detection.py
"""

import cv2
import numpy as np
import dlib
import time
from pathlib import Path
from typing import Tuple, Optional, List


class HeadPoseDetector:
    """Real-time head pose detection for face proctoring."""
    
    def __init__(self, 
                 model_dir: str = "models",
                 yaw_threshold: float = 30.0,
                 looking_away_duration: float = 2.0):
        """
        Initialize head pose detector.
        
        Args:
            model_dir: Directory containing model files
            yaw_threshold: Yaw angle threshold for "looking away" detection
            looking_away_duration: Time in seconds before warning
        """
        self.model_dir = Path(__file__).parent / model_dir
        self.yaw_threshold = yaw_threshold
        self.looking_away_duration = looking_away_duration
        
        # Tracking variables
        self.looking_away_start_time = None
        self.total_violations = 0
        
        # Load models
        self._load_models()
        
        # Define 3D facial model points (standard anthropometric coordinates)
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float64)
        
        # Landmark indices for the 68-point model
        self.landmark_indices = [30, 8, 36, 45, 48, 54]  # Nose, Chin, Eyes, Mouth corners
    
    def _load_models(self):
        """Load OpenCV DNN face detector and dlib landmark predictor."""
        # Paths to model files
        prototxt_path = self.model_dir / "deploy.prototxt"
        caffemodel_path = self.model_dir / "res10_300x300_ssd_iter_140000.caffemodel"
        landmark_path = self.model_dir / "shape_predictor_68_face_landmarks.dat"
        
        # Check if model files exist
        if not prototxt_path.exists():
            raise FileNotFoundError(
                f"deploy.prototxt not found at {prototxt_path}\n"
                "Download from: https://github.com/opencv/opencv/blob/master/samples/dnn/face_detector/deploy.prototxt"
            )
        
        if not caffemodel_path.exists():
            raise FileNotFoundError(
                f"Caffe model not found at {caffemodel_path}\n"
                "Download from: https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
            )
        
        if not landmark_path.exists():
            raise FileNotFoundError(
                f"Landmark predictor not found at {landmark_path}\n"
                "Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2\n"
                "Extract the .bz2 file to get the .dat file"
            )
        
        # Load OpenCV DNN face detector
        print("[INFO] Loading face detector...")
        self.face_net = cv2.dnn.readNetFromCaffe(str(prototxt_path), str(caffemodel_path))
        
        # Load dlib landmark predictor
        print("[INFO] Loading facial landmark predictor...")
        self.landmark_predictor = dlib.shape_predictor(str(landmark_path))
        
        print("[SUCCESS] All models loaded successfully!")
    
    def detect_face(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect face using OpenCV DNN.
        
        Args:
            frame: Input image frame
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            Tuple of (x, y, w, h) for face bounding box, or None if no face detected
        """
        h, w = frame.shape[:2]
        
        # Prepare blob for DNN
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        # Perform detection
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        # Find faces with confidence > threshold
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                
                # Convert to (x, y, w, h) format
                x = x1
                y = y1
                width = x2 - x1
                height = y2 - y1
                
                faces.append((x, y, width, height, confidence))
        
        # Return None if no face or multiple faces
        if len(faces) == 0:
            return None
        elif len(faces) > 1:
            return "multiple"
        else:
            return faces[0][:4]  # Return (x, y, w, h)
    
    def get_landmarks(self, frame: np.ndarray, face_rect: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Get facial landmarks using dlib.
        
        Args:
            frame: Input image frame
            face_rect: Face bounding box (x, y, w, h)
            
        Returns:
            Array of 2D landmark points for selected indices
        """
        x, y, w, h = face_rect
        
        # Convert to dlib rectangle
        dlib_rect = dlib.rectangle(x, y, x + w, y + h)
        
        # Get 68 facial landmarks
        shape = self.landmark_predictor(frame, dlib_rect)
        
        # Extract selected landmarks
        landmarks = []
        for idx in self.landmark_indices:
            point = shape.part(idx)
            landmarks.append([point.x, point.y])
        
        return np.array(landmarks, dtype=np.float64)
    
    def estimate_head_pose(self, landmarks: np.ndarray, frame_shape: Tuple[int, int]) -> Tuple[float, float, float]:
        """
        Estimate head pose using PnP algorithm.
        
        Args:
            landmarks: 2D facial landmark points
            frame_shape: Shape of the frame (height, width)
            
        Returns:
            Tuple of (pitch, yaw, roll) in degrees
        """
        h, w = frame_shape[:2]
        
        # Camera internals (approximate)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        
        # Assume no lens distortion
        dist_coeffs = np.zeros((4, 1))
        
        # Solve PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points,
            landmarks,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return (0.0, 0.0, 0.0)
        
        # Convert rotation vector to rotation matrix
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        
        # Calculate Euler angles
        pitch, yaw, roll = self._rotation_matrix_to_euler_angles(rotation_matrix)
        
        # Convert to degrees
        pitch = np.degrees(pitch)
        yaw = np.degrees(yaw)
        roll = np.degrees(roll)
        
        return (pitch, yaw, roll)
    
    def _rotation_matrix_to_euler_angles(self, R: np.ndarray) -> Tuple[float, float, float]:
        """Convert rotation matrix to Euler angles."""
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0
        
        return (x, y, z)
    
    def draw_annotations(self, frame: np.ndarray, face_rect: Tuple[int, int, int, int], 
                        landmarks: np.ndarray, pose: Tuple[float, float, float]) -> np.ndarray:
        """
        Draw face detection and pose estimation annotations.
        
        Args:
            frame: Input frame
            face_rect: Face bounding box
            landmarks: Facial landmarks
            pose: Head pose angles (pitch, yaw, roll)
            
        Returns:
            Annotated frame
        """
        x, y, w, h = face_rect
        pitch, yaw, roll = pose
        
        # Draw face bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw landmarks
        for point in landmarks:
            cv2.circle(frame, tuple(point.astype(int)), 3, (0, 0, 255), -1)
        
        # Draw nose direction line
        nose_tip = landmarks[0].astype(int)
        
        # Calculate nose direction based on yaw
        nose_length = 100
        nose_end_x = int(nose_tip[0] + nose_length * np.sin(np.radians(yaw)))
        nose_end_y = int(nose_tip[1] - nose_length * np.sin(np.radians(pitch)))
        
        cv2.arrowedLine(frame, tuple(nose_tip), (nose_end_x, nose_end_y), (255, 0, 0), 2, tipLength=0.3)
        
        # Display pose angles
        text_y = y - 10
        cv2.putText(frame, f"Pitch: {pitch:.1f}", (x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Yaw: {yaw:.1f}", (x, text_y - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Roll: {roll:.1f}", (x, text_y - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Check if looking away
        if abs(yaw) > self.yaw_threshold:
            cv2.putText(frame, "LOOKING AWAY!", (10, 30), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 2)
        
        return frame
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Process a single frame for face proctoring.
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (annotated_frame, status_dict)
        """
        status = {
            'face_detected': False,
            'multiple_faces': False,
            'looking_away': False,
            'pitch': 0.0,
            'yaw': 0.0,
            'roll': 0.0,
            'warning': None
        }
        
        # Detect face
        face_result = self.detect_face(frame)
        
        if face_result is None:
            # No face detected
            cv2.putText(frame, "Face Not Detected", (10, 30), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 2)
            self.looking_away_start_time = None
            return frame, status
        
        elif face_result == "multiple":
            # Multiple faces detected
            status['multiple_faces'] = True
            cv2.putText(frame, "Multiple Faces Detected", (10, 30), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 165, 255), 2)
            self.looking_away_start_time = None
            return frame, status
        
        # Single face detected
        status['face_detected'] = True
        face_rect = face_result
        
        # Get landmarks
        landmarks = self.get_landmarks(frame, face_rect)
        if landmarks is None:
            return frame, status
        
        # Estimate head pose
        pitch, yaw, roll = self.estimate_head_pose(landmarks, frame.shape)
        status['pitch'] = pitch
        status['yaw'] = yaw
        status['roll'] = roll
        
        # Check if looking away
        if abs(yaw) > self.yaw_threshold:
            status['looking_away'] = True
            
            # Track duration
            if self.looking_away_start_time is None:
                self.looking_away_start_time = time.time()
            else:
                duration = time.time() - self.looking_away_start_time
                if duration > self.looking_away_duration:
                    self.total_violations += 1
                    warning_msg = f"[WARNING] Looking away for {duration:.1f}s! Total violations: {self.total_violations}"
                    print(warning_msg)
                    status['warning'] = warning_msg
        else:
            self.looking_away_start_time = None
        
        # Draw annotations
        annotated_frame = self.draw_annotations(frame, face_rect, landmarks, (pitch, yaw, roll))
        
        return annotated_frame, status


def main():
    """Main function to run real-time face proctoring."""
    print("=" * 70)
    print("Real-Time Face Proctoring System")
    print("=" * 70)
    
    try:
        # Initialize detector
        detector = HeadPoseDetector(
            yaw_threshold=30.0,
            looking_away_duration=2.0
        )
        
        # Open webcam
        print("\n[INFO] Opening webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("[ERROR] Could not open webcam!")
            return
        
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("[SUCCESS] Webcam opened successfully!")
        print("\nPress 'q' to quit")
        print("=" * 70)
        
        # FPS calculation
        fps_start_time = time.time()
        fps_frame_count = 0
        fps = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to capture frame")
                break
            
            # Process frame
            annotated_frame, status = detector.process_frame(frame)
            
            # Calculate FPS
            fps_frame_count += 1
            if fps_frame_count >= 30:
                fps_end_time = time.time()
                fps = fps_frame_count / (fps_end_time - fps_start_time)
                fps_start_time = fps_end_time
                fps_frame_count = 0
            
            # Display FPS
            cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, annotated_frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Display violations
            cv2.putText(annotated_frame, f"Violations: {detector.total_violations}", 
                       (annotated_frame.shape[1] - 200, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Show frame
            cv2.imshow('Face Proctoring - Press Q to Quit', annotated_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        print("\n" + "=" * 70)
        print("Session Summary:")
        print(f"Total Violations: {detector.total_violations}")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("\nPlease download the required model files as described at the top of this script.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
