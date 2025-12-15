import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
import threading
import winsound
import time
import requests

# ---------------- CONFIG ----------------
SAMPLE_RATE = 16000
CHANNELS = 1
KEYWORDS = ["help", "police", "save me", "help me", "emergency"]

SIREN_FILE = "siren.wav"

BOT_TOKEN = "8059364109:AAF6FMKpTJBFdJ6Wh8b86SVMnQCm2k5KYh8"
CHAT_ID = "1268317249"
# ----------------------------------------

# Load Vosk Model
print("Loading model...")
model = Model("model")
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

def send_telegram_alert(keyword):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    message = f"""
🚨 STREET GUARDIAN ALERT 🚨
Keyword Detected: {keyword.upper()}
Time: {timestamp}
Location: (Simulated)
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)
        print("Telegram alert sent ✔️", response.text)
    except Exception as e:
        print("Telegram sending error:", e)

def play_siren():
    try:
        winsound.PlaySound(SIREN_FILE, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print("Siren error:", e)

def callback(indata, frames, time_data, status):
    if status:
        print("Status:", status)

    raw = indata.tobytes()

    if recognizer.AcceptWaveform(raw):
        result = recognizer.Result()
        text = json.loads(result).get("text", "").lower()

        if text:
            print("Recognized:", text)

            for kw in KEYWORDS:
                if kw in text:
                    print(f"\n🚨 ALERT TRIGGERED — {kw.upper()} 🚨\n")
                    threading.Thread(target=play_siren, daemon=True).start()
                    threading.Thread(target=send_telegram_alert, args=(kw,), daemon=True).start()

    else:
        partial = json.loads(recognizer.PartialResult()).get("partial", "").lower()

        if partial:
            print("Partial:", partial)

            for kw in KEYWORDS:
                if kw in partial:
                    print(f"\n🚨 PARTIAL ALERT — {kw.upper()} 🚨\n")
                    threading.Thread(target=play_siren, daemon=True).start()
                    threading.Thread(target=send_telegram_alert, args=(kw,), daemon=True).start()

print("Starting ALERT system (Ctrl+C to stop)...")
with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                    channels=CHANNELS, callback=callback):
    print("Say any emergency word...")
    while True:
        sd.sleep(1000)
