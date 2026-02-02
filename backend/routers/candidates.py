"""
Candidates Router - Handle candidate profiles and resume uploads
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Optional
import shutil
from pathlib import Path
import hashlib
import json
import logging

from ..database import Database, db
from ..dependencies import get_ocr_service, validate_file_upload, get_db
from ..config import settings
from services.ocr_service import OCRService

# Configure Logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

class CandidateProfile(BaseModel):
    """Candidate profile data"""
    name: str
    email: EmailStr
    phone: str
    target_position: str

class CandidateResponse(BaseModel):
    """Response after creating candidate"""
    candidate_id: int
    message: str

class ResumeResponse(BaseModel):
    """Response after resume upload"""
    success: bool
    parsed_data: Dict
    message: str

@router.post("/profile", response_model=CandidateResponse)
async def create_candidate_profile(
    profile: CandidateProfile,
    database: Database = Depends(get_db)
):
    """Create candidate profile"""
    try:
        candidate_id = await database.create_candidate(
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            target_position=profile.target_position
        )
        
        return CandidateResponse(
            candidate_id=candidate_id,
            message="Profile created successfully"
        )
    
    except Exception as e:
        logger.error(f"Profile Creation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {str(e)}")

@router.post("/resume/{candidate_id}", response_model=ResumeResponse)
async def upload_resume(
    candidate_id: int,
    file: UploadFile = File(...),
    database: Database = Depends(get_db),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Upload and parse resume"""
    try:
        # 1. Validate file
        file_ext = validate_file_upload(file, settings.ALLOWED_RESUME_EXTENSIONS)
        
        # 2. Save file
        file_hash = hashlib.md5(f"{candidate_id}_{file.filename}".encode()).hexdigest()
        file_path = settings.UPLOAD_DIR / f"{file_hash}{file_ext}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. Parse resume
        logger.info(f"Parsing resume for candidate {candidate_id}")
        parsed_data = ocr_service.parse_resume(file_path)
        
        # 4. Prepare data for DB (CRITICAL FIX: Sanitize Null Bytes)
        raw_text = parsed_data.get('raw_text', '').replace('\x00', '')
        
        skills = json.dumps(parsed_data.get('skills', []))
        experience = json.dumps(parsed_data.get('experience', []))
        projects = json.dumps(parsed_data.get('projects', []))
        
        logger.info(f"Saving resume data to DB for candidate {candidate_id}")
        
        # 5. Update Database
        await database.execute(
            "UPDATE candidates SET resume_text = ?, skills = ?, experience = ?, projects = ? WHERE id = ?",
            (raw_text, skills, experience, projects, candidate_id)
        )
        
        return ResumeResponse(
            success=True,
            parsed_data={
                'email': parsed_data.get('email'),
                'phone': parsed_data.get('phone'),
                'skills': parsed_data.get('skills', []),
                'sections': list(parsed_data.get('sections', {}).keys())
            },
            message="Resume parsed successfully"
        )
    
    except Exception as e:
        logger.error(f"Resume Parsing Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")

@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    database: Database = Depends(get_db)
):
    """Get candidate details"""
    candidate = await database.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate