import sounddevice as sd

def test_mic():
    print("\nAvailable audio input devices:\n")
    print(sd.query_devices())

    print("\nNow testing microphone for 3 seconds...")
    duration = 3  # seconds
    fs = 16000    # sample rate

    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # wait until recording is finished

    print("Recording done.")

    # Check if audio was captured
    if recording.any():
        print("Microphone test SUCCESS ✔️")
    else:
        print("Microphone test FAILED ❌ -- No audio captured")

test_mic()
