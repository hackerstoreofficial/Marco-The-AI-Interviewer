"""
Proctoring Router - Face tracking and violation detection
Built from scratch with correct FaceMetrics variable names
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
import numpy as np
import cv2
from typing import Dict, Optional
import logging

from ..database import Database
from ..dependencies import get_db, get_or_create_face_service, cleanup_face_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/proctoring", tags=["proctoring"])


# Response Models
class FrameAnalysisResponse(BaseModel):
    """Response from frame analysis - matches FaceMetrics structure"""
    face_detected: bool
    looking_away: bool
    violation_detected: bool
    violation_count: int
    should_terminate: bool
    message: str
    details: Dict


class TabSwitchResponse(BaseModel):
    """Response from tab switch logging"""
    message: str
    total_tab_switches: int
    should_terminate: bool


class ViolationStatusResponse(BaseModel):
    """Current violation status for session"""
    gaze_violations: int
    tab_switches: int
    should_terminate: bool
    termination_reason: Optional[str] = None


# Endpoints
@router.post("/frame/{session_id}", response_model=FrameAnalysisResponse)
async def analyze_frame(
    session_id: int,
    frame: UploadFile = File(...),
    database: Database = Depends(get_db)
):
    """
    Analyze video frame for face tracking and gaze violations.
    Returns success response even if face tracking fails to prevent frontend errors.
    """
    try:
        # Get session-specific face tracking service
        face_service = get_or_create_face_service(session_id)
        
        # Read and decode image
        contents = await frame.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.warning(f"Session {session_id}: Invalid image data received")
            return FrameAnalysisResponse(
                face_detected=False,
                looking_away=False,
                violation_detected=False,
                should_terminate=False,
                violation_count=0,
                message="Invalid image data",
                details={}
            )
        
        # Process frame with FaceTrackingService
        # Returns FaceMetrics with: is_face_detected, head_pose, is_looking_away, confidence, violation_message
        metrics = face_service.process_frame(img)
        
        # Debug logging to see what's being detected
        logger.info(f"Session {session_id}: Frame processed - Face: {metrics.is_face_detected}, "
                   f"Looking away: {metrics.is_looking_away}, Head pose: {metrics.head_pose}, "
                   f"Violation count: {face_service.violation_count}")
        
        # Check if HeadPoseDetector counted a new violation
        # HeadPoseDetector only increments after looking away for 2+ seconds
        current_violations = face_service.violation_count
        session = await database.get_session(session_id)
        db_violations = session.get('gaze_violations', 0)
        
        # If HeadPoseDetector counted a new violation, log it to database
        if current_violations > db_violations:
            await database.increment_violation(session_id, 'gaze')
            await database.log_proctoring_event(
                session_id,
                event_type='gaze_violation',
                severity='warning',
                details={
                    'head_pose': metrics.head_pose,
                    'confidence': metrics.confidence,
                    'violation_count': current_violations
                }
            )
            logger.info(f"Session {session_id}: Gaze violation detected (count: {current_violations})")
            
            # Re-fetch session to get updated violation count
            session = await database.get_session(session_id)
        
        # Check if should terminate (max 5 violations)
        should_terminate = session.get('gaze_violations', 0) >= 5
        
        if should_terminate:
            await database.update_session_status(
                session_id,
                status='terminated',
                termination_reason='excessive_gaze_violations'
            )
            logger.warning(f"Session {session_id}: Terminated due to excessive violations")
        
        # Build response - map FaceMetrics fields to response fields
        return FrameAnalysisResponse(
            face_detected=metrics.is_face_detected,
            looking_away=metrics.is_looking_away,
            violation_detected=metrics.is_looking_away and metrics.is_face_detected,
            should_terminate=should_terminate,
            violation_count=face_service.violation_count,
            message=metrics.violation_message or "Frame analyzed successfully",
            details={
                'head_pose': metrics.head_pose,
                'confidence': metrics.confidence,
                'is_face_detected': metrics.is_face_detected,
                'is_looking_away': metrics.is_looking_away
            }
        )
    
    except Exception as e:
        logger.error(f"Session {session_id}: Frame analysis failed - {str(e)}", exc_info=True)
        
        # Return graceful error response instead of 500
        return FrameAnalysisResponse(
            face_detected=False,
            looking_away=False,
            violation_detected=False,
            should_terminate=False,
            violation_count=0,
            message=f"Face tracking error: {str(e)}",
            details={"error": str(e)}
        )


@router.post("/tab-switch/{session_id}", response_model=TabSwitchResponse)
async def log_tab_switch(
    session_id: int,
    database: Database = Depends(get_db)
):
    """Log tab switch violation and check for termination (>= 2 switches)"""
    try:
        # Increment violation in database
        await database.increment_violation(session_id, 'tab_switch')
        await database.log_proctoring_event(
            session_id,
            event_type='tab_switch',
            severity='warning',
            details={}
        )
        
        # Get current session to check total tab switches
        session = await database.get_session(session_id)
        tab_switches = session.get('tab_switch_count', 0) if session else 0
        
        # Check if should terminate (>= 2 tab switches)
        should_terminate = tab_switches >= 2
        
        if should_terminate:
            await database.update_session_status(
                session_id,
                status='terminated',
                termination_reason='excessive_tab_switches'
            )
            logger.warning(f"Session {session_id}: Terminated due to excessive tab switches ({tab_switches})")
        else:
            logger.info(f"Session {session_id}: Tab switch detected ({tab_switches}/2)")
        
        return TabSwitchResponse(
            message="Tab switch logged",
            total_tab_switches=tab_switches,
            should_terminate=should_terminate
        )
    
    except Exception as e:
        logger.error(f"Session {session_id}: Failed to log tab switch - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log tab switch: {str(e)}")


@router.get("/status/{session_id}", response_model=ViolationStatusResponse)
async def get_violation_status(
    session_id: int,
    database: Database = Depends(get_db)
):
    """Get current violation status for a session"""
    try:
        # Get session from database
        session = await database.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get face service to check current violation count
        face_service = get_or_create_face_service(session_id)
        
        gaze_violations = face_service.violation_count
        tab_switches = session.get('tab_switch_count', 0)
        
        # Check termination conditions
        should_terminate = (gaze_violations >= face_service.max_violations) or (tab_switches >= 2)
        
        if should_terminate:
            if gaze_violations >= face_service.max_violations:
                termination_reason = 'excessive_gaze_violations'
            else:
                termination_reason = 'excessive_tab_switches'
        else:
            termination_reason = None
        
        return ViolationStatusResponse(
            gaze_violations=gaze_violations,
            tab_switches=tab_switches,
            should_terminate=should_terminate,
            termination_reason=termination_reason
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session {session_id}: Failed to get status - {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
