
from abc import ABCMeta, abstractmethod
from typing import Any, TYPE_CHECKING

from plox._errors import LoxRuntimeError, is_truthy
from plox._token import Token, TokenType
from plox._stmt import ClassType

if TYPE_CHECKING:
    from plox._callable import LoxInstance
    from plox._resolver import Resolver

def _lox_eq(left: Any, right: Any):
    if type(left) is not type(right):
        return False
    return left == right
    
class Expr(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self) -> None:
        ...
    
    @abstractmethod
    def __repr__(self) -> str:
        ...
    
    @abstractmethod
    def evaluate(self) -> Any:
        ...

    @abstractmethod
    def resolve(self, resolver: "Resolver") -> None:
        ...

class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right
    
    def __repr__(self) -> str:
        return f"({self.operator.lexeme} {self.left} {self.right})"
    
    def evaluate(self) -> Any:
        left: Any = self.left.evaluate()
        right: Any = self.right.evaluate()

        match self.operator.type:
            case TokenType.GREATER:
                self.check_number_operands(self.operator, left, right)
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                self.check_number_operands(self.operator, left, right)
                return float(left) >= float(right)
            case TokenType.LESS:
                self.check_number_operands(self.operator, left, right)
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                self.check_number_operands(self.operator, left, right)
                return float(left) <= float(right)
            case TokenType.BANG_EQUAL:
                return not _lox_eq(left, right)
            case TokenType.EQUAL_EQUAL:
                return _lox_eq(left, right)
            case TokenType.MINUS:
                self.check_number_operands(self.operator, left, right)
                return float(left) - float(right)
            case TokenType.SLASH:
                self.check_number_operands(self.operator, left, right)
                return float(left) / float(right)
            case TokenType.STAR:
                self.check_number_operands(self.operator, left, right)
                return float(left) * float(right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                elif isinstance(left, str) and isinstance(right, str):
                    return left + right
                else:
                    raise RuntimeError(f"{self.operator} operarands must both " +
                                       f"be strs or numbers - "
                                       f"{type(left)} & {type(right)}")
            case _:
                return None
    
    def is_equal(self, left: Any, right: Any) -> bool:
        if left is None and right is None:
            return True
        elif left is None:
            return False
        else:
            return left == right
    
    def resolve(self, resolver: "Resolver") -> None:
        self.left.resolve(resolver)
        self.right.resolve(resolver)

    
    @staticmethod
    def check_number_operands(operator: Token, left: Any, right: Any) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return
        else:
            raise RuntimeError(f"{operator}: operands {left} " + 
                               f"and {right} must be numbers")


class Grouping(Expr):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression
        
    def __repr__(self) -> str:
        return f"(group {self.expression})"
    
    def evaluate(self) -> Any:
        return self.expression.evaluate()

    def resolve(self, resolver: "Resolver") -> None:
        self.expression.resolve(resolver)


class Literal(Expr):
    def __init__(self, value: Any) -> None:
        self.value = value
    
    def __repr__(self) -> str:
        if self.value is None:
            return "nil"
        else:
            return str(self.value)
    
    def evaluate(self) -> Any:
        return self.value
    
    def resolve(self, resolver: "Resolver") -> None:
        return None


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr) -> None:
        self.operator = operator
        self.right = right
    
    def __repr__(self) -> str:
        return f"({self.operator.lexeme} {self.right})"
    
    def evaluate(self) -> Any:
        right: Any = self.right.evaluate()
        
        if self.operator.type == TokenType.MINUS:
            self.check_number_operand(self.operator, right)
            return -float(right)
        elif self.operator.type == TokenType.BANG:
            return not is_truthy(right)
        else:
            raise LoxRuntimeError(self.operator, "Unexpected unary operator.")

    @staticmethod
    def check_number_operand(operator: Token, operand: Any) -> None:
        if isinstance(operand, float):
            return
        else:
            raise RuntimeError(f"{operator}: operand {operand} must be a number")

    def resolve(self, resolver: "Resolver") -> None:
        self.right.resolve(resolver)

class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name
    
    def __repr__(self):
        return f"(variable {self.name})"
    
    def evaluate(self) -> Any:
        return self.lookup_variable(self.name, self)
    
    def lookup_variable(self, name: Token, expr: Expr) -> Any:
        from plox._interpreter import interpreter
        try:
            distance: int | None = interpreter.locals[expr]
            assert distance is not None
            return interpreter.environment.get_at(distance, name.lexeme)
        except KeyError:
            return interpreter.globals.get(name)
    
    def resolve(self, resolver: "Resolver") -> None:
        if (len(resolver.scopes) > 0 and 
            self.name.lexeme in resolver.scopes[-1] and 
            not resolver.scopes[-1][self.name.lexeme]):
            
            from plox.lox import Lox
            Lox.error_token(self.name, 
                "Can't read local variable in it's own initializer.")
        
        resolver.resolve_local(self, self.name)


class Assign(Expr):
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value
    
    def __repr__(self):
        return f"(assign {self.name.lexeme} {self.value})"
    
    def evaluate(self) -> Any:
        value: Any = self.value.evaluate()

        from plox._interpreter import interpreter
        distance: int | None = interpreter.locals.get(self.value)

        if distance is not None:
            interpreter.environment.assign_at(distance, self.name, value)
        else:
            interpreter.globals.assign(self.name, value)

        return value
    
    def resolve(self, resolver: "Resolver") -> None:
        self.value.resolve(resolver)
        resolver.resolve_local(self, self.name)


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right
    
    def __repr__(self):
        return f"(logical: {self.operator}, {self.left}, {self.right})"
    
    def evaluate(self) -> Any:
        left: Any = self.left.evaluate()

        if self.operator.type == TokenType.OR:
            if is_truthy(self.left):
                return left
        else:
            if not is_truthy(self.left):
                return left
        
        return self.right.evaluate()
    
    def resolve(self, resolver: "Resolver") -> None:
        self.left.resolve(resolver)
        self.right.resolve(resolver)

class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]):
        self.callee = callee
        self.paren = paren
        self.arguments = arguments

    def __repr__(self):
        return f"(call {self.callee} -> {self.arguments})"

    def evaluate(self) -> Any:
        callee: Any = self.callee.evaluate()
        
        arguments: list[Any] = []
        for argument in self.arguments:
            arguments.append(argument.evaluate())
        
        from plox._callable import LoxCallable

        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(self.paren,
                "Can only call functions and classes.")

        function: LoxCallable = callee

        if len(arguments) != function.arity:
            raise LoxRuntimeError(self.paren,
                f"Expected {function.arity} arguments, but got {len(arguments)}.")

        from plox._interpreter import interpreter
        return function.call(interpreter, arguments)
        
    def resolve(self, resolver: "Resolver") -> None:
        self.callee.resolve(resolver)

        for argument in self.arguments:
            argument.resolve(resolver)

class Get(Expr):
    def __init__(self, _object: Expr, name: Token):
        self.object = _object
        self.name = name
    
    def __repr__(self):
        return f"(get {self.name})"

    def evaluate(self) -> Any:
        _object: Any = self.object.evaluate()
        if isinstance(_object, LoxInstance):
            return _object.get(self.name)
        
        raise LoxRuntimeError(self.name, "Only instances have properties.")

    def resolve(self, resolver: "Resolver") -> None:
        self.object.resolve(resolver)

class Set(Expr):
    def __init__(self, _object: Expr, name: Token, value: Expr):
        self.object = _object
        self.name = name
        self.value = value
    
    def __repr__(self) -> str:
        return f"(set {self.name})"
    
    def evaluate(self) -> Any:
        _object: Any = self.object.evaluate()
        if not isinstance(_object, LoxInstance):
            raise RuntimeError(self.name, "Only instances have fields.")

        value: LoxInstance = self.value.evaluate()
        value.set(self.name, value)
        return value

    def resolve(self, resolver: "Resolver") -> None:
        self.value.resolve(resolver)
        self.object.resolve(resolver)

class This(Expr):
    def __init__(self, keyword: Token) -> None:
        self.keyword = keyword

    def __repr__(self) -> str:
        return f"(this {self.keyword.lexeme})"
    
    def evaluate(self) -> Any:
        v: Variable = Variable(self.keyword)
        return v.lookup_variable(self.keyword, self)

    def resolve(self, resolver: "Resolver") -> None:
        from plox.lox import Lox

        if resolver.current_class == ClassType.NONE:
            Lox.error_token(self.keyword, "Can't use 'this' outside of a class.")
            return None
        
        resolver.resolve_local(self, self.keyword)

class Super(Expr):
    def __init__(self, keyword: Token, method: Token) -> None:
        self.keyword = keyword
        self.method = method

    def __repr__(self) -> str:
        return f"(super {self.keyword})"
    
    def evaluate(self) -> Any:
        from plox._interpreter import interpreter
        from plox._callable import LoxClass, LoxInstance, LoxFunction

        distance: int | None = interpreter.locals.get(self)
        if distance is None:
            raise LoxRuntimeError(self.method, "Cannot determine distance to expr.")
        
        superclass: LoxClass = interpreter.environment.get_at(distance, "super")
        _object: LoxInstance = interpreter.environment.get_at(distance - 1, "this")

        method: LoxFunction| None = superclass.find_method(self.method.lexeme)
        if method is None:
            raise LoxRuntimeError(self.method, 
                                  f"Undefined property {self.method.lexeme}.")

        return method.bind(_object)

    def resolve(self, resolver: "Resolver") -> None:
        from plox.lox import Lox
        
        if resolver.current_class == ClassType.NONE:
            Lox.error_token(self.keyword, "Can't use 'super' outside of a class.")
        elif resolver.current_class != ClassType.SUBCLASS:
            Lox.error_token(self.keyword, 
                            "Can't use 'super' in a class with not superclass.")
        
        resolver.resolve_local(self, self.keyword)

if __name__ == "__main__":

    print(
        Binary(
            Unary(
                Token(TokenType.MINUS, "-", None, 1),
                Literal(123)
            ),
            Token(TokenType.STAR, "*", None, 1),
            Grouping(Literal(45.67))
        )
    )