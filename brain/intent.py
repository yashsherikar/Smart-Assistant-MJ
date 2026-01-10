def detect_intent(text):
    text = text.lower()
    # PC automation
    if "open chrome" in text or "open google" in text:
        return "open_chrome"
    if "open notepad" in text or "open notepad++" in text:
        return "open_notepad"
    if "search file" in text or "find file" in text or "search for" in text:
        return "search_file"
    if "shutdown" in text or "shut down" in text:
        return "shutdown"
    if "play music" in text or "play song" in text:
        return "play_music"

    # simple chat
    if "how are you" in text or "कैसी" in text or "कैसे" in text:
        return "chat"

    return "chat"
