
import pytesseract
import cv2

def extract_text_from_image(path):
    try:
        img = cv2.imread(path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except:
        return ""
