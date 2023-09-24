from textwrap import dedent

import pytest

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/if/fun_in_then.lox
TEST_SRC = dedent(
    """\
    // [line 2] Error at 'fun': Expect expression.
    if (true) fun foo() {}
    """
)

EXPECTED_STDOUTS = ["2:11: LoxParseError: Expected expression."]


def test_fun_in_then(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert interpreter.had_error
    assert not interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS
