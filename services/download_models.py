"""
Automated Model Downloader for Head Pose Detection
Downloads all required model files for the face proctoring system.
"""

import urllib.request
import bz2
import shutil
from pathlib import Path
import sys


def download_file(url: str, destination: Path, description: str):
    """Download a file with progress indication."""
    print(f"\n[DOWNLOADING] {description}")
    print(f"URL: {url}")
    print(f"Destination: {destination}")
    
    try:
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\rProgress: {percent}%")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, destination, reporthook)
        print(f"\n✅ Downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading: {e}")
        return False


def extract_bz2(source: Path, destination: Path):
    """Extract a .bz2 file."""
    print(f"\n[EXTRACTING] {source.name}")
    
    try:
        with bz2.open(source, 'rb') as f_in:
            with open(destination, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"✅ Extracted successfully!")
        
        # Remove the .bz2 file
        source.unlink()
        print(f"🗑️  Removed compressed file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False


def main():
    """Main function to download all models."""
    print("=" * 70)
    print("MODEL DOWNLOADER - Head Pose Detection")
    print("=" * 70)
    
    # Define models directory
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Models directory: {models_dir}")
    
    # Define model files
    models = [
        {
            "url": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
            "filename": "deploy.prototxt",
            "description": "OpenCV DNN Face Detector - Architecture"
        },
        {
            "url": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
            "filename": "res10_300x300_ssd_iter_140000.caffemodel",
            "description": "OpenCV DNN Face Detector - Weights"
        },
        {
            "url": "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
            "filename": "shape_predictor_68_face_landmarks.dat.bz2",
            "description": "Dlib 68-Point Landmark Predictor (Compressed)"
        }
    ]
    
    # Download each model
    success_count = 0
    for model in models:
        destination = models_dir / model["filename"]
        
        # Skip if already exists
        if destination.exists():
            print(f"\n✓ {model['filename']} already exists, skipping...")
            success_count += 1
            continue
        
        # Download
        if download_file(model["url"], destination, model["description"]):
            success_count += 1
    
    # Extract dlib model if needed
    bz2_file = models_dir / "shape_predictor_68_face_landmarks.dat.bz2"
    dat_file = models_dir / "shape_predictor_68_face_landmarks.dat"
    
    if bz2_file.exists() and not dat_file.exists():
        extract_bz2(bz2_file, dat_file)
    
    # Verify all files
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    required_files = [
        "deploy.prototxt",
        "res10_300x300_ssd_iter_140000.caffemodel",
        "shape_predictor_68_face_landmarks.dat"
    ]
    
    all_present = True
    for filename in required_files:
        file_path = models_dir / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ {filename} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {filename} - MISSING!")
            all_present = False
    
    print("\n" + "=" * 70)
    if all_present:
        print("✅ ALL MODELS DOWNLOADED SUCCESSFULLY!")
        print("=" * 70)
        print("\nYou can now run:")
        print("  python services/headpose_detection.py")
    else:
        print("⚠️  SOME MODELS ARE MISSING!")
        print("=" * 70)
        print("\nPlease check the errors above and try again.")
        print("You can also download manually - see services/models/README.md")


if __name__ == "__main__":
    main()
