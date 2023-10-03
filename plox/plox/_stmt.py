from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from textwrap import dedent
from typing import Any, TYPE_CHECKING

from plox._token import Token
from plox._environment import Environment
from plox._errors import FakeReturnError, LoxRuntimeError, stringify, is_truthy
from plox._callable import LoxClass, LoxFunction

if TYPE_CHECKING:
    from plox._resolver import Resolver
    from plox._interpreter import Interpreter
    from plox._expr import Expr, Variable as VariableExpr


class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    INITIALIZER = auto()
    METHOD = auto()


class ClassType(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Stmt(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self) -> None:
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def evaluate(self) -> None:
        ...

    @abstractmethod
    def resolve(self, resolver: "Resolver") -> None:
        ...


class Print(Stmt):
    def __init__(self, expression: "Expr") -> None:
        self.expression = expression

    def __repr__(self) -> str:
        return f"(print {self.expression})"

    def evaluate(self) -> None:
        value: Any = self.expression.evaluate()
        print(stringify(value))
        return None

    def resolve(self, resolver: "Resolver") -> None:
        self.expression.resolve(resolver)
        return None


class Expression(Stmt):
    def __init__(self, expression: "Expr") -> None:
        self.expression = expression

    def __repr__(self) -> str:
        return f"(expr-eval {self.expression})"

    def evaluate(self) -> None:
        self.expression.evaluate()
        return None

    def resolve(self, resolver: "Resolver") -> None:
        self.expression.resolve(resolver)


class Variable(Stmt):
    def __init__(self, name: Token, initializer: "None | Expr") -> None:
        self.name = name
        self.initializer = initializer

    def __repr__(self) -> str:
        return f"(var {self.name} {self.initializer})"

    def evaluate(self) -> None:
        if self.initializer is not None:
            value: Any = self.initializer.evaluate()
        else:
            value = None

        from plox._interpreter import interpreter

        interpreter.environment.define(self.name.lexeme, value)

        return None

    def resolve(self, resolver: "Resolver") -> None:
        resolver.declare(self.name)
        if self.initializer is not None:
            self.initializer.resolve(resolver)
        resolver.define(self.name)
        return None


class Block(Stmt):
    def __init__(self, statements: list[Stmt]) -> None:
        self.statements = statements

    def __repr__(self) -> str:
        joiner: str = "\n\t"
        return f"(block {joiner.join([str(s) for s in self.statements])})"

    def evaluate(self) -> None:
        from plox._interpreter import interpreter

        self.execute_block(interpreter, Environment(enclosing=interpreter.environment))

    def execute_block(
        self, interpreter: "Interpreter", environment: Environment
    ) -> None:
        previous: Environment = interpreter.environment

        try:
            interpreter.environment = environment
            for statement in self.statements:
                statement.evaluate()

        finally:
            interpreter.environment = previous

    def resolve(self, resolver: "Resolver") -> None:
        resolver.begin_scope()
        for statement in self.statements:
            statement.resolve(resolver)
        resolver.end_scope()


class If(Stmt):
    def __init__(self, condition: "Expr", then_branch: Stmt, else_branch: Stmt | None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __repr__(self):
        return dedent(
            f"""(if: 
                             then: {self.then_branch}
                             else: {self.else_branch})
                       """
        )

    def evaluate(self) -> None:
        if is_truthy(self.condition.evaluate()):
            self.then_branch.evaluate()
        elif self.else_branch is not None:
            self.else_branch.evaluate()

    def resolve(self, resolver: "Resolver") -> None:
        self.condition.resolve(resolver)
        self.then_branch.resolve(resolver)
        if self.else_branch is not None:
            self.else_branch.resolve(resolver)


class While(Stmt):
    def __init__(self, condition: "Expr", body: Stmt):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return dedent(
            f"""(while {self.condition}
                            {self.body}
                          )"""
        )

    def evaluate(self) -> None:
        while is_truthy(self.condition.evaluate()):
            self.body.evaluate()

    def resolve(self, resolver: "Resolver") -> None:
        self.condition.resolve(resolver)
        self.body.resolve(resolver)


class Function(Stmt):
    def __init__(self, name: Token, params: list[Token], body: list[Stmt]):
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        return dedent(f"""(fn {self.name} {self.params})""")

    def evaluate(self) -> None:
        from plox._callable import LoxFunction
        from plox._interpreter import interpreter

        f: LoxFunction = LoxFunction(self, interpreter.environment, False)

        environment = interpreter.environment
        environment.define(self.name.lexeme, f)

    def resolve(self, resolver: "Resolver") -> None:
        resolver.declare(self.name)
        resolver.define(self.name)
        self.resolve_function(resolver, FunctionType.FUNCTION)

    def resolve_function(
        self, resolver: "Resolver", function_type: FunctionType
    ) -> None:
        enclosing_function: FunctionType = resolver.current_function
        resolver.current_function = function_type

        resolver.begin_scope()
        for param in self.params:
            resolver.declare(param)
            resolver.define(param)
        for statement in self.body:
            statement.resolve(resolver)
        resolver.end_scope()

        resolver.current_function = enclosing_function


class Return(Stmt):
    def __init__(self, keyword: Token, value: "Expr | None") -> None:
        self.keyword = keyword
        self.value = value

    def __repr__(self) -> str:
        return f"(return {self.keyword.lexeme}={self.value})"

    def evaluate(self) -> None:
        if self.value is not None:
            value = self.value.evaluate()
        else:
            value = None

        raise FakeReturnError(value)

    def resolve(self, resolver: "Resolver") -> None:
        from plox.lox import Lox

        if resolver.current_function == FunctionType.NONE:
            Lox.error_token(self.keyword, "Can't return from outside function.")

        if self.value is not None:
            if resolver.current_function == FunctionType.INITIALIZER:
                Lox.error_token(
                    self.keyword, "Can't return a value from an initializer."
                )
            self.value.resolve(resolver)


class Class(Stmt):
    def __init__(
        self, name: Token, superclass: "VariableExpr | None", methods: list[Function]
    ) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def __repr__(self) -> str:
        return f"(class {self.name.lexeme})"

    def evaluate(self) -> None:
        # TODO double check this
        superclass: Any = None
        if self.superclass is not None:
            superclass = self.superclass.evaluate()
            if not isinstance(superclass, LoxClass):
                message = f"Superclass must be a class: '{self.superclass.name.lexeme}'."
                raise LoxRuntimeError(f"{message} [line {self.superclass.name.line}]")

        from plox._interpreter import interpreter

        interpreter.environment.define(self.name.lexeme, None)

        if superclass is not None:
            interpreter.environment = Environment(interpreter.environment)
            interpreter.environment.define("super", superclass)

        methods: dict[str, LoxFunction] = {}
        for method in self.methods:
            function: LoxFunction = LoxFunction(
                method, interpreter.environment, method.name.lexeme == "init"
            )
            methods[method.name.lexeme] = function

        _class: LoxClass = LoxClass(self.name.lexeme, superclass, methods)

        if superclass is not None:
            assert interpreter.environment.enclosing is not None
            interpreter.environment = interpreter.environment.enclosing

        interpreter.environment.assign(self.name, _class)

    def resolve(self, resolver: "Resolver") -> None:
        enclosing_class: ClassType = resolver.current_class
        resolver.current_class = ClassType.CLASS

        resolver.declare(self.name)
        resolver.define(self.name)

        if (
            self.superclass is not None
            and self.name.lexeme == self.superclass.name.lexeme
        ):
            from plox.lox import Lox

            Lox.error_token(self.superclass.name, "A class cannot inherit from itself.")

        if self.superclass is not None:
            resolver.current_class = ClassType.SUBCLASS
            self.superclass.resolve(resolver)

        if self.superclass is not None:
            resolver.begin_scope()
            resolver.scopes[-1]["super"] = True

        resolver.begin_scope()
        resolver.scopes[-1]["this"] = True

        for method in self.methods:
            declaration: FunctionType = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            method.resolve_function(resolver, declaration)

        resolver.end_scope()

        if self.superclass is not None:
            resolver.end_scope()

        resolver.current_class = enclosing_class
