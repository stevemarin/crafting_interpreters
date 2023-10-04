from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

import plox._stmt as _stmt
from plox._environment import Environment
from plox._errors import FakeReturnError
from plox._token import Token

if TYPE_CHECKING:
    from plox._interpreter import Interpreter


class LoxCallable(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, declaration: "None | _stmt.Function" = None) -> None:
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def arity(self) -> int:
        ...

    @abstractmethod
    def call(
        self, current_interpreter: "Interpreter", arguments: list[Any] = []
    ) -> Any:
        ...


class Clock(LoxCallable):
    def __init__(self):
        pass

    def __repr__(self):
        return "<native fn>"    

    def arity(self) -> int:
        return 0

    def call(self):
        from time import time
        return time()


class LoxFunction(LoxCallable):
    def __init__(
        self, declaration: "_stmt.Function", closure: Environment, is_initializer: bool
    ) -> None:
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def __repr__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(
        self, current_interpreter: "Interpreter", arguments: list[Any] = []
    ) -> Any:
        # setup the environment for the function call
        environment: Environment = Environment(self.closure)
        for parameter, argument in zip(self.declaration.params, arguments):
            environment.define(parameter.lexeme, argument)

        block: _stmt.Block = _stmt.Block(self.declaration.body)
        try:
            block.execute_block(current_interpreter, environment)
        except FakeReturnError as r:
            if self.is_initializer:
                return self.closure.get_at(0, "this")
            else:
                return r.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")

        return None

    def bind(self, instance: "LoxInstance") -> "LoxFunction":
        environment: Environment = Environment(self.closure)
        environment.define("this", instance)
        return LoxFunction(self.declaration, environment, self.is_initializer)


class LoxClass(LoxCallable):
    def __init__(
        self, name: str, superclass: "LoxClass", methods: dict[str, LoxFunction]
    ) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def __repr__(self) -> str:
        return self.name

    def arity(self) -> int:
        initializer: LoxFunction | None = self.find_method("init")
        if initializer is not None:
            return initializer.arity()
        else:
            return 0

    def call(self, interpreter: "Interpreter", arguments: list[Any] = []) -> Any:
        instance: LoxInstance = LoxInstance(self)

        initializer: LoxFunction | None = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def find_method(self, name: str) -> LoxFunction | None:
        if name in self.methods:
            return self.methods[name]
        elif self.superclass is not None:
            return self.superclass.find_method(name)
        else:
            return None


class LoxInstance:
    def __init__(self, _class: LoxClass) -> None:
        self._class = _class
        self.fields: dict[str, Any] = {}

    def __repr__(self) -> str:
        return f"(instance {self._class.name})"

    def get(self, name: Token) -> Any:
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method: None | LoxFunction = self._class.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise RuntimeError(name, f"Undefined property {name.lexeme}.")

    def set(self, name: Token, value: Any) -> None:
        self.fields[name.lexeme] = value
