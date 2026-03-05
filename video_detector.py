
from PIL import Image
import imagehash
import cv2

from utils.ocr import extract_text_from_image
from detectors.text_detector import detect_fake_text

def detect_fake_image(path):
    img = Image.open(path)
    hash_value = imagehash.average_hash(img)

    image_cv = cv2.imread(path)
    edges = cv2.Canny(image_cv,100,200)
    edge_ratio = edges.mean()

    extracted_text = extract_text_from_image(path)

    text_analysis = None
    if extracted_text and len(extracted_text) > 10:
        text_analysis = detect_fake_text(extracted_text)

    return {
        "image_hash": str(hash_value),
        "edge_score": float(edge_ratio),
        "detected_text": extracted_text,
        "text_analysis": text_analysis
    }
