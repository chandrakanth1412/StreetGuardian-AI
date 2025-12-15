# speech_test.py  — corrected
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

# -------- CONFIG --------
SAMPLE_RATE = 16000
CHANNELS = 1
# ------------------------

print("Loading model...")
model = Model("model")
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

# (Optional) set a specific device index if you have many devices.
# Uncomment and set the index from your earlier device list (e.g., 1 or 9).
# sd.default.device = 1

def callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    # indata is a NumPy array when using InputStream; convert to bytes:
    try:
        raw_bytes = indata.tobytes()
    except Exception:
        # fallback if it's already bytes/memoryview
        raw_bytes = bytes(indata)

    # Pass bytes to recognizer
    if recognizer.AcceptWaveform(raw_bytes):
        result = recognizer.Result()
        text = json.loads(result).get("text", "")
        if text:
            print("Recognized:", text)
    else:
        partial = recognizer.PartialResult()
        partial_text = json.loads(partial).get("partial", "")
        if partial_text:
            print("Partial:", partial_text)

print("Starting microphone stream (press Ctrl+C to stop)...")
with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                    channels=CHANNELS, callback=callback):
    print("Speak something...")
    try:
        while True:
            sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nStopped by user")
