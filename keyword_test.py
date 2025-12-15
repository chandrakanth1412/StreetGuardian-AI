import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

# ------- CONFIG -------
SAMPLE_RATE = 16000
CHANNELS = 1
KEYWORDS = ["help", "police", "save me", "help me", "emergency"]
# ----------------------

print("Loading model...")
model = Model("model")
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

def callback(indata, frames, time, status):
    if status:
        print("Status:", status)

    raw = indata.tobytes()

    if recognizer.AcceptWaveform(raw):
        result = recognizer.Result()
        text = json.loads(result).get("text", "").lower()

        if text:
            print("Recognized:", text)

            # Check for emergency words
            for kw in KEYWORDS:
                if kw in text:
                    print("\n🚨🚨 ALERT TRIGGERED — Keyword Detected:", kw.upper(), "🚨🚨\n")
    else:
        partial = recognizer.PartialResult()
        ptext = json.loads(partial).get("partial", "").lower()

        if ptext:
            print("Partial:", ptext)

            # detect partial emergency words
            for kw in KEYWORDS:
                if kw in ptext:
                    print("\n🚨🚨 ALERT TRIGGERED (PARTIAL) —", kw.upper(), "🚨🚨\n")

print("Starting keyword detection (Ctrl+C to stop)...")
with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                    channels=CHANNELS, callback=callback):
    print("Say: help / police / save me / help me")
    while True:
        sd.sleep(1000)
