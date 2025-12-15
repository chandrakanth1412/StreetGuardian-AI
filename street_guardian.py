#!/usr/bin/env python3
"""
streetguardian_main.py

Full prototype:
- Vosk speech detection (English)
- On emergency keyword:
    - capture snapshot from webcam (index 0)
    - upload snapshot to imgbb
    - send Telegram photo + caption
    - send FCM data-only high-priority message (topic police_zone_a)
    - play looping siren on laptop until manual stop
"""

import os
import sys
import time
import json
import base64
import threading
import requests
from datetime import datetime
import platform

# audio + STT
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# webcam
import cv2
import numpy as np

# firebase (server)
import firebase_admin
from firebase_admin import credentials, messaging

# ---------------- CONFIG ----------------
CAMERA_INDEX = 0   # you said cv2.VideoCapture(0)
VOSK_MODEL_PATH = "model"   # english model folder
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCKSIZE = 8000

# Telegram
TELEGRAM_BOT_TOKEN = "add_bot_token"
TELEGRAM_CHAT_ID = "add_chat_id"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# imgbb
IMGBB_API_KEY = "Imgbb-api_key"
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

# Firebase
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
FCM_TOPIC = "police_zone_a"

# Siren file - change if needed
SIREN_WAV = "siren.wav"  # put a valid .wav file in the same folder

# Emergency keywords (English demo)
EMERGENCY_KEYWORDS = [
    "help", "help me", "save me", "save", "police",
    "thief", "emergency", "problem", "attack",
    "ambulance", "108", "fire","100"
]

# snapshot filename
SNAPSHOT_FILE = "snapshot.jpg"

# JPEG compression config
SNAPSHOT_WIDTH = 480
JPEG_QUALITY = 60

# ----------------------------------------

# Global flags
siren_playing = False
siren_lock = threading.Lock()

# ------------------ Utilities ------------------

def init_firebase():
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print("❌ Missing serviceAccountKey.json in folder.")
        return False
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    try:
        firebase_admin.initialize_app(cred)
        print("✅ Firebase admin initialized.")
        return True
    except Exception as e:
        print("❌ Firebase init failed:", e)
        return False

def upload_to_imgbb(image_path):
    """Upload a local image to imgbb, return public url or ''"""
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("❌ Could not open snapshot:", e)
        return ""

    payload = {
        "key": IMGBB_API_KEY,
        "image": img_b64
    }
    try:
        r = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=30)
        res = r.json()
        if res.get("success"):
            url = res["data"]["url"]
            print("✅ Uploaded to imgbb:", url)
            return url
        else:
            print("❌ imgbb response error:", res)
            return ""
    except Exception as e:
        print("❌ imgbb upload failed:", e)
        return ""

def send_telegram_photo(image_url, keyword, location, timestamp):
    caption = f"<b>ALERT</b>\nKeyword: {keyword}\nLocation: {location}\nTime: {timestamp}"
    try:
        resp = requests.post(f"{TELEGRAM_API}/sendPhoto",
                             data={"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": caption, "parse_mode":"HTML"},
                             timeout=15)
        j = resp.json()
        if j.get("ok"):
            print("✅ Telegram photo sent")
            return True
        else:
            print("❌ Telegram photo failed:", j)
            # fallback to text
            text = caption + ("\n\nImage: " + image_url if image_url else "")
            resp2 = requests.post(f"{TELEGRAM_API}/sendMessage",
                                  data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode":"HTML"}, timeout=10)
            print("Fallback sendMessage response:", resp2.json())
            return False
    except Exception as e:
        print("❌ Telegram send exception:", e)
        return False

def send_fcm_data(keyword, image_url, location, timestamp):
    if not firebase_admin._apps:
        print("❌ Firebase not initialized. Skipping FCM.")
        return False
    data_payload = {
        "keyword": keyword,
        "image": image_url,
        "location": location,
        "time": timestamp,
        "type": "street_guardian_alert"
    }
    message = messaging.Message(
        data=data_payload,
        topic=FCM_TOPIC,
        android=messaging.AndroidConfig(priority="high")
    )
    try:
        resp = messaging.send(message)
        print("✅ FCM sent:", resp)
        return True
    except Exception as e:
        print("❌ FCM send failed:", e)
        return False

def capture_snapshot(save_path=SNAPSHOT_FILE, cam_index=CAMERA_INDEX):
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW if platform.system()=="Windows" else 0)
    if not cap.isOpened():
        print("❌ Cannot open webcam (index {})".format(cam_index))
        return False
    # warm camera
    for _ in range(3):
        ret, frame = cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        print("❌ Snapshot capture failed")
        return False

    h, w = frame.shape[:2]
    if w > SNAPSHOT_WIDTH:
        scale = SNAPSHOT_WIDTH / float(w)
        frame = cv2.resize(frame, (SNAPSHOT_WIDTH, int(h * scale)), interpolation=cv2.INTER_AREA)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    success, enc = cv2.imencode('.jpg', frame, encode_param)
    if not success:
        print("❌ JPEG encode failed")
        return False
    with open(save_path, "wb") as f:
        f.write(enc.tobytes())
    print("✅ Snapshot saved:", save_path)
    return True

# ------------------ Siren control ------------------

def _winsound_loop(path):
    # Windows winsound loop
    import winsound
    # loop async
    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)

def _winsound_stop():
    import winsound
    winsound.PlaySound(None, winsound.SND_PURGE)

def _simpleaudio_loop(path):
    try:
        import simpleaudio as sa
    except Exception:
        print("simpleaudio not available")
        return
    wave_obj = sa.WaveObject.from_wave_file(path)
    play_obj = None
    while siren_playing:
        play_obj = wave_obj.play()
        play_obj.wait_done()

def start_siren_thread(path=SIREN_WAV):
    global siren_playing
    with siren_lock:
        if siren_playing:
            return
        siren_playing = True

    def _runner():
        print("🔊 Siren starting (type 'stop' + Enter to stop)...")
        try:
            if platform.system() == "Windows":
                _winsound_loop(path)
                # keep running until flag cleared
                while siren_playing:
                    time.sleep(0.5)
                _winsound_stop()
            else:
                # use simpleaudio if available
                try:
                    import simpleaudio as sa
                    wave_obj = sa.WaveObject.from_wave_file(path)
                    while siren_playing:
                        play_obj = wave_obj.play()
                        play_obj.wait_done()
                except Exception as e:
                    print("No simple audio playback available:", e)
                    print("Siren not played.")
        except Exception as e:
            print("Siren error:", e)
        print("🔕 Siren stopped.")
    t = threading.Thread(target=_runner, daemon=True)
    t.start()

def stop_siren():
    global siren_playing
    with siren_lock:
        if not siren_playing:
            return
        siren_playing = False
    # winsound stop handled in thread
    print("Stopping siren...")

def input_monitor():
    # thread to listen for 'stop' command from user
    while True:
        try:
            cmd = input().strip().lower()
            if cmd in ("stop", "s", "exit", "quit"):
                stop_siren()
                print("User requested stop. Siren stopped.")
            # allow other commands later
        except EOFError:
            break
        except Exception:
            break

# ------------------ Vosk STT ------------------

print("Loading Vosk model... (this may take a few seconds)")
if not os.path.exists(VOSK_MODEL_PATH):
    print("❌ Vosk model folder not found:", VOSK_MODEL_PATH)
    sys.exit(1)

model = Model(VOSK_MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)
print("✅ Vosk model loaded.")

# initialize firebase
firebase_ok = init_firebase()

# start input monitor thread (to stop siren manually)
threading.Thread(target=input_monitor, daemon=True).start()

# listening callback
def contains_keyword(text):
    t = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in t:
            return kw
    return None

def handle_emergency(detected_keyword):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n🚨🚨 ALERT TRIGGERED — Keyword Detected: {detected_keyword.upper()} at {ts} 🚨🚨")

    # 1) capture snapshot
    ok = capture_snapshot(SNAPSHOT_FILE, CAMERA_INDEX)
    img_url = ""
    if ok:
        # 2) upload to imgbb
        img_url = upload_to_imgbb(SNAPSHOT_FILE)

    # 3) send telegram
    try:
        send_telegram_photo(img_url, detected_keyword.upper(), "Police Zone A", ts)
    except Exception as e:
        print("Telegram error:", e)

    # 4) send FCM (data-only high-priority)
    try:
        send_fcm_data(detected_keyword.upper(), img_url, "Police Zone A", ts)
    except Exception as e:
        print("FCM error:", e)

    # 5) start siren
    if os.path.exists(SIREN_WAV):
        start_siren_thread(SIREN_WAV)
    else:
        print("⚠ Siren file not found:", SIREN_WAV, " — put a WAV file named siren.wav or update SIREN_WAV variable.")

# audio callback
def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio status:", status)
    raw = indata.tobytes()
    try:
        if recognizer.AcceptWaveform(raw):
            res = json.loads(recognizer.Result())
            text = res.get("text", "").strip()
            if text:
                print("> Recognized:", text)
                kw = contains_keyword(text)
                if kw:
                    handle_emergency(kw)
        else:
            # optional: partial results
            partial = json.loads(recognizer.PartialResult()).get("partial", "")
            if partial:
                print("Partial:", partial)
    except Exception as e:
        print("Audio processing error:", e)

# ------------------ MAIN ------------------

def main():
    print("\n🎧 StreetGuardian MAIN starting. Speak emergency words to trigger alert.")
    print("Keywords:", ", ".join(EMERGENCY_KEYWORDS))
    print("Type 'stop' + Enter in this console to stop the siren.")
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=BLOCKSIZE,
                            dtype='int16', channels=CHANNELS, callback=audio_callback):
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print("Fatal error:", e)

if __name__ == "__main__":
    main()

