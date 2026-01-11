import json
import random
from voice.stt import listen
from voice.tts import speak
from brain.response import reply, emotion_for_text, jealousy_for_text
from brain.intent import detect_intent
from skills import system as sys_skills
from skills import search as search_skills
from skills import utils as util_skills
from brain.transliterate import transliterate
from brain import memory as memory
import os

cfg = json.load(open("brain.json", encoding="utf-8"))
NAME = cfg.get("name", "MJ")

# List of 10 different greetings
GREETINGS = [
    "Hello sirji, kahaan the? Main yahan intezar kar rahi thi!",
    "Namaste sir, aap kaise hain? Batao kya madad chahiye?",
    "Hi sirji, welcome back! Kya kaam karna hai aaj?",
    "Hello boss, main ready hoon! Kya command denge?",
    "Sirji, aap aa gaye! Batao kya karna hai?",
    "Hey sir, good to see you! What's up?",
    "Namaste sir, aapki seva mein hazir hoon!",
    "Hello sirji, kahaan gum ho gaye the? Main yahan hoon!",
    "Sir, welcome! Kya help chahiye aaj?",
    "Hi there, sirji! Ready for your commands!"
]

def detect_language_from_text(text: str) -> str:
    if not text:
        return cfg.get("language", "hinglish") or "hinglish"  # Changed default from "hi" to "hinglish"
    has_deva = any('\u0900' <= c <= '\u097F' for c in text)
    has_latin = any('a' <= c.lower() <= 'z' for c in text)
    if has_deva and has_latin:
        return "hinglish"
    if has_deva:
        return "hinglish"  # Changed from "hi" to "hinglish"
    return "en"

print(f"💖 {NAME} is online! Say '{NAME}' to wake her up...")
try:
    greeting = random.choice(GREETINGS)
    speak(greeting, lang="hinglish", emotion="happy")
except Exception as e:
    print(f"Greeting TTS Error: {e}")
# build giggle cache in background so first giggle is fast
try:
    import threading
    from voice.giggle_cache import build_giggle_cache
    t = threading.Thread(target=lambda: build_giggle_cache('hi'), daemon=True)
    t.start()
except Exception:
    pass

while True:
    try:
        text = listen()
        if not text:
            continue
        tl = text.lower()
        if NAME.lower() in tl or "एमजे" in tl or "mj" in tl:
            # Acknowledge in the language detected
            lang = detect_language_from_text(tl)
            try:
                if lang == "en":
                    speak("Yes? Speak your command.", lang=lang)
                elif lang == "hinglish":
                    speak("Haan? Kya bolna hai?", lang="hinglish")
                else:
                    speak("Haan? Kya bolna hai?", lang="hinglish")  # Default to Hinglish
            except Exception as e:
                print(f"TTS Error: {e}")
                continue

            command = listen(timeout=10)
            if not command:
                continue
            
            # Process the command
            lang = detect_language_from_text(command)
            # create a Latin-letter (ASCII) transliteration for Hindi/Hinglish inputs
            command_latin = command
            # only print transliteration when console echo is enabled
            try:
                from brain import memory
                cfg_echo = False
                try:
                    import json
                    cfg = json.load(open('brain.json', encoding='utf-8'))
                    cfg_echo = bool(cfg.get('console_echo', False))
                except Exception:
                    cfg_echo = False
                if lang in ("hi", "hinglish") and cfg_echo:
                    command_latin = transliterate(command)
                    print(f"🔤 Transliteration: {command_latin}")
            except Exception:
                pass

            intent = detect_intent(command)

            # set personality mode via voice command: "set personality flirty" or "personality flirty"
            if "personality" in command.lower() or "set personality" in command.lower():
                words = command.lower().split()
                for m in ['flirty', 'normal', 'serious']:
                    if m in words:
                        try:
                            from brain import memory
                            memory.set_mode(m)
                            speak(f"Personality set to {m}.", lang=lang)
                        except Exception:
                            speak(f"Set to {m} mode.", lang=lang)
                        break
                continue

            # add to conversational memory
            try:
                memory.add_user(command)
            except Exception:
                pass

            # Use the new responder to get answer, emotion and optional effect
            ans, emo, effect = None, None, None
            try:
                ans, emo, effect = __import__('brain.response', fromlist=['respond_with_effects']).respond_with_effects(command, lang=lang)
            except Exception:
                ans = reply(command, lang=lang)
                emo = emotion_for_text(command, lang=lang)

            # If an automation intent was detected, perform it instead
            if intent == "open_chrome":
                speak("Opening Chrome.", lang=lang, emotion="neutral")
                sys_skills.open_chrome()
                continue
            if intent == "open_notepad":
                speak("Opening Notepad.", lang=lang, emotion="neutral")
                sys_skills.open_notepad()
                continue
            if intent == "play_music":
                speak("Toggling playback.", lang=lang)
                try:
                    sys_skills.media_play_pause()
                except Exception:
                    pass
                continue
            if intent == "shutdown":
                speak("Do you want to shutdown the PC? Say yes to confirm.", lang=lang)
                confirm = listen(timeout=6)
                if confirm and ("yes" in confirm.lower() or "हाँ" in confirm.lower()):
                    speak("Shutting down now.", lang=lang)
                    os.system("shutdown /s /t 1")
                else:
                    speak("Cancelled.", lang=lang)
                continue

            # direct keyword-based shortcuts (media, volume, clipboard, windows)
            kl = command.lower()
            if "next" in kl and "track" in kl:
                sys_skills.media_next(); speak("Next track.", lang=lang); continue
            if "previous" in kl or "prev" in kl or "last track" in kl:
                sys_skills.media_prev(); speak("Previous track.", lang=lang); continue
            if "volume up" in kl or "increase volume" in kl:
                sys_skills.volume_up(); speak("Volume up.", lang=lang); continue
            if "volume down" in kl or "decrease volume" in kl:
                sys_skills.volume_down(); speak("Volume down.", lang=lang); continue
            if "mute" in kl:
                sys_skills.mute_toggle(); speak("Toggled mute.", lang=lang); continue
            if "copy" in kl and "to clipboard" in kl:
                # expect phrase like "copy <text> to clipboard"
                parts = kl.split("copy",1)[1].replace("to clipboard","").strip()
                if parts:
                    sys_skills.copy_to_clipboard(parts)
                    speak("Copied to clipboard.", lang=lang)
                    continue
            if "paste" in kl and "clipboard" in kl:
                txt = sys_skills.paste_from_clipboard()
                speak(f"Clipboard contains: {txt}", lang=lang)
                continue
            if "switch window" in kl or "alt tab" in kl:
                sys_skills.switch_window_alt_tab(); speak("Switched window.", lang=lang); continue
            if "maximize" in kl:
                sys_skills.maximize_active(); speak("Maximised.", lang=lang); continue
            if "minimize" in kl:
                sys_skills.minimize_active(); speak("Minimised.", lang=lang); continue
            if intent == "search_file":
                # try to extract query (simple)
                q = command.replace("search for", "").replace("search file", "").strip()
                if not q:
                    speak("What file name should I search for?", lang=lang)
                    q = listen(timeout=8)
                root = "."
                results = search_skills.search_files(root, q)
                if results:
                    speak(f"I found {len(results)} files. Showing top results.", lang=lang)
                    for r in results[:3]:
                        speak(r, lang=lang)
                else:
                    speak("No files found.", lang=lang)
                continue

            # If responder suggested an effect, act on it (giggle/whisper)
            if effect == "giggle":
                # play a short giggle and then the answer
                try:
                    from voice.tts import play_giggle
                    play_giggle(lang=lang)
                except Exception:
                    pass

            try:
                speak(ans, lang=lang, emotion=emo, effect=effect)
            except Exception as e:
                print(f"TTS Error in response: {e}")
            try:
                memory.add_assistant(ans)
            except Exception:
                pass
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        continue
