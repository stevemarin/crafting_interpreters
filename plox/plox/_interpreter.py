from typing import Final, TYPE_CHECKING

from plox._errors import LoxRuntimeError
from plox._environment import Environment

if TYPE_CHECKING:
    from plox._stmt import Stmt
    from plox._expr import Expr


class Interpreter:
    def __init__(self) -> None:
        from plox._callable import Clock
        clock = Clock()

        self.globals: Final[Environment] = Environment()
        self.globals.define("clock", clock)
        self.environment: Environment = self.globals
        self.locals: dict[Expr, int] = {}

    def resolve(self, expr: "Expr", depth: int):
        self.locals[expr] = depth

    @staticmethod
    def interpret(statements: list["Stmt"]):
        from plox.lox import Lox

        try:
            for statement in statements:
                statement.evaluate()
        except LoxRuntimeError as error:
            Lox.runtime_error(error)


interpreter: Interpreter = Interpreter()
