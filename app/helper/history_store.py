from collections import defaultdict, deque
import os
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", 20))
HISTORY = defaultdict(lambda: deque(maxlen=HISTORY_LIMIT))

def add_history(token: str, question: str, answer: str):
    HISTORY[token].append({
        "question": question,
        "answer": answer
    })

def get_history(token: str):
    return list(HISTORY[token])