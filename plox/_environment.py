
from typing import Any, Self

from plox._errors import LoxRuntimeError
from plox._token import Token

class Environment:
    def __init__(self, enclosing: Self | None = None):
        self.values: dict[str, Any] = {}
        self.enclosing = enclosing
    
    def __repr__(self) -> str:
        return f"(environment {self.values})"
    
    def define(self, name: str, value: Any):
        self.values[name] = value
    
    def ancestor(self, distance: int) -> "Environment":
        environment: Environment | None = self
        for _ in range(distance):
            if environment is None:
                raise RuntimeError("Enclosing environment is nil")
            else:
                environment = environment.enclosing

        if environment is None:
            raise RuntimeError("Environment is nil")

        return environment
    
    def get_at(self, distance: int, name: str) -> Any:
        return self.ancestor(distance).values.get(name)
    
    def assign_at(self, distance: int, name: Token, value: Any):
        self.ancestor(distance).values[name.lexeme] = value

    def get(self, name: Token):
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        elif self.enclosing is not None:
            return self.enclosing.get(name)
        else:
            raise LoxRuntimeError(name, f"Undefined variable: '{name.lexeme}'.")
    
    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return None
        elif self.enclosing is not None:
            self.enclosing.assign(name, value)
            return None
        else:
            raise LoxRuntimeError(name, f"Undefined variable: {name.lexeme}.")