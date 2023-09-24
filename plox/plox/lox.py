
import sys
import logging
from typing import Final

from plox._scanner import Scanner
from plox._token import Token, TokenType
from plox._parser import Parser
from plox._errors import LoxRuntimeError
from plox._interpreter import Interpreter, interpreter
from plox._resolver import Resolver
from plox._stmt import Stmt

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

class Lox:

    interpreter: Final[Interpreter] = Interpreter()
    had_error: bool = False
    had_runtime_error: bool = False

    @classmethod
    def run_file(cls, filename: str) -> None:
        with open(filename, "r") as fh:
            source: str = fh.read()
        
        cls.run(source)

        if cls.had_error:
            sys.exit(65)
        elif cls.had_runtime_error:
            sys.exit(70)
            
    @classmethod
    def run_prompt(cls) -> None:
        logging.info("Entering Interpreter...")
        logging.info("Press CTRL-D to execute...")
        while True:
            source: str = sys.stdin.read().strip()
            if source == "":
                break
            cls.run(source)
            cls.had_error = False
    
    @classmethod
    def run(cls, source: str) -> None:
        scanner = Scanner(source)
        tokens: list[Token] = scanner.scan_tokens()
        parser: Parser = Parser(tokens)
        statements: list[Stmt] = parser.parse()

        if cls.had_error:
            return
        
        resolver: Resolver = Resolver(interpreter)
        for statement in statements:
            statement.resolve(resolver)

        if cls.had_error:
            return

        cls.interpreter.interpret(statements)
    
    @staticmethod
    def error(line: int, message: str) -> None:
        Lox.report(line, "", message)
    
    @classmethod
    def runtime_error(cls, error: LoxRuntimeError):
        logging.error(error)
        cls.had_runtime_error = True

    @classmethod
    def report(cls, line: int, where: str, message: str) -> None:
        logging.error(f"[line {line}] Errror {where}: {message}")
        cls.had_error = True

    @classmethod
    def error_token(cls, token: Token, message: str) -> None:
        if token.type == TokenType.EOF:
            cls.report(token.line, " at end ", message)
        else:
            cls.report(token.line, f" at '{token.lexeme}' ", message)


def main(filename: str | None = None) -> None:
    if isinstance(filename, str):
            Lox().run_file(filename)
    elif filename is None:
            Lox().run_prompt()
    else:
        logging.error("must pass a filename or nothing")

if __name__ == "__main__":
    try:
        filename: str | None = sys.argv[1]
    except IndexError:
        filename = None
    
    main(filename)