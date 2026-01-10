import time
import vosk
import sounddevice as sd
import json

model = vosk.Model("vosk-model-small-hi-0.22")
recognizer = vosk.KaldiRecognizer(model, 16000)

def listen(timeout=6):
    """Listen for speech up to `timeout` seconds and return recognized text.

    Returns empty string on timeout or if nothing recognized.
    """
    print("🎤 Lyra is listening...")
    start = time.time()
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1) as stream:
        while True:
            if time.time() - start > timeout:
                print("🔇 Listening timed out")
                return ""

            try:
                data, overflow = stream.read(4000)
            except Exception as e:
                print(f"⚠️ Audio read error: {e}")
                return ""

            if overflow:
                print("⚠️ Input overflow detected")

            # Convert to bytes if needed
            if isinstance(data, bytes):
                chunk = data
            else:
                try:
                    chunk = data.tobytes()
                except Exception:
                    # Fallback: make bytes from buffer
                    chunk = bytes(data)

            if recognizer.AcceptWaveform(chunk):
                try:
                    result = json.loads(recognizer.Result())
                except Exception:
                    result = {}
                text = result.get("text", "")
                if text:
                    print(f"👂 You said: {text}")
                    return text
            # otherwise continue until timeout or a full result is returned
