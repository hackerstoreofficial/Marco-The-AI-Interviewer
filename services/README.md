# Marco Services - OCR and Face Tracking

This directory contains core services for the Marco AI Interview Simulator.

## Services Overview

### 1. OCR Service (`ocr_service.py`)

Extracts and parses text from resume files (PDF, DOCX).

**Features:**
- PDF text extraction using pdfplumber
- DOCX text extraction using python-docx
- OCR support for scanned documents using pytesseract
- Resume parsing with skill extraction
- Email and phone number detection
- Section identification (Education, Experience, Skills, etc.)

**Usage:**

```python
from services import OCRService

# Initialize service
ocr = OCRService()

# Extract raw text
text = ocr.extract_text("resume.pdf")
print(text)

# Parse resume with structured data
parsed = ocr.parse_resume("resume.docx")
print(f"Email: {parsed['email']}")
print(f"Phone: {parsed['phone']}")
print(f"Skills: {parsed['skills']}")
print(f"Sections: {parsed['sections']}")
```

**Standalone Test:**
```bash
python services/test_ocr.py
```

---

### 2. Face Tracking Service (`face_tracking_service.py`)

Monitors face position and gaze for interview proctoring.

**Features:**
- Real-time face detection using MediaPipe Face Mesh
- Head pose estimation (pitch, yaw, roll angles)
- "Looking away" detection based on configurable thresholds
- Violation counter with automatic termination
- Visual annotations for debugging

**Usage:**

```python
from services import FaceTrackingService
import cv2

# Initialize service
tracker = FaceTrackingService(
    max_violations=7,
    look_away_threshold=30.0
)

# Process video frames
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Analyze frame
    metrics = tracker.process_frame(frame)
    
    if metrics.is_looking_away:
        print(f"Warning! Violation {tracker.get_violation_count()}")
    
    # Check if terminated
    if tracker.is_terminated():
        print("Interview terminated - too many violations!")
        break
    
    # Optional: Draw annotations
    annotated = tracker.draw_annotations(frame, metrics)
    cv2.imshow('Tracking', annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

**Standalone Test:**
```bash
python services/test_face_tracking.py
```

---

## Installation

### 1. Create Virtual Environment (REQUIRED)

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
pip install -r ../requirements.txt
```

### 3. Install Tesseract OCR (for scanned document support)

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer and note installation path
3. Add to PATH or set in code:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

---

## Testing

### Test OCR Service
```bash
python services/test_ocr.py
```

Tests include:
- Service initialization
- DOCX text extraction
- PDF text extraction
- Resume parsing (skills, email, phone)
- Error handling

### Test Face Tracking Service
```bash
python services/test_face_tracking.py
```

Tests include:
- Service initialization
- Webcam access
- Live face tracking (with user interaction)
- Violation counting logic

---

## API Reference

### OCRService

| Method | Description | Returns |
|--------|-------------|---------|
| `extract_text(file_path)` | Extract raw text from file | `str` |
| `parse_resume(file_path)` | Parse resume into structured data | `dict` |

**Parsed Resume Structure:**
```python
{
    'raw_text': str,           # Full extracted text
    'skills': List[str],       # Identified technical skills
    'email': Optional[str],    # Email address
    'phone': Optional[str],    # Phone number
    'sections': Dict[str, str] # Identified sections
}
```

### FaceTrackingService

| Method | Description | Returns |
|--------|-------------|---------|
| `process_frame(frame)` | Analyze video frame | `FaceMetrics` |
| `is_terminated()` | Check if max violations reached | `bool` |
| `get_violation_count()` | Get current violation count | `int` |
| `reset_violations()` | Reset violation counter | `None` |
| `get_status()` | Get tracking statistics | `dict` |
| `draw_annotations(frame, metrics)` | Draw debug visuals | `np.ndarray` |

**FaceMetrics Structure:**
```python
@dataclass
class FaceMetrics:
    is_face_detected: bool
    head_pose: Optional[Tuple[float, float, float]]  # (pitch, yaw, roll)
    is_looking_away: bool
    confidence: float
    violation_message: Optional[str]
```

---

## Integration with Backend

Both services are designed to be imported and used by the FastAPI backend:

```python
# In your FastAPI app
from services import OCRService, FaceTrackingService

app = FastAPI()

# Initialize services
ocr_service = OCRService()
face_tracker = FaceTrackingService()

@app.post("/upload-resume")
async def upload_resume(file: UploadFile):
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Parse resume
    resume_data = ocr_service.parse_resume(file_path)
    return resume_data

@app.post("/analyze-frame")
async def analyze_frame(frame_data: bytes):
    # Decode frame
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Analyze
    metrics = face_tracker.process_frame(frame)
    
    return {
        "is_looking_away": metrics.is_looking_away,
        "violations": face_tracker.get_violation_count(),
        "terminated": face_tracker.is_terminated()
    }
```

---

## Troubleshooting

### "pdfplumber not installed"
```bash
pip install pdfplumber
```

### "MediaPipe not installed"
```bash
pip install mediapipe opencv-python
```

### "Tesseract not found"
Install Tesseract OCR system binary (see Installation section above)

### Webcam not accessible
- Check camera permissions in system settings
- Ensure no other application is using the camera
- Try different camera index: `cv2.VideoCapture(1)` instead of `0`

---

## License

Part of Marco AI Interview Simulator project.
