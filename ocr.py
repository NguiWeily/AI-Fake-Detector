
from utils.frame_extractor import extract_frames
from detectors.image_detector import detect_fake_image

def detect_fake_video(path):
    frames = extract_frames(path)

    results = []
    suspicious = 0

    for frame in frames:
        result = detect_fake_image(frame)
        results.append(result)

        if result["edge_score"] > 25:
            suspicious += 1

    probability = suspicious / len(results) if results else 0

    return {
        "frames_checked": len(results),
        "suspicious_frames": suspicious,
        "fake_probability": probability
    }
