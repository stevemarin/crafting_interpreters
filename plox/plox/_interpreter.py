
from typing import Final, TYPE_CHECKING

from plox._errors import LoxRuntimeError
from plox._environment import Environment

if TYPE_CHECKING:
    from plox._stmt import Stmt
    from plox._expr import Expr

class Interpreter:
    def __init__(self) -> None:
        self.globals: Final[Environment] = Environment()
        self.locals: dict[Expr, int] = {}

        from plox._callable import Clock
        self.globals.define("clock", Clock)

        self.environment: Environment = self.globals

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