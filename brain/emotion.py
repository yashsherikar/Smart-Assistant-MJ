def detect_emotion(text, hour):
    text = text.lower()
    if hour >= 22 or hour <= 5:
        return "late_night"
    if any(w in text for w in ["sad", "tired", "upset", "low"]):
        return "sad"
    return "normal"
