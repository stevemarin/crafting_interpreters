import plox._expr as _expr
import plox._stmt as _stmt

from plox._expr import Expr
from plox._stmt import Stmt
from plox._token import Token, TokenType


class ParseError(RuntimeError):
    ...


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current: int = 0

    def parse(self) -> list[Stmt]:
        statements: list[Stmt] = []
        while not self.is_at_end():
            stmt: Stmt | None = self.declaration()
            if stmt is not None:
                statements.append(stmt)

        return statements

    def expression(self) -> Expr:
        return self.assignment()

    def declaration(self) -> Stmt | None:
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            elif self.match(TokenType.FUN):
                return self.function("function")
            elif self.match(TokenType.VAR):
                return self.var_declaration()
            else:
                return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def class_declaration(self) -> Stmt:
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass: _expr.Variable | None = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = _expr.Variable(self.previous())

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods: list[_stmt.Function] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function("method"))

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return _stmt.Class(name, superclass, methods)

    def statement(self) -> Stmt:
        if self.match(TokenType.FOR):
            return self.for_statement()
        elif self.match(TokenType.IF):
            return self.if_statement()
        elif self.match(TokenType.PRINT):
            return self.print_statement()
        elif self.match(TokenType.RETURN):
            return self.return_statement()
        elif self.match(TokenType.WHILE):
            return self.while_statement()
        elif self.match(TokenType.LEFT_BRACE):
            return _stmt.Block(self.block())
        else:
            return self.expression_statement()

    def for_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        if self.match(TokenType.SEMICOLON):
            initializer: None | Stmt = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        if not self.check(TokenType.SEMICOLON):
            condition: Expr | None = self.expression()
        else:
            condition = None

        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        if not self.check(TokenType.RIGHT_PAREN):
            increment: Expr | None = self.expression()
        else:
            increment = None

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body: Stmt = self.statement()

        if increment is not None:
            body = _stmt.Block([body, _stmt.Expression(increment)])

        if condition is None:
            condition = _expr.Literal(True)

        body = _stmt.While(condition, body)

        if initializer is not None:
            body = _stmt.Block([initializer, body])

        return body

    def if_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after if.")
        condition: Expr = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch: Stmt = self.statement()
        if self.match(TokenType.ELSE):
            else_branch: Stmt | None = self.statement()
        else:
            else_branch = None

        return _stmt.If(condition, then_branch, else_branch)

    def print_statement(self) -> Stmt:
        value: Expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return _stmt.Print(value)

    def return_statement(self) -> Stmt:
        keyword: Token = self.previous()
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        else:
            value = None

        self.consume(TokenType.SEMICOLON, "Expect ';' after return value")

        return _stmt.Return(keyword, value)

    def var_declaration(self) -> Stmt:
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer: Expr | None = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")

        if initializer is None:
            raise self.error(self.peek(), "Expect variable expression.")
        else:
            return _stmt.Variable(name, initializer)

    def while_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: Expr = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body: Stmt = self.statement()

        return _stmt.While(condition, body)

    def expression_statement(self) -> Stmt:
        expr: Expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return _stmt.Expression(expr)

    def function(self, kind: str) -> _stmt.Function:
        name: Token = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")

        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters: list[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            parameters.append(
                self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
            )
            while self.match(TokenType.COMMA):
                if len(parameters) >= 255:
                    self.error(self.peek(), "Can't have more than 255 parameters.")
                parameters.append(
                    self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")

        body: list[Stmt] = self.block()

        return _stmt.Function(name, parameters, body)

    def block(self) -> list[Stmt]:
        statements: list[Stmt] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            stmt: Stmt | None = self.declaration()
            if stmt is not None:
                statements.append(stmt)

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")

        return statements

    def assignment(self) -> Expr:
        expr: Expr = self.or_expression()

        if self.match(TokenType.EQUAL):
            equals: Token = self.previous()
            value: Expr = self.assignment()

            if isinstance(expr, _expr.Variable):
                name: Token = expr.name  # type: ignore
                return _expr.Assign(name, value)
            elif isinstance(expr, _expr.Get):
                return _expr.Set(expr.object, expr.name, value)  # type: ignore

            self.error(equals, "Invalid assignment target.")

        return expr

    def or_expression(self) -> Expr:
        expr: Expr = self.and_expression()

        while self.match(TokenType.OR):
            operator: Token = self.previous()
            right: Expr = self.and_expression()
            expr = _expr.Logical(expr, operator, right)

        return expr

    def and_expression(self) -> Expr:
        expr: Expr = self.equality()

        while self.match(TokenType.AND):
            operator: Token = self.previous()
            right: Expr = self.equality()
            expr = _expr.Logical(expr, operator, right)

        return expr

    def equality(self) -> Expr:
        expr: Expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator: Token = self.previous()
            right: Expr = self.comparison()
            expr = _expr.Binary(expr, operator, right)

        return expr

    def match(self, *token_types: TokenType) -> bool:
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()

        raise self.error(self.peek(), message)

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        else:
            return self.peek().type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def error(self, token: Token, message: str) -> ParseError:
        from plox.lox import Lox

        Lox.error_token(token, message)
        return ParseError()

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            if self.peek().type in (
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            ):
                return

            self.advance()

    def comparison(self) -> Expr:
        expr: Expr = self.term()

        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator: Token = self.previous()
            right: Expr = self.term()
            expr = _expr.Binary(expr, operator, right)

        return expr

    def term(self) -> Expr:
        expr: Expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator: Token = self.previous()
            right: Expr = self.factor()
            expr = _expr.Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        expr: Expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator: Token = self.previous()
            right: Expr = self.unary()
            expr = _expr.Binary(expr, operator, right)

        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right: Expr = self.unary()
            return _expr.Unary(operator, right)

        return self.call()

    def finish_call(self, callee: Expr):
        arguments: list[Expr] = []

        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self.error(self.peek(), "Can't have more than 255 arguments.")
                arguments.append(self.expression())

        paren: Token = self.consume(
            TokenType.RIGHT_PAREN, "Expect ')' after arguments."
        )

        return _expr.Call(callee, paren, arguments)

    def call(self) -> Expr:
        expr: Expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name: Token = self.consume(
                    TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expr = _expr.Get(expr, name)
            else:
                break

        return expr

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return _expr.Literal(False)
        elif self.match(TokenType.TRUE):
            return _expr.Literal(True)
        elif self.match(TokenType.NIL):
            return _expr.Literal(None)
        elif self.match(TokenType.NUMBER, TokenType.STRING):
            return _expr.Literal(self.previous().literal)
        elif self.match(TokenType.SUPER):
            keyword: Token = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method: Token = self.consume(
                TokenType.IDENTIFIER, "Expect superclass method name."
            )
            return _expr.Super(keyword, method)
        elif self.match(TokenType.LEFT_PAREN):
            expr: Expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return _expr.Grouping(expr)
        elif self.match(TokenType.THIS):
            return _expr.This(self.previous())
        elif self.match(TokenType.IDENTIFIER):
            return _expr.Variable(self.previous())
        else:
            raise self.error(self.peek(), "Expect expression.")
