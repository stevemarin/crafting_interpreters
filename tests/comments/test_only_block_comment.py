from textwrap import dedent

import pytest

from plox.lox import Lox

TEST_SRC = dedent(
    """\
    /*
    This is a multiline block comment
    */
    """
)

EXPECTED_STDOUTS: list[str] = []


def test_block_comment_at_eof(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert not interpreter.had_error
    assert not interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS