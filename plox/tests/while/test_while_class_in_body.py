from textwrap import dedent

import pytest

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/while/class_in_body.lox
TEST_SRC = dedent(
    """\
    // [line 2] Error at 'class': Expect expression.
    while (true) class Foo {}
    """
)

EXPECTED_STDOUTS = ["2:14: LoxParseError: Expected expression."]


def test_class_in_body(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert interpreter.had_error
    assert not interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS
