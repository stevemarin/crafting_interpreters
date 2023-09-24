from textwrap import dedent
from typing import Any

from plox._token import Token

class LoxRuntimeError(RuntimeError):
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message
    
    def __repr__(self):
        return dedent(f"""{self.message}
                          [line {self.token.line}]""")

class FakeReturnError(RuntimeError):
    def __init__(self, value: Any) -> None:
        super().__init__()
        self.value = value
    
    def __repr__(self) -> str:
        return f"(FakeReturnError = {self.value})"

def is_truthy(obj: Any):
    # False and None are False
    # everthing else is True
    if obj is None:
        return False
    if isinstance(obj, bool):
        return bool(obj)
    else:
        return True

def stringify(obj: Any):
    if obj is None:
        return "nil"
    elif isinstance(obj, float):
        text = str(obj)
        if text.endswith(".0"):
            text = text[0: len(text) - 2]

        return text

    return str(obj)
