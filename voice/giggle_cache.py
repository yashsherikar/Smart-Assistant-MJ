import os
import json
import random
import asyncio
import edge_tts
import soundfile as sf
import sounddevice as sd
import tempfile

HERE = os.path.dirname(__file__)
GIGGLE_DIR = os.path.join(HERE, "giggles")
TEMPLATES_PATH = os.path.join(HERE, "..", "brain", "personality_templates.json")

os.makedirs(GIGGLE_DIR, exist_ok=True)


def _load_giggle_phrases():
    try:
        tmpl = json.load(open(TEMPLATES_PATH, encoding="utf-8"))
        phrases = tmpl.get("giggle_phrases", ["हाहा", "हेहे", "hehe"])
    except Exception:
        phrases = ["हाहा", "हेहे", "hehe"]
    return phrases


def _paths_for(lang, variants=3):
    phrases = _load_giggle_phrases()
    paths = []
    for i, p in enumerate(phrases):
        vpaths = []
        for v in range(variants):
            name = f"giggle_{lang}_{i}_{v}.wav"
            vpaths.append(os.path.join(GIGGLE_DIR, name))
        paths.append((p, vpaths))
    return paths


def build_giggle_cache(lang='hi', variants=3):
    """Synthesize giggle phrases with small prosody variations to WAV files and cache them."""
    items = _paths_for(lang, variants=variants)
    voice = "hi-IN-NeerjaNeural" if lang in ("hi", "hinglish") else "en-US-JennyNeural"
    for phrase, vpaths in items:
        for vi, path in enumerate(vpaths):
            if os.path.exists(path):
                continue
            # create a small SSML variance for each variant when possible
            rate = f"{5 + vi*3:+d}%"
            pitch = f"{1 + vi:+d}Hz"
            ssml = f'<speak><voice name="{voice}"><prosody rate="{rate}" pitch="{pitch}">{phrase}</prosody></voice></speak>'
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
                tmp = tf.name
            try:
                # try SSML mode first
                try:
                    c = edge_tts.Communicate(ssml, voice, input_type="ssml")
                except TypeError:
                    c = edge_tts.Communicate(phrase, voice)
                asyncio.run(c.save(tmp))
                data, sr = sf.read(tmp, dtype='float32')
                sf.write(path, data, sr)
            except Exception:
                try:
                    os.remove(tmp)
                except Exception:
                    pass


def play_random_giggle(lang='hi'):
    """Play a cached giggle WAV chosen at random. If cache missing, build it."""
    phrases, paths = _paths_for(lang)
    # expand the list of candidate paths from structure
    candidate_paths = []
    items = _paths_for(lang)
    for phrase, vpaths in items:
        candidate_paths.extend(vpaths)
    existing = [p for p in candidate_paths if os.path.exists(p)]
    if not existing:
        try:
            build_giggle_cache(lang=lang)
            existing = [p for p in candidate_paths if os.path.exists(p)]
        except Exception:
            existing = []
    if not existing:
        # fallback: speak short laugh via edge-tts
        try:
            c = edge_tts.Communicate('हाहा' if lang in ("hi","hinglish") else 'hehe', 'hi-IN-NeerjaNeural' if lang in ("hi","hinglish") else 'en-US-JennyNeural')
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tf:
                tmp = tf.name
            asyncio.run(c.save(tmp))
            data, sr = sf.read(tmp, dtype='float32')
            sd.play(data, sr)
            sd.wait()
            try:
                os.remove(tmp)
            except Exception:
                pass
            return
        except Exception:
            return

    path = random.choice(existing)
    try:
        data, sr = sf.read(path, dtype='float32')
        sd.play(data, sr)
        sd.wait()
    except Exception:
        pass
