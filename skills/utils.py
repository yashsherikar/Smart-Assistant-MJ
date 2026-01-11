import time
from datetime import datetime


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calc(expression: str):
    """Safe-ish calculator for basic arithmetic. Rejects letters.

    Note: keep simple to avoid code injection.
    """
    allowed = "0123456789+-*/(). %"
    if any(c.isalpha() for c in expression):
        raise ValueError("Invalid characters in expression")
    expr = ''.join(c for c in expression if c in allowed)
    return eval(expr)


def debounce(seconds=0.2):
    time.sleep(seconds)
