from textwrap import dedent
from typing import TYPE_CHECKING

from plox._token import Token
from plox._interpreter import Interpreter, interpreter
from plox._stmt import FunctionType, ClassType

if TYPE_CHECKING:
    from plox._expr import Expr


class Scope:
    def __init__(self) -> None:
        self._: dict[str, bool] = {}

    def __getitem__(self, name: str) -> bool:
        return self._[name]

    def __setitem__(self, name: str, value: bool) -> None:
        self._[name] = value

    def __contains__(self, value: str) -> bool:
        return True if value in self._ else False

    def __repr__(self) -> str:
        return dedent(
            f"""(Scope with: {",".join([k + "=" + str(v) 
            for k, v in self._.items()])})"""
        )


class Resolver:
    def __init__(self, interpreter: Interpreter) -> None:
        self.interpreter = interpreter
        self.scopes: list[Scope] = []
        self.current_function: FunctionType = FunctionType.NONE
        self.current_class: ClassType = ClassType.NONE

    def begin_scope(self) -> None:
        self.scopes.append(Scope())

    def end_scope(self) -> None:
        _ = self.scopes.pop()

    def declare(self, name: Token) -> None:
        if len(self.scopes) == 0:
            return None
        else:
            if name.lexeme in self.scopes[-1]:
                from plox.lox import Lox

                Lox.error_token(
                    name, "Already a variable with this name in this scope."
                )
            else:
                self.scopes[-1][name.lexeme] = False

    def define(self, name: Token) -> None:
        if len(self.scopes) == 0:
            return None
        self.scopes[-1][name.lexeme] = True

    def resolve_local(self, expr: "Expr", name: Token) -> None:
        for distance, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                interpreter.resolve(expr, len(self.scopes) - 1 - distance)
                return None
