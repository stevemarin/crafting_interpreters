from textwrap import dedent

import pytest

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/inheritance/inherit_from_nil.lox
TEST_SRC = dedent(
    """\
    var Nil = nil;
    class Foo < Nil {} // expect runtime error: Superclass must be a class.
    """
)

EXPECTED_STDOUTS = ["2:13: LoxRuntimeError: Superclass must be a class."]


def test_inherit_from_nil(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert interpreter.had_error
    assert interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS