import asyncio
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import random
from xml.sax.saxutils import escape
from brain.transliterate import transliterate
import json
import numpy as np
import edge_tts
import re
def add_breathing_pauses(text):
    """Add breathing pauses to make speech more human-like."""
    # Add pauses after punctuation marks
    import re

    # Replace periods, commas, etc. with pause markers
    text = re.sub(r'\.', '. <break time="300ms"/>', text)
    text = re.sub(r',', ', <break time="200ms"/>', text)
    text = re.sub(r'!', '! <break time="400ms"/>', text)
    text = re.sub(r'\?', '? <break time="400ms"/>', text)

    # Add subtle pauses between sentences
    text = re.sub(r'(?<=[.!?])\s+', ' <break time="150ms"/> ', text)

    return text

def add_breathing_sounds(audio_data, samplerate):
    """Add subtle breathing sounds and pauses to make speech more human-like."""
    try:
        import numpy as np

        # Create breathing sound
        breath_duration = 0.4  # 400ms breath
        breath_samples = int(breath_duration * samplerate)
        breath_sound = np.random.normal(0, 0.008, breath_samples).astype(np.float32)

        # Apply envelope
        fade_samples = int(0.15 * samplerate)
        envelope = np.ones(breath_samples)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        breath_sound *= envelope

        # Add pauses at sentence boundaries (look for amplitude drops)
        breathing_audio = audio_data.copy()

        # Find quiet segments (potential sentence breaks)
        window_size = int(0.8 * samplerate)  # 800ms windows
        threshold = 0.015
        min_distance = int(2 * samplerate)  # Minimum 2 seconds between breaths

        insert_positions = []
        last_insert = -min_distance

        for i in range(window_size, len(audio_data) - window_size, window_size // 2):
            window = audio_data[i:i + window_size]
            if np.max(np.abs(window)) < threshold and (i - last_insert) > min_distance:
                # Insert breathing sound
                insert_pos = i + window_size // 2
                if insert_pos + len(breath_sound) < len(breathing_audio):
                    breathing_audio[insert_pos:insert_pos + len(breath_sound)] += breath_sound * 0.25
                    last_insert = insert_pos
                    insert_positions.append(insert_pos)

        # Limit to 2-3 breathing sounds per utterance
        if len(insert_positions) > 3:
            # Keep only the most natural positions
            keep_positions = insert_positions[::len(insert_positions)//3][:3]
            # Reset audio and add only selected breaths
            breathing_audio = audio_data.copy()
            for pos in keep_positions:
                if pos + len(breath_sound) < len(breathing_audio):
                    breathing_audio[pos:pos + len(breath_sound)] += breath_sound * 0.25

        return breathing_audio

    except Exception as e:
        print(f"Breathing effect failed: {e}")
        return audio_data

def create_emotional_laugh(samplerate, emotion):
    """Create different types of laughs based on emotion."""
    try:
        duration = random.uniform(0.5, 1.5)  # Random duration
        samples = int(duration * samplerate)

        if emotion == "happy":
            # Joyful, high-pitched laugh
            t = np.linspace(0, duration, samples)
            laugh = np.sin(2 * np.pi * 250 * t * (1 + 0.5 * np.sin(2 * np.pi * 6 * t)))
            laugh *= np.exp(-t * 1.5)  # Decay

        elif emotion == "playful":
            # Light, teasing laugh
            t = np.linspace(0, duration, samples)
            laugh = np.sin(2 * np.pi * 300 * t * (1 + 0.3 * np.sin(2 * np.pi * 8 * t)))
            laugh *= np.exp(-t * 2.0)

        elif emotion == "flirty":
            # Soft, seductive laugh
            t = np.linspace(0, duration, samples)
            laugh = np.sin(2 * np.pi * 220 * t * (1 + 0.2 * np.sin(2 * np.pi * 4 * t)))
            laugh *= np.exp(-t * 1.0)

        elif emotion == "sarcastic":
            # Short, mocking laugh
            t = np.linspace(0, duration * 0.7, samples)
            laugh = np.sin(2 * np.pi * 180 * t * (1 + 0.4 * np.sin(2 * np.pi * 10 * t)))
            laugh *= np.exp(-t * 3.0)

        else:
            # Default laugh
            t = np.linspace(0, duration, samples)
            laugh = np.sin(2 * np.pi * 200 * t * (1 + 0.3 * np.sin(2 * np.pi * 5 * t)))
            laugh *= np.exp(-t * 2.0)

        # Add some breathiness
        noise = np.random.normal(0, 0.02, samples)
        laugh += noise

        # Apply envelope
        fade_samples = int(0.1 * samplerate)
        envelope = np.ones(samples)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        laugh *= envelope

        return laugh.astype(np.float32) * 0.2

    except Exception as e:
        print(f"Emotional laugh creation failed: {e}")
        return np.array([], dtype=np.float32)

def add_emotional_laughter(audio_data, samplerate, emotion):
    """Add emotional laughter to the end of sentences."""
    try:
        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["neutral"])

        if emotion in ["happy", "playful", "flirty", "excited"] and random.random() < 0.6:  # 60% chance
            laugh = create_emotional_laugh(samplerate, emotion)
            if len(laugh) > 0:
                pause_samples = int(0.15 * samplerate)  # 150ms pause
                pause = np.zeros(pause_samples, dtype=np.float32)
                return np.concatenate([audio_data, pause, laugh])

        return audio_data

    except Exception as e:
        print(f"Emotional laughter failed: {e}")
        return audio_data

def add_giggle_effect(audio_data, samplerate):
    """Add a short giggle sound at the end of happy/playful sentences."""
    try:
        # Create a short giggle sound
        giggle_duration = 0.8  # 800ms giggle
        giggle_samples = int(giggle_duration * samplerate)

        # Generate giggle-like sound with varying pitch
        t = np.linspace(0, giggle_duration, giggle_samples)
        giggle_base = np.sin(2 * np.pi * 300 * t) * np.exp(-t * 2)  # Decaying sine wave

        # Add pitch variations for natural giggle
        pitch_mod = 1 + 0.3 * np.sin(2 * np.pi * 8 * t)  # 8 Hz modulation
        giggle_sound = giggle_base * pitch_mod

        # Add some noise for realism
        noise = np.random.normal(0, 0.05, giggle_samples)
        giggle_sound += noise

        # Apply envelope
        fade_samples = int(0.1 * samplerate)
        envelope = np.ones(giggle_samples)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        giggle_sound *= envelope

        giggle_sound = giggle_sound.astype(np.float32)

        # Insert giggle at the end with a small pause
        pause_samples = int(0.2 * samplerate)  # 200ms pause
        pause = np.zeros(pause_samples, dtype=np.float32)

        return np.concatenate([audio_data, pause, giggle_sound * 0.3])

    except Exception as e:
        print(f"Giggle effect failed: {e}")
        return audio_data

def add_sigh_effect(audio_data, samplerate):
    """Add a sighing sound for sad/tender emotions."""
    try:
        # Create a sighing sound
        sigh_duration = 1.2  # 1.2 seconds
        sigh_samples = int(sigh_duration * samplerate)

        # Generate sigh-like sound (falling pitch)
        t = np.linspace(0, sigh_duration, sigh_samples)
        start_freq = 200
        end_freq = 80
        freq = start_freq - (start_freq - end_freq) * (t / sigh_duration)
        sigh_sound = np.sin(2 * np.pi * freq * t) * np.exp(-t * 0.8)

        # Add breathy quality with noise
        noise = np.random.normal(0, 0.03, sigh_samples)
        sigh_sound += noise

        # Apply envelope (slow attack, slow decay)
        attack_samples = int(0.3 * samplerate)
        decay_samples = int(0.4 * samplerate)
        envelope = np.ones(sigh_samples)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
        sigh_sound *= envelope

        sigh_sound = sigh_sound.astype(np.float32)

        # Insert sigh at the end
        pause_samples = int(0.3 * samplerate)  # 300ms pause
        pause = np.zeros(pause_samples, dtype=np.float32)

        return np.concatenate([audio_data, pause, sigh_sound * 0.25])

    except Exception as e:
        print(f"Sigh effect failed: {e}")
        return audio_data

def apply_emotional_modifications(audio_data, samplerate, emotion):
    """Apply pitch shifting, speed changes, and volume adjustments for emotions."""
    try:
        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["neutral"])

        # Apply volume boost
        if params["volume_boost"] != 1.0:
            audio_data = audio_data * params["volume_boost"]

        # Apply pitch shifting
        if params["pitch_shift"] != 0.0:
            audio_data = shift_pitch(audio_data, samplerate, params["pitch_shift"])

        # Apply speed changes
        if params["speed_factor"] != 1.0:
            audio_data = change_speed(audio_data, params["speed_factor"])

        return audio_data

    except Exception as e:
        print(f"Emotional modification failed: {e}")
        return audio_data

def shift_pitch(audio_data, samplerate, semitones):
    """Shift pitch by given semitones."""
    try:
        # Simple pitch shifting using resampling
        factor = 2 ** (semitones / 12.0)
        new_length = int(len(audio_data) / factor)
        indices = np.arange(new_length) * factor
        return np.interp(indices, np.arange(len(audio_data)), audio_data).astype(np.float32)
    except Exception as e:
        print(f"Pitch shift failed: {e}")
        return audio_data

def change_speed(audio_data, speed_factor):
    """Change playback speed."""
    try:
        new_length = int(len(audio_data) / speed_factor)
        indices = np.arange(new_length) * speed_factor
        return np.interp(indices, np.arange(len(audio_data)), audio_data).astype(np.float32)
    except Exception as e:
        print(f"Speed change failed: {e}")
        return audio_data

def add_emotional_text_modifiers(text, emotion):
    """Add emotional text modifiers and expressions."""
    try:
        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["neutral"])
        modifiers = params["text_modifiers"]

        if not modifiers:
            return text

        # Randomly add emotional modifiers
        if random.random() < 0.3:  # 30% chance
            modifier = random.choice(modifiers)
            if modifier in ["!", "!!!", "?"]:
                text = text.rstrip(".!?") + modifier
            elif modifier in ["...", "😊", "😢", "😄", "😠", "😘", "😍", "😜", "😲", "😕", "😏"]:
                text += " " + modifier
            else:
                # Insert modifier randomly in the text
                words = text.split()
                if len(words) > 1:
                    insert_pos = random.randint(0, len(words)-1)
                    words.insert(insert_pos, modifier)
                    text = " ".join(words)

        return text

    except Exception as e:
        print(f"Text modifier failed: {e}")
        return text

def add_emotional_sounds(audio_data, samplerate, emotion):
    """Add emotional sound effects like giggling, sighing, laughter, etc."""
    try:
        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["neutral"])

        # Add giggling for happy/playful/flirty emotions
        if params["add_giggle"]:
            audio_data = add_giggle_effect(audio_data, samplerate)

        # Add sighing for sad/tender/confused emotions
        if params["add_sigh"]:
            audio_data = add_sigh_effect(audio_data, samplerate)

        # Add emotional laughter
        audio_data = add_emotional_laughter(audio_data, samplerate, emotion)

        return audio_data
    except Exception as e:
        print(f"Emotional sound effect failed: {e}")
        return audio_data

        # Add pauses at sentence boundaries (look for amplitude drops)
        breathing_audio = audio_data.copy()

        # Find quiet segments (potential sentence breaks)
        window_size = int(0.8 * samplerate)  # 800ms windows
        threshold = 0.015
        min_distance = int(2 * samplerate)  # Minimum 2 seconds between breaths

        insert_positions = []
        last_insert = -min_distance

        for i in range(window_size, len(audio_data) - window_size, window_size // 2):
            window = audio_data[i:i + window_size]
            if np.max(np.abs(window)) < threshold and (i - last_insert) > min_distance:
                # Insert breathing sound
                insert_pos = i + window_size // 2
                if insert_pos + len(breath_sound) < len(breathing_audio):
                    breathing_audio[insert_pos:insert_pos + len(breath_sound)] += breath_sound * 0.25
                    last_insert = insert_pos
                    insert_positions.append(insert_pos)

        # Limit to 2-3 breathing sounds per utterance
        if len(insert_positions) > 3:
            # Keep only the most natural positions
            keep_positions = insert_positions[::len(insert_positions)//3][:3]
            # Reset audio and add only selected breaths
            breathing_audio = audio_data.copy()
            for pos in keep_positions:
                if pos + len(breath_sound) < len(breathing_audio):
                    breathing_audio[pos:pos + len(breath_sound)] += breath_sound * 0.25

        return breathing_audio

    except Exception as e:
        print(f"Breathing effect failed: {e}")
        return audio_data

# read console echo setting from brain.json
try:
    _cfg = json.load(open("brain.json", encoding="utf-8"))
    CONSOLE_ECHO = bool(_cfg.get("console_echo", False))
except Exception:
    CONSOLE_ECHO = False

VOICE_MAP = {
    "en": "en-US-JennyNeural",  # Female voice for English
    "hi": "hi-IN-SwaraNeural",  # Indian female voice for Hindi
    "hinglish": "hi-IN-SwaraNeural"  # Indian female voice for Hinglish
}

# Enhanced emotion parameters for Coqui TTS with audio processing
EMOTION_PARAMS = {
    "neutral": {
        "pitch_shift": 0.0,      # semitones
        "speed_factor": 1.0,     # 1.0 = normal speed
        "volume_boost": 1.0,     # volume multiplier
        "add_giggle": False,
        "add_sigh": False,
        "text_modifiers": [],
        "voice_style": "neutral"
    },
    "happy": {
        "pitch_shift": 1.5,
        "speed_factor": 1.08,
        "volume_boost": 1.1,
        "add_giggle": True,
        "add_sigh": False,
        "text_modifiers": ["!", "😊", "yay"],
        "voice_style": "cheerful"
    },
    "sad": {
        "pitch_shift": -1.0,
        "speed_factor": 0.92,
        "volume_boost": 0.9,
        "add_giggle": False,
        "add_sigh": True,
        "text_modifiers": ["...", "😢", "oh"],
        "voice_style": "calm"
    },
    "excited": {
        "pitch_shift": 2.0,
        "speed_factor": 1.15,
        "volume_boost": 1.2,
        "add_giggle": True,
        "add_sigh": False,
        "text_modifiers": ["!!!", "😄", "wow", "amazing"],
        "voice_style": "excited"
    },
    "angry": {
        "pitch_shift": -0.5,
        "speed_factor": 1.1,
        "volume_boost": 1.3,
        "add_giggle": False,
        "add_sigh": False,
        "text_modifiers": ["!", "grrr", "😠"],
        "voice_style": "angry"
    },
    "flirty": {
        "pitch_shift": 1.2,
        "speed_factor": 0.95,
        "volume_boost": 1.05,
        "add_giggle": True,
        "add_sigh": False,
        "text_modifiers": ["😘", "darling", "sweetie", "mmm"],
        "voice_style": "seductive"
    },
    "tender": {
        "pitch_shift": -0.3,
        "speed_factor": 0.88,
        "volume_boost": 0.95,
        "add_giggle": False,
        "add_sigh": True,
        "text_modifiers": ["...", "dear", "sweetheart", "😍"],
        "voice_style": "gentle"
    },
    "playful": {
        "pitch_shift": 1.8,
        "speed_factor": 1.12,
        "volume_boost": 1.15,
        "add_giggle": True,
        "add_sigh": False,
        "text_modifiers": ["😜", "teehee", "hehe", "playful"],
        "voice_style": "playful"
    },
    "whisper": {
        "pitch_shift": -2.0,
        "speed_factor": 0.85,
        "volume_boost": 0.4,
        "add_giggle": False,
        "add_sigh": False,
        "text_modifiers": ["...", "shh"],
        "voice_style": "whispering"
    },
    "surprised": {
        "pitch_shift": 2.5,
        "speed_factor": 1.2,
        "volume_boost": 1.25,
        "add_giggle": False,
        "add_sigh": False,
        "text_modifiers": ["!!!", "wow", "oh my", "😲"],
        "voice_style": "surprised"
    },
    "confused": {
        "pitch_shift": 0.5,
        "speed_factor": 0.9,
        "volume_boost": 0.95,
        "add_giggle": False,
        "add_sigh": True,
        "text_modifiers": ["?", "umm", "huh", "😕"],
        "voice_style": "confused"
    },
    "sarcastic": {
        "pitch_shift": -0.8,
        "speed_factor": 0.95,
        "volume_boost": 1.1,
        "add_giggle": False,
        "add_sigh": False,
        "text_modifiers": ["sure", "right", "oh please", "😏"],
        "voice_style": "sarcastic"
    }
}



def create_emotional_ssml(text, voice_name, emotion, effect=None):
    """Create SSML with emotional styling for more natural speech."""
    # Base SSML structure
    ssml_start = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">'
    ssml_end = '</speak>'

    # Voice element
    voice_start = f'<voice name="{voice_name}">'

    # Emotional styling based on emotion (using basic prosody for better compatibility)
    emotion_styles = {
        "happy": '<prosody rate="+8%" pitch="+2Hz" volume="+1dB">',
        "sad": '<prosody rate="-5%" pitch="-1Hz" volume="-2dB">',
        "angry": '<prosody rate="+5%" pitch="+3Hz" volume="+2dB">',
        "excited": '<prosody rate="+12%" pitch="+4Hz" volume="+1dB">',
        "tender": '<prosody rate="-3%" pitch="-2Hz" volume="-1dB">',
        "playful": '<prosody rate="+6%" pitch="+1Hz">',
        "neutral": '<prosody rate="+2%">',
        "flirty": '<prosody rate="+4%" pitch="+1Hz" volume="+0.5dB">'
    }

    style_start = emotion_styles.get(emotion, emotion_styles["neutral"])

    # Apply whisper effect if specified
    if effect == "whisper":
        style_start += '<prosody volume="-8dB">'

    style_end = '</prosody>'
    if effect == "whisper":
        style_end += '</prosody>'

    voice_end = '</voice>'

    # Combine all elements
    full_ssml = f"{ssml_start}{voice_start}{style_start}{text}{style_end}{voice_end}{ssml_end}"

    return full_ssml


async def speak_async(text, lang="hi", emotion="neutral", effect: str = None):
    # Use Edge TTS with NeerjaNeural for Indian female voice
    voice_name = VOICE_MAP.get(lang, VOICE_MAP.get("hi"))

    # For Hindi/hinglish, keep original text (edge-tts supports Hindi)
    if lang in ["hi", "hinglish"]:
        processed_text = text
    else:
        processed_text = text

    # Add emotional text modifiers
    processed_text = add_emotional_text_modifiers(processed_text, emotion)

    # Add emotional sentence variations
    processed_text = add_emotional_sentence_variations(processed_text, emotion)

    # Add breathing pauses using SSML
    processed_text = add_breathing_pauses(processed_text)

    # Create SSML with emotional styling
    ssml = create_emotional_ssml(processed_text, voice_name, emotion, effect)

    # Generate speech using edge-tts
    try:
        communicate = edge_tts.Communicate(ssml, voice_name, input_type="ssml")
    except TypeError:
        # Fallback for older edge-tts versions
        communicate = edge_tts.Communicate(processed_text, voice_name)

    # Save to temporary file and play
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        temp_path = temp_file.name

    try:
        await communicate.save(temp_path)

        # Load and play the audio
        data, samplerate = sf.read(temp_path, dtype='float32')

        # Apply additional breathing sounds if needed
        try:
            data = add_breathing_sounds(data, samplerate)
        except Exception as e:
            print(f"Breathing enhancement failed, using original audio: {e}")

        # Add emotional sound effects
        data = add_emotional_sounds(data, samplerate, emotion)

        # Play the audio
        sd.play(data, samplerate)
        sd.wait()

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except Exception:
            pass

def speak(text, lang="hi", emotion="neutral", effect: str = None):
    display = text or ""
    if CONSOLE_ECHO:
        try:
            if lang in ("hi", "hinglish"):
                tr = transliterate(display)
                print(f"MJ -> (lang={lang}, emotion={emotion}, effect={effect}): {display} | transliteration: {tr}")
            else:
                print(f"MJ -> (lang={lang}, emotion={emotion}, effect={effect}): {display}")
        except Exception:
            print(f"MJ -> (lang={lang}, emotion={emotion}, effect={effect}): {display}")

    try:
        asyncio.run(speak_async(text, lang=lang, emotion=emotion, effect=effect))
    except Exception as e:
        print(f"TTS speak_async error: {e}")
        # Fallback to console output if TTS fails
        if not CONSOLE_ECHO:
            print(f"MJ: {display}")

def play_giggle(lang="hi", emotion="happy"):
    """Synthesize and play emotional giggles/laughs based on emotion type."""
    # Different giggle types based on emotion
    giggle_types = {
        "happy": ["हाहा", "hehe", "haha", "😊"],
        "playful": ["teehee", "hehe", "😜", "giggle"],
        "flirty": ["mmm", "hehe", "😘", "teehee"],
        "excited": ["wow", "haha", "yay", "😄"],
        "tender": ["hehe", "sweet", "😍"],
        "surprised": ["oh my", "wow", "😲", "haha"],
        "sarcastic": ["sure", "right", "hehe"],
        "confused": ["umm", "huh", "😕"]
    }

    # Get appropriate phrases for the emotion
    phrases = giggle_types.get(emotion, giggle_types["happy"])

    # Try to use personality giggle phrases if available
    try:
        import json
        tmpl = json.load(open("brain/personality_templates.json", encoding="utf-8"))
        personality_phrases = tmpl.get("giggle_phrases", [])
        if personality_phrases:
            phrases.extend(personality_phrases)
    except Exception:
        pass

    # speak 2-3 short giggle fragments to sound more natural
    import random
    num_giggles = random.randint(2, 4) if emotion in ["excited", "happy"] else random.randint(1, 2)
    seq = random.sample(phrases, min(num_giggles, len(phrases)))

    # Prefer playing cached giggles if available
    try:
        from .giggle_cache import play_random_giggle
        play_random_giggle(lang=lang)
        return
    except Exception:
        pass

    for p in seq:
        try:
            asyncio.run(speak_async(p, lang=lang, emotion=emotion))
        except Exception:
            pass

def play_emotional_sound(emotion, lang="hi"):
    """Play emotional sound effects based on emotion type."""
    sound_effects = {
        "happy": ["yay!", "woo!", "great!"],
        "sad": ["oh...", "sigh...", "aww..."],
        "surprised": ["wow!", "oh my!", "really?!"],
        "angry": ["grrr!", "humph!", "tch!"],
        "flirty": ["mmm...", "oh darling...", "😘"],
        "tender": ["aww...", "sweet...", "dear..."],
        "confused": ["umm...", "huh?", "what?"],
        "sarcastic": ["oh please...", "sure...", "right..."],
        "excited": ["wow!", "amazing!", "fantastic!"],
        "playful": ["teehee!", "gotcha!", "😜"]
    }

    phrases = sound_effects.get(emotion, ["okay"])
    phrase = random.choice(phrases)

    try:
        asyncio.run(speak_async(phrase, lang=lang, emotion=emotion))
    except Exception as e:
        print(f"Emotional sound failed: {e}")

def add_emotional_sentence_variations(text, emotion):
    """Add emotional sentence variations and fillers."""
    try:
        variations = {
            "happy": [
                lambda t: f"Oh {t}! That's wonderful!",
                lambda t: f"Yay! {t}",
                lambda t: f"I'm so happy! {t}",
                lambda t: f"Great! {t}"
            ],
            "sad": [
                lambda t: f"Oh... {t}",
                lambda t: f"I'm sorry... {t}",
                lambda t: f"Aww... {t}",
                lambda t: f"That's sad... {t}"
            ],
            "flirty": [
                lambda t: f"Oh darling, {t}",
                lambda t: f"Mmm... {t}",
                lambda t: f"You're so sweet... {t}",
                lambda t: f"My dear, {t}"
            ],
            "surprised": [
                lambda t: f"Wow! {t}",
                lambda t: f"Oh my! {t}",
                lambda t: f"Really? {t}",
                lambda t: f"That's amazing! {t}"
            ],
            "angry": [
                lambda t: f"Oh come on! {t}",
                lambda t: f"This is ridiculous! {t}",
                lambda t: f"I'm so mad! {t}",
                lambda t: f"Unbelievable! {t}"
            ],
            "playful": [
                lambda t: f"Hehe! {t}",
                lambda t: f"Gotcha! {t}",
                lambda t: f"Teehee! {t}",
                lambda t: f"You're funny! {t}"
            ],
            "tender": [
                lambda t: f"Aww... {t}",
                lambda t: f"That's so sweet... {t}",
                lambda t: f"My dear... {t}",
                lambda t: f"How lovely... {t}"
            ],
            "confused": [
                lambda t: f"Umm... {t}",
                lambda t: f"I'm confused... {t}",
                lambda t: f"Huh? {t}",
                lambda t: f"What do you mean? {t}"
            ],
            "sarcastic": [
                lambda t: f"Oh sure... {t}",
                lambda t: f"Right... {t}",
                lambda t: f"Oh please... {t}",
                lambda t: f"As if... {t}"
            ]
        }

        if emotion in variations and random.random() < 0.4:  # 40% chance
            variation_func = random.choice(variations[emotion])
            return variation_func(text)

        return text

    except Exception as e:
        print(f"Sentence variation failed: {e}")
        return text
