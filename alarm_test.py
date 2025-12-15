import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
import threading
import winsound

# ------------- CONFIG -------------
SAMPLE_RATE = 16000
CHANNELS = 1
KEYWORDS = ["help", "police", "save me", "help me", "emergency","save","thief","108",]
SIREN_FILE = "siren.wav"   # Must be WAV format
# ----------------------------------

print("Loading model...")
model = Model("model")
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

# Siren function (threaded)
def play_siren():
    try:
        winsound.PlaySound(SIREN_FILE, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print("Siren error:", e)

def callback(indata, frames, time, status):
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

    else:
        partial = recognizer.PartialResult()
        ptext = json.loads(partial).get("partial", "").lower()

        if ptext:
            print("Partial:", ptext)

            for kw in KEYWORDS:
                if kw in ptext:
                    print(f"\n🚨 PARTIAL ALERT — {kw.upper()} 🚨\n")
                    threading.Thread(target=play_siren, daemon=True).start()

print("Starting siren test (say: help / police)...")
with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                    channels=CHANNELS, callback=callback):
    print("Speak emergency words...")
    while True:
        sd.sleep(1000)
