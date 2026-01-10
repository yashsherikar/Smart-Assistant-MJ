from collections import deque
import re
from collections import Counter


class Memory:
    def __init__(self, size=50):
        self.size = size
        self.history = deque(maxlen=size)
        self.mode = 'normal'

    def add_user(self, text: str):
        self.history.append({'who': 'user', 'text': text})

    def add_assistant(self, text: str):
        self.history.append({'who': 'assistant', 'text': text})

    def get_context(self, last_n=6):
        return list(self.history)[-last_n:]

    def get_topics(self, top_n=5):
        # simple keyword extraction from user messages
        texts = [item['text'] for item in self.history if item.get('who') == 'user']
        text = ' '.join(texts).lower()
        # tokenize on non-word
        tokens = re.findall(r"\w+", text)
        stopwords = set(['the', 'is', 'in', 'at', 'on', 'and', 'or', 'a', 'an', 'to', 'for', 'of', 'mein', 'है', 'हूँ','मैं','का','में','क्या'])
        tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
        counts = Counter(tokens)
        most = [w for w, _ in counts.most_common(top_n)]
        return most

    def get_summary(self, max_chars=200):
        # produce a compact summary with topics and recent user utterances
        topics = self.get_topics(top_n=5)
        parts = []
        for item in list(self.history)[-6:]:
            who = item.get('who')
            text = item.get('text', '')
            if who == 'user':
                parts.append(text)
        s = ' | '.join(parts[-5:])
        if topics:
            topic_str = 'Topics: ' + ', '.join(topics) + '. '
        else:
            topic_str = ''
        summary = topic_str + s
        if len(summary) > max_chars:
            return summary[:max_chars-3] + '...'
        return summary


# module-level default memory
_mem = Memory()


def add_user(text: str):
    _mem.add_user(text)


def add_assistant(text: str):
    _mem.add_assistant(text)


def get_context(last_n=6):
    return _mem.get_context(last_n)


def get_summary(max_chars=200):
    return _mem.get_summary(max_chars=max_chars)


def set_mode(mode: str):
    _mem.mode = mode


def get_mode():
    return getattr(_mem, 'mode', 'normal')
