from textwrap import dedent

import pytest

from plox.lox import Lox

TEST_SRC = dedent(
    """\
    fun f1(a) {
        break;  // Expect resolver error: Can't use 'break' outside of a for or while loop.
    }
    """
)

EXPECTED_STDOUTS = ["2:5: LoxResolverError: Can't use 'break' outside of a for or while loop."]


def test_non_loop_break(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert interpreter.had_error
    assert not interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS
