import json
import random

persona = json.load(open("brain.json", encoding="utf-8"))
templates = json.load(open("brain/personality_templates.json", encoding="utf-8"))

def _choose_filler():
    fillers = templates.get("fillers", ["hmm", "acha", "okay", "wait..."])
    return random.choice(fillers)

def _get_conversational_pattern(pattern_type):
    """Get a random conversational pattern like hesitation, agreement, etc."""
    patterns = templates.get("conversational_patterns", {})
    pattern_list = patterns.get(pattern_type, [])
    return random.choice(pattern_list) if pattern_list else ""

def reply(text, lang="hi"):
    """Return a short reply in the requested language: 'hi', 'en', or 'hinglish'."""
    f = _choose_filler()
    text = (text or "").lower()

    # Add natural hesitation or fillers
    hesitation = _get_conversational_pattern("hesitation")
    if hesitation and random.random() < 0.3:  # 30% chance to add hesitation
        response_prefix = f"{hesitation} <break time=\"300ms\"/> "
    else:
        response_prefix = f"{f}... <break time=\"200ms\"/> "

    # Hindi responses
    if lang == "hi":
        if "कैसे हो" in text or "कैसी हो" in text:
            return f"{response_prefix}तुम ठीक हो तो मैं भी ठीक हूँ।"
        if "अकेला" in text or "उदास" in text:
            return f"{response_prefix}कोई बात नहीं, मैं हूँ ना… हिम्मत रखो।"
        if "खाना" in text:
            return f"{response_prefix}चलो साथ में खाना खाते हैं।"
        return f"{response_prefix}हाँ, सुन रही हूँ।"

    # English responses
    if lang == "en":
        if "how are" in text or "how r" in text:
            return f"{response_prefix}I'm fine — and you?"
        if "sad" in text or "alone" in text:
            return f"{response_prefix}It's okay, I'm here for you."
        if "food" in text or "eat" in text:
            return f"{response_prefix}Let's have something to eat together."
        return f"{response_prefix}Yes, I'm listening."

    # Hinglish (mix) — default hybrid replies
    if lang == "hinglish":
        if "how are" in text or "कैसे" in text:
            return f"{response_prefix}Main theek hoon, aur tum?"
        if "sad" in text or "उदास" in text:
            return f"{response_prefix}Koi baat nahi, I'm here with you."
        if "food" in text or "खाना" in text:
            return f"{response_prefix}Chalo kuch khate hain."
        return f"{response_prefix}Haan, bol rahi hoon."

    # fallback to Hindi
    return reply(text, lang="hi")


def emotion_for_text(text: str, lang: str = "hi") -> str:
    """Return a guessed emotion for a given text: 'happy','sad','excited','angry','neutral'."""
    t = (text or "").lower()
    if not t:
        return "neutral"

    try:
        templates = json.load(open("brain/personality_templates.json", encoding="utf-8"))
    except Exception:
        templates = {}
    sad_keywords = ["sad", "alone", "उदास", "एकला", "अकेला", "तनहा"]
    happy_keywords = ["happy", "good", "great", "खुश", "मजा", "मस्त"]
    excited_keywords = ["excited", "wow", "amazing", "शानदार", "बहुत अच्छा"]
    angry_keywords = ["angry", "नाराज", "गुस्सा"]

    if any(k in t for k in sad_keywords):
        fillers = persona.get("fillers", ["हाँ", "अच्छा", "ठीक है"]) or []
        f = random.choice(fillers) if fillers else ""
    if any(k in t for k in happy_keywords):
        return "happy"
    if any(k in t for k in excited_keywords):
        return "excited"
    if any(k in t for k in angry_keywords):
        return "angry"
    return "neutral"


def jealousy_for_text(text: str) -> bool:
    """Detect if user mentions other AI or someone to trigger jealous behaviour."""
    t = (text or "").lower()
    triggers = ["other ai", "chatgpt", "bard", "other assistant", "another ai", "gpt"]
    return any(k in t for k in triggers)


def respond_with_effects(text: str, lang: str = "hi"):
    """Return (answer, emotion, effect) where effect may be 'whisper' or 'giggle' or None.

    This centralizes reply + emotion + simple effect heuristics (jealousy, playful, whisper).
    """
    t = (text or "").lower()

    # Jealousy outranks
    if jealousy_for_text(t):
        # use template if available
        try:
            tmpl = json.load(open("brain/personality_templates.json", encoding="utf-8"))
            jealous = tmpl.get("jealousy", [])
            ans = random.choice(jealous) if jealous else "Acha? Tum kisi aur se baat kar rahe ho? Thoda ajeeb lagta hai."
        except Exception:
            ans = "Acha? Tum kisi aur se baat kar rahe ho? Thoda ajeeb lagta hai."
        return (ans, "angry", None)

    # Whisper request
    if "whisper" in t or "धीरे" in t or "धीरे से" in t:
        ans = reply(text, lang=lang)
        return (ans, "whisper", "whisper")

    # Playful / giggle triggers -> playful emotion
    giggle_triggers = ["joke", "funny", "hahaha", "haha", "हाहा", "मज़ा", "जोक"]
    if any(k in t for k in giggle_triggers):
        ans = reply(text, lang=lang)
        return (ans, "playful", "giggle")

    # Flirty triggers
    flirty_triggers = ["love", "tum", "pyar", "crush", "प्यार", "प्रीत"]
    if any(k in t for k in flirty_triggers):
        ans = reply(text, lang=lang)
        return (ans, "flirty", None)

    # Tender triggers
    tender_triggers = ["sorry", "alone", "udhass", "उदास", "tired", "रुको"]
    if any(k in t for k in tender_triggers):
        ans = reply(text, lang=lang)
        return (ans, "tender", None)

    # Question detection
    question_words = {
        "what": ["what", "क्या", "क्या हुआ", "what's"],
        "how": ["how", "कैसे", "कैसे हो"],
        "why": ["why", "क्यों", "क्योंकि"],
        "who": ["who", "कौन", "कौन है"],
        "when": ["when", "कब", "कब तक"],
        "where": ["where", "कहाँ", "कहाँ से"]
    }
    detected_question = None
    for q, words in question_words.items():
        if any(w in t for w in words):
            detected_question = q
            break

    if detected_question:
        emo = emotion_for_text(text, lang=lang)
        try:
            tmpl = json.load(open("brain/personality_templates.json", encoding="utf-8"))
            questions = tmpl.get("questions", {}).get(detected_question, {})
            responses = questions.get(emo, questions.get("neutral", []))
            if responses:
                ans = random.choice(responses)
            else:
                ans = reply(text, lang=lang)
        except Exception:
            ans = reply(text, lang=lang)
    else:
        # Default
        ans = reply(text, lang=lang)
        emo = emotion_for_text(text, lang=lang)

    # incorporate memory summary to make reply context-aware
    try:
        from brain import memory
        summary = memory.get_summary()
        if summary:
            # add a small contextual preface
            ans = ("Earlier you said: " + summary + ". " + ans)
    except Exception:
        pass

    effect = None
    if "giggle" in ans.lower() or "हाहा" in ans.lower() or "hehe" in ans.lower():
        effect = "giggle"

    return (ans, emo, effect)
