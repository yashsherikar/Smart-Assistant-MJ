# Simple Devanagari -> Latin transliteration (approximate, ASCII-friendly)
VOWELS = {
    'अ':'a','आ':'aa','इ':'i','ई':'ii','उ':'u','ऊ':'uu',
    'ए':'e','ऐ':'ai','ओ':'o','औ':'au','ऋ':'ri','अं':'an'
}

MATRA = {
    'ा':'a','ि':'i','ी':'ii','ु':'u','ू':'uu','े':'e','ै':'ai','ो':'o','ौ':'au','ृ':'ri'
}

CONSONANTS = {
    'क':'k','ख':'kh','ग':'g','घ':'gh','ङ':'ng',
    'च':'ch','छ':'chh','ज':'j','झ':'jh','ञ':'ny',
    'ट':'t','ठ':'th','ड':'d','ढ':'dh','ण':'n',
    'त':'t','थ':'th','द':'d','ध':'dh','न':'n',
    'प':'p','फ':'ph','ब':'b','भ':'bh','म':'m',
    'य':'y','र':'r','ल':'l','व':'v',
    'श':'sh','ष':'sh','स':'s','ह':'h',
}

SIGNS = {
    'ं':'n','ः':'h','ँ':'n','्':''
}

def transliterate(text: str) -> str:
    if not text:
        return ""
    out = []
    i = 0
    L = len(text)
    while i < L:
        ch = text[i]
        # space / punctuation passthrough
        if ch.isspace() or ch.isascii() and ch.isprintable() and not ('\u0900' <= ch <= '\u097F'):
            out.append(ch)
            i += 1
            continue

        # independent vowel
        if ch in VOWELS:
            out.append(VOWELS[ch])
            i += 1
            continue

        # consonant
        if ch in CONSONANTS:
            base = CONSONANTS[ch]
            next_ch = text[i+1] if i+1 < L else ''
            # virama: no inherent vowel
            if next_ch == '्':
                out.append(base)
                i += 2
                continue
            # dependent vowel mark
            if next_ch in MATRA:
                out.append(base + MATRA[next_ch])
                i += 2
                continue
            # default inherent 'a'
            out.append(base + 'a')
            i += 1
            continue

        # matra or sign alone
        if ch in MATRA:
            out.append(MATRA[ch])
            i += 1
            continue
        if ch in SIGNS:
            out.append(SIGNS[ch])
            i += 1
            continue

        # fallback: pass through character
        out.append(ch)
        i += 1

    return ''.join(out)
