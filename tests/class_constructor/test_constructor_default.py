from textwrap import dedent

import pytest

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/constructor/default.lox
TEST_SRC = dedent(
    """\
    class Foo {}

    var foo = Foo();
    print foo; // expect: Foo instance
    """
)

EXPECTED_STDOUTS = ["<inst Foo>"]


def test_default(capsys: pytest.CaptureFixture) -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert not interpreter.had_error
    assert not interpreter.had_runtime_error

    all_out = capsys.readouterr().out.splitlines()
    assert all_out == EXPECTED_STDOUTS