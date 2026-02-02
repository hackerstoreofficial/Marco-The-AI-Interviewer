# Model Files Directory

This directory contains the face detection and landmark prediction models used by the HeadPoseDetector.

## Required Models

The following models are automatically downloaded when you run the application:

1. **deploy.prototxt** - Face detection model configuration
2. **res10_300x300_ssd_iter_140000_fp16.caffemodel** - Face detection weights
3. **shape_predictor_68_face_landmarks.dat** - Facial landmark predictor

## Auto-Download

Models are automatically downloaded on first run via `services/download_models.py`.

## Manual Download

If auto-download fails, you can manually download:

- Face detection models: [OpenCV DNN samples](https://github.com/opencv/opencv/tree/master/samples/dnn/face_detector)
- Landmark predictor: [dlib models](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)

Place the files in this `services/models/` directory.

## File Sizes

- deploy.prototxt: ~28 KB
- res10_300x300_ssd_iter_140000_fp16.caffemodel: ~5.1 MB
- shape_predictor_68_face_landmarks.dat: ~99.7 MB (compressed: ~64 MB)

**Note**: These files are excluded from git due to their size. They will be downloaded automatically when needed.
