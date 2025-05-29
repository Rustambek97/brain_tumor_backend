from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import cv2
import numpy as np
import requests
import base64
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

UPLOAD_DIR = "./Server/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROK_API_TOKEN = "YOUR_GROK_TOKEN"  # Вставьте ваш токен Grok
GROK_API_URL = "https://api.grok.x.ai/v1/chat/completions"

def analyze_with_grok(image_path):
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        prompt = f"Это base64 МРТ-снимка мозга: {img_b64}. Есть ли на нём признаки опухоли? Ответь максимально подробно."
        headers = {
            "Authorization": f"Bearer {GROK_API_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-1",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(GROK_API_URL, headers=headers, json=data)
        if response.status_code != 200:
            return None
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return None

def highlight_blobs(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    kernel = np.ones((7, 7), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)
    min_area = 2000
    mask = np.zeros_like(gray)
    suspicious_found = False
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > min_area:
            x, y, w, h, area = stats[i]
            if x > 20 and y > 20 and x + w < gray.shape[1] - 20 and y + h < gray.shape[0] - 20:
                mask[labels == i] = 255
                suspicious_found = True
    img_result = img.copy()
    img_result[mask > 0] = [0, 0, 255]
    return img_result, suspicious_found

@app.post("/analyze/")
async def analyze_image(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = cv2.imread(file_location)
    if img is None:
        os.remove(file_location)
        raise HTTPException(status_code=400, detail="Не удалось прочитать изображение")
    img_with_filter, suspicious_found = highlight_blobs(img)
    _, buffer_img = cv2.imencode('.png', img_with_filter)
    img_b64 = base64.b64encode(buffer_img).decode("utf-8")

    if suspicious_found:
        verdict = "Обнаружены подозрительные области. Рекомендуется консультация врача."
    else:
        verdict = "Подозрительных областей не обнаружено."

    os.remove(file_location)

    return JSONResponse({
        "verdict": verdict,
        "image_base64": img_b64
    }) 