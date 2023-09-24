from textwrap import dedent

import pytest

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/method/missing_arguments.lox
TEST_SRC = dedent(
    """\
    class Foo {
      method(a, b) {}
    }

    Foo().method(1); // expect runtime error: Expected 2 arguments but got 1.
    """
)

EXPECTED_STDOUTS = ["5:15: LoxRuntimeError: Expected 2 arguments but got 1."]


def test_missing_arguments(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert interpreter.had_error
    assert interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS
