import string
from textwrap import dedent
from typing import Any

from plox._token import Token, TokenType

DIGITS = frozenset(string.digits)
LETTERS = frozenset(string.ascii_letters + "_")


class Scanner:
    __slots__ = ("start", "current", "line", "source", "tokens")

    def __init__(self, source: str) -> None:
        self.start: int = 0
        self.current: int = 0
        self.line: int = 1

        self.source: str = source
        self.tokens: list[Token] = []

    def scan_tokens(self) -> list[Token]:
        while not self.isAtEnd():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))

        return self.tokens

    def scan_token(self) -> None:
        char: str = self.advance()
        match char:
            case "(":
                self.add_token(TokenType.LEFT_PAREN)
            case ")":
                self.add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.add_token(TokenType.LEFT_BRACE)
            case "}":
                self.add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.add_token(TokenType.COMMA)
            case ".":
                self.add_token(TokenType.DOT)
            case "-":
                self.add_token(TokenType.MINUS)
            case "+":
                self.add_token(TokenType.PLUS)
            case ";":
                self.add_token(TokenType.SEMICOLON)
            case "*":
                self.add_token(TokenType.STAR)
            case "!":
                self.add_token(
                    TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG
                )
            case "=":
                self.add_token(
                    TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL
                )
            case "<":
                self.add_token(
                    TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS
                )
            case ">":
                self.add_token(
                    TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER
                )
            case "/":
                if self.match("/"):
                    # comments go to end of line
                    while self.peek() != "\n" and not self.isAtEnd():
                        self.advance()
                else:
                    self.add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
            case '"':
                self.string()
            case _:
                if self.is_digit(char):
                    self.number()
                elif self.is_alpha(char):
                    self.identifier()
                else:
                    from plox.lox import Lox

                    c: str = self.source[self.current - 1]
                    Lox.error(self.line, f"Unexpected character: {c}")

    def identifier(self) -> None:
        while self.is_alpha_numeric(self.peek()):
            self.advance()

        source: str = self.source[self.start : self.current]

        try:
            token_type: TokenType = TokenType(source)
        except ValueError:
            token_type = TokenType.IDENTIFIER

        self.add_token(token_type)

    def string(self) -> None:
        while self.peek() != '"' and not self.isAtEnd():
            if self.peek() == "\n":
                self.line += 1
            self.advance()

        if self.isAtEnd():
            from plox.lox import Lox

            Lox.error(self.line, "Unterminated string")
            return None

        # the closing "
        self.advance()

        value: str = self.source[self.start + 1 : self.current - 1]
        self.add_token(TokenType.STRING, value)

    def is_digit(self, c: str) -> bool:
        return True if c in DIGITS else False

    def is_alpha(self, c: str) -> bool:
        return True if c in LETTERS else False

    def is_alpha_numeric(self, c: str) -> bool:
        return self.is_digit(c) or self.is_alpha(c)

    def number(self) -> None:
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == "." and self.is_digit(self.peek_next()):
            self.advance()

            while self.is_digit(self.peek()):
                self.advance()

        self.add_token(TokenType.NUMBER, float(self.source[self.start : self.current]))

    def match(self, expected: str) -> bool:
        if self.isAtEnd():
            return False
        elif self.source[self.current] != expected:
            return False
        else:
            self.current += 1
            return True

    def peek(self) -> str:
        if self.isAtEnd():
            return "\0"
        else:
            return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        else:
            return self.source[self.current + 1]

    def advance(self) -> str:
        char: str = self.source[self.current : self.current + 1]
        self.current += 1
        return char

    def add_token(self, type: TokenType, literal: Any = None):
        text: str = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, literal, self.line))

    def isAtEnd(self) -> bool:
        return self.current >= len(self.source)


def test_identifiers():
    src = dedent(
        """
        andy formless fo _ _123 _abc ab123
        abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_
    """
    )

    results = [
        "TokenType.IDENTIFIER andy None",
        "TokenType.IDENTIFIER formless None",
        "TokenType.IDENTIFIER fo None",
        "TokenType.IDENTIFIER _ None",
        "TokenType.IDENTIFIER _123 None",
        "TokenType.IDENTIFIER _abc None",
        "TokenType.IDENTIFIER ab123 None",
        "TokenType.IDENTIFIER abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_ None",
        "TokenType.EOF  None",
    ]

    scanner = Scanner(source=src)
    scanner.scan_tokens()
    for token, res in zip(scanner.tokens, results):
        assert str(token) == res


def test_keywords():
    src = dedent(
        """
        and class else false for fun if nil or return super this true var while
    """
    )

    results = [
        "TokenType.AND and None",
        "TokenType.CLASS class None",
        "TokenType.ELSE else None",
        "TokenType.FALSE false None",
        "TokenType.FOR for None",
        "TokenType.FUN fun None",
        "TokenType.IF if None",
        "TokenType.NIL nil None",
        "TokenType.OR or None",
        "TokenType.RETURN return None",
        "TokenType.SUPER super None",
        "TokenType.THIS this None",
        "TokenType.TRUE true None",
        "TokenType.VAR var None",
        "TokenType.WHILE while None",
        "TokenType.EOF  None",
    ]

    scanner = Scanner(source=src)
    scanner.scan_tokens()
    for token, res in zip(scanner.tokens, results):
        assert str(token) == res


def test_numbers():
    src = dedent(
        """
        123
        123.456
        .456
        123.
    """
    )

    results = [
        "TokenType.NUMBER 123 123.0",
        "TokenType.NUMBER 123.456 123.456",
        "TokenType.DOT . None",
        "TokenType.NUMBER 456 456.0",
        "TokenType.NUMBER 123 123.0",
        "TokenType.DOT . None",
        "TokenType.EOF  None",
    ]

    scanner = Scanner(source=src)
    scanner.scan_tokens()
    for token, res in zip(scanner.tokens, results):
        assert str(token) == res


def test_punctuators():
    src = "(){};,+-*!===<=>=!=<>/."

    results = [
        "TokenType.LEFT_PAREN ( None",
        "TokenType.RIGHT_PAREN ) None",
        "TokenType.LEFT_BRACE { None",
        "TokenType.RIGHT_BRACE } None",
        "TokenType.SEMICOLON ; None",
        "TokenType.COMMA , None",
        "TokenType.PLUS + None",
        "TokenType.MINUS - None",
        "TokenType.STAR * None",
        "TokenType.BANG_EQUAL != None",
        "TokenType.EQUAL_EQUAL == None",
        "TokenType.LESS_EQUAL <= None",
        "TokenType.GREATER_EQUAL >= None",
        "TokenType.BANG_EQUAL != None",
        "TokenType.LESS < None",
        "TokenType.GREATER > None",
        "TokenType.SLASH / None",
        "TokenType.DOT . None",
        "TokenType.EOF  None",
    ]

    scanner = Scanner(source=src)
    scanner.scan_tokens()
    for token, res in zip(scanner.tokens, results):
        assert str(token) == res


def test_strings():
    src = dedent(
        """
    ""
    "string"
    """
    )

    results = [
        'TokenType.STRING "" ',
        'TokenType.STRING "string" string',
        "TokenType.EOF  None",
    ]

    scanner = Scanner(source=src)
    scanner.scan_tokens()
    for token, res in zip(scanner.tokens, results):
        assert str(token) == res


def test_whitespace():
    src = dedent(
        """
        space    tabs				newlines




        end
    """
    )

    results = [
        "TokenType.IDENTIFIER space None",
        "TokenType.IDENTIFIER tabs None",
        "TokenType.IDENTIFIER newlines None",
        "TokenType.IDENTIFIER end None",
        "TokenType.EOF  None",
    ]

    scanner = Scanner(source=src)
    scanner.scan_tokens()
    for token, res in zip(scanner.tokens, results):
        assert str(token) == res
