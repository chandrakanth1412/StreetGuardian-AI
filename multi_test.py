import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000
CHANNELS = 1

# -------------------------------
# LOAD ALL MODELS (EN, HI, TE)
# -------------------------------
MODEL_PATHS = {
    "english": "models/english",
    "hindi": "models/hindi",
    "telugu": "models/telugu"
}

print("\nLoading models...\n")
MODELS = {}
for lang, path in MODEL_PATHS.items():
    try:
        MODELS[lang] = Model(path)
        print(f"✔ Loaded: {lang}")
    except:
        print(f"❌ ERROR loading: {lang}")

# Create recognizers
recognizers = {lang: KaldiRecognizer(model, SAMPLE_RATE) for lang, model in MODELS.items()}

# -------------------------------
# EMERGENCY KEYWORDS COMBINED
# -------------------------------

EMERGENCY_WORDS = [
    # English
    "help", "police", "save me", "help me", "thief", "emergency", "attack", "fire", "ambulance", "108",

    # Hindi
    "madad", "police", "bachao", "chori", "hamla", "aag", "emergency",

    # Telugu
    "saahayam", "sahayam", "kaapadu", "kapadu", "nannu kaapadu", "dongalu", "aapad", "agni",

    # Tamil
    "uthaavi", "kaaval", "kaapathu", "soodam", "thee", "thuṇai",

    # Kannada
    "sahaya", "rakshisi", "police", "agni", "aparadhi", "bedi",

    # Malayalam
    "sahayam", "police", "rakshikkuka", "thee", "apatham",

    # Urdu
    "madad", "police", "bachao", "hamla", "aag"
]

def is_emergency(text):
    for word in EMERGENCY_WORDS:
        if word in text:
            return True, word
    return False, None

# -------------------------------
# MAIN LISTENING LOGIC
# -------------------------------

model_cycle = list(recognizers.keys())
index = 0

print("\n🎤 Multi-language detection started…\n")

def callback(indata, frames, time, status):
    global index
    raw = indata.tobytes()

    lang = model_cycle[index]
    rec = recognizers[lang]

    if rec.AcceptWaveform(raw):
        text = json.loads(rec.Result()).get("text", "").lower()

        if text.strip():
            print(f"> {text}")   # SIMPLE ONE-LINE OUTPUT

            alert, keyword = is_emergency(text)
            if alert:
                print(f"\n🚨 ALERT — '{keyword.upper()}' DETECTED 🚨\n")

    index = (index + 1) % len(model_cycle)

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                    blocksize=8000, callback=callback):
    while True:
        sd.sleep(1000)
