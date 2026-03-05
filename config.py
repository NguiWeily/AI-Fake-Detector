
import cv2, os

def extract_frames(video_path):

    cap = cv2.VideoCapture(video_path)
    frames = []
    count = 0

    os.makedirs("frames", exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % 30 == 0:
            path = f"frames/frame_{count}.jpg"
            cv2.imwrite(path, frame)
            frames.append(path)

        count += 1

        if count > 150:
            break

    cap.release()
    return frames
