from textwrap import dedent

import pytest

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/variable/use_nil_as_var.lox
TEST_SRC = dedent(
    """\
    // [line 2] Error at 'nil': Expect variable name.
    var nil = "value";
    """
)

EXPECTED_STDOUTS = ["2:5: LoxParseError: Expected variable name."]


def test_use_nil_as_var(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert interpreter.had_error
    assert not interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS
