"""
Face Tracking Service for Interview Proctoring
Uses HeadPoseDetector for real-time face detection and gaze tracking
"""
import numpy as np
import cv2
from typing import Dict, Optional
from pathlib import Path
import logging

from .headpose_detection import HeadPoseDetector

logger = logging.getLogger(__name__)


class FaceMetrics:
    """Face tracking metrics returned by process_frame"""
    def __init__(self, is_face_detected: bool = False, is_looking_away: bool = False,
                 head_pose: tuple = (0.0, 0.0, 0.0), confidence: float = 0.0,
                 violation_message: str = ""):
        self.is_face_detected = is_face_detected
        self.is_looking_away = is_looking_away
        self.head_pose = head_pose  # (pitch, yaw, roll)
        self.confidence = confidence
        self.violation_message = violation_message


class FaceTrackingService:
    """
    Face tracking service for interview proctoring.
    Wraps HeadPoseDetector for integration with backend.
    """
    
    def __init__(self, yaw_threshold: float = 30.0, looking_away_duration: float = 2.0):
        """
        Initialize face tracking service.
        
        Args:
            yaw_threshold: Yaw angle threshold for "looking away" detection
            looking_away_duration: Time in seconds before counting as violation
        """
        self.detector = HeadPoseDetector(
            model_dir="models",
            yaw_threshold=yaw_threshold,
            looking_away_duration=looking_away_duration
        )
        self.violation_count = 0
        logger.info(f"FaceTrackingService initialized with yaw_threshold={yaw_threshold}, "
                   f"looking_away_duration={looking_away_duration}")
    
    def process_frame(self, frame: np.ndarray) -> FaceMetrics:
        """
        Process a video frame for face tracking.
        
        Args:
            frame: Input video frame (BGR format from OpenCV)
            
        Returns:
            FaceMetrics object with detection results
        """
        try:
            # Process frame with HeadPoseDetector
            _, status = self.detector.process_frame(frame)
            
            # Extract metrics
            is_face_detected = status.get('face_detected', False)
            is_looking_away = status.get('looking_away', False)
            pitch = status.get('pitch', 0.0)
            yaw = status.get('yaw', 0.0)
            roll = status.get('roll', 0.0)
            head_pose = (pitch, yaw, roll)
            
            # Build violation message
            violation_message = ""
            if not is_face_detected:
                violation_message = "No face detected"
            elif status.get('multiple_faces', False):
                violation_message = "Multiple faces detected"
            elif is_looking_away:
                violation_message = f"Looking away (yaw: {yaw:.1f}°)"
                self.violation_count = self.detector.total_violations
            
            # Confidence (approximate based on face detection)
            confidence = 0.9 if is_face_detected else 0.0
            
            return FaceMetrics(
                is_face_detected=is_face_detected,
                is_looking_away=is_looking_away,
                head_pose=head_pose,
                confidence=confidence,
                violation_message=violation_message
            )
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return FaceMetrics(
                is_face_detected=False,
                is_looking_away=False,
                head_pose=(0.0, 0.0, 0.0),
                confidence=0.0,
                violation_message=f"Processing error: {str(e)}"
            )
    
    def reset(self):
        """Reset violation counters"""
        self.violation_count = 0
        self.detector.total_violations = 0
        self.detector.looking_away_start_time = None
        logger.info("Face tracking service reset")


# Singleton instance management
_face_service_instance: Optional[FaceTrackingService] = None


def get_face_tracking_service() -> FaceTrackingService:
    """Get or create singleton face tracking service instance"""
    global _face_service_instance
    if _face_service_instance is None:
        _face_service_instance = FaceTrackingService(
            yaw_threshold=30.0,
            looking_away_duration=2.0
        )
    return _face_service_instance


def reset_face_tracking_service():
    """Reset the face tracking service"""
    global _face_service_instance
    if _face_service_instance:
        _face_service_instance.reset()
