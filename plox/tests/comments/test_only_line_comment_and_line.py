from textwrap import dedent

from plox.lox import Lox

# Base cases from https://github.com/munificent/craftinginterpreters/blob/master/test/comments/only_line_comment_and_line.lox
TEST_SRC = dedent(
    """\
    // comment

    """
)


def test_only_line_comment_and_line() -> None:
    interpreter = Lox()
    interpreter.run(TEST_SRC)

    assert not interpreter.had_error
    assert not interpreter.had_runtime_error
