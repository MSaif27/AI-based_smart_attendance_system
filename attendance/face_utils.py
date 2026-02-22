"""
DeepFace-based face recognition utility for LPU Smart Attendance.
Handles: photo upload matching, webcam frame matching.
"""
import os
import base64
import tempfile
import numpy as np
from django.conf import settings


def _decode_base64_image(data_url):
    """Convert base64 data URL to a temp file path."""
    if ',' in data_url:
        header, data = data_url.split(',', 1)
    else:
        data = data_url
    img_bytes = base64.b64decode(data)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    tmp.write(img_bytes)
    tmp.close()
    return tmp.name


def recognize_face_from_image(capture_image_path, students_queryset):
    """
    Compare a captured image against all enrolled students.
    Returns list of (student, confidence) matches above threshold.
    """
    try:
        from deepface import DeepFace
    except ImportError:
        return []

    results = []
    threshold = getattr(settings, 'FACE_RECOGNITION_THRESHOLD', 0.4)
    model = getattr(settings, 'FACE_RECOGNITION_MODEL', 'VGG-Face')
    metric = getattr(settings, 'FACE_RECOGNITION_DISTANCE', 'cosine')

    for student in students_queryset:
        if not student.photo or not student.face_enrolled:
            continue

        db_photo_path = os.path.join(settings.MEDIA_ROOT, str(student.photo))
        if not os.path.exists(db_photo_path):
            continue

        try:
            result = DeepFace.verify(
                img1_path=capture_image_path,
                img2_path=db_photo_path,
                model_name=model,
                distance_metric=metric,
                enforce_detection=False
            )
            if result['verified']:
                confidence = 1 - result['distance']  # Convert distance to confidence
                results.append((student, round(confidence * 100, 1)))
        except Exception:
            continue

    # Sort by confidence descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def recognize_faces_bulk(capture_image_path, students_queryset):
    """
    Detect ALL faces in one image (group photo / classroom webcam shot)
    and match each to enrolled students.
    Returns dict: {student_id: confidence}
    """
    try:
        from deepface import DeepFace
        import cv2
    except ImportError:
        return {}

    recognized = {}
    model = getattr(settings, 'FACE_RECOGNITION_MODEL', 'VGG-Face')
    metric = getattr(settings, 'FACE_RECOGNITION_DISTANCE', 'cosine')

    try:
        # Detect all faces in the capture
        face_objs = DeepFace.extract_faces(
            img_path=capture_image_path,
            enforce_detection=False
        )
    except Exception:
        return {}

    for face_obj in face_objs:
        face_img = face_obj.get('face')
        if face_img is None:
            continue

        # Save face crop to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            import cv2
            face_bgr = (face_img * 255).astype(np.uint8)
            face_bgr = cv2.cvtColor(face_bgr, cv2.COLOR_RGB2BGR)
            cv2.imwrite(tmp.name, face_bgr)
            tmp_path = tmp.name

        # Match this face against all students
        for student in students_queryset:
            if not student.photo or not student.face_enrolled:
                continue
            if student.id in recognized:
                continue

            db_path = os.path.join(settings.MEDIA_ROOT, str(student.photo))
            if not os.path.exists(db_path):
                continue

            try:
                res = DeepFace.verify(
                    img1_path=tmp_path,
                    img2_path=db_path,
                    model_name=model,
                    distance_metric=metric,
                    enforce_detection=False
                )
                if res['verified']:
                    recognized[student.id] = round((1 - res['distance']) * 100, 1)
            except Exception:
                continue

        os.unlink(tmp_path)

    return recognized


def verify_single_student(capture_path, student):
    """Verify a single student's face."""
    try:
        from deepface import DeepFace
    except ImportError:
        return False, 0

    if not student.photo or not student.face_enrolled:
        return False, 0

    db_path = os.path.join(settings.MEDIA_ROOT, str(student.photo))
    if not os.path.exists(db_path):
        return False, 0

    model = getattr(settings, 'FACE_RECOGNITION_MODEL', 'VGG-Face')
    metric = getattr(settings, 'FACE_RECOGNITION_DISTANCE', 'cosine')

    try:
        result = DeepFace.verify(
            img1_path=capture_path,
            img2_path=db_path,
            model_name=model,
            distance_metric=metric,
            enforce_detection=False
        )
        confidence = round((1 - result['distance']) * 100, 1)
        return result['verified'], confidence
    except Exception:
        return False, 0
