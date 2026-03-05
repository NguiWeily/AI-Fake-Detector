
from fastapi import FastAPI, UploadFile, File
import shutil, os

from detectors.text_detector import detect_fake_text
from detectors.image_detector import detect_fake_image
from detectors.video_detector import detect_fake_video

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Fake Media Detector API running"}

@app.post("/detect-text")
async def detect_text(text: str):
    result = detect_fake_text(text)
    return {"analysis": result}

@app.post("/detect-image")
async def detect_image(file: UploadFile = File(...)):
    path = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = detect_fake_image(path)
    return {"analysis": result}

@app.post("/detect-video")
async def detect_video(file: UploadFile = File(...)):
    path = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result = detect_fake_video(path)
    return {"analysis": result}
