# #!/usr/bin/env python

# filename=${1}

# mapfile arr < "${filename}"

# expected=""
# for line in "${arr[@]}"; do
#     match="$(perl -n -e '/expect: (.*)\n$/ && print $1' <<< ${line})"
#     [[ ! -z ${match} ]] && expected="${expected}${match}\n"

#     match="$(perl -n -e '/expect runtime error: (.*)\n$/ && print $1' <<< ${line})"
#     [[ ! -z ${match} ]] && expected="${expected}${match}\n"

#     match="$(perl -n -e '/Error at '\=': (.*)\n$/ && print $1' <<< ${line})"
#     [[ ! -z ${match} ]] && expected="${expected}${match}\n"
# done


# expected=$(echo -e "${expected}")
# result=$(python plox/plox/lox.py "${filename}" 2>&1)

# if [[ -z ${expected} ]]; then
#     echo "⚡ ${filename}"
# else [[ ${result} =~ ${expected} ]] \
#     && echo "💲 ${filename}" \
#     || echo "❌ ${filename}"
# fi

# echo "Expected: ${expected}"
# echo "Result: ${result}"

"""
skipped: [
    './test/operator/not_class.lox', 
    './test/assignment/local.lox'
]

failed: [
    './test/limit/no_reuse_constants.lox', 
    './test/limit/too_many_constants.lox', 
    './test/limit/loop_too_large.lox', 
    './test/variable/shadow_and_local.lox', 
    './test/variable/in_nested_block.lox', 
    './test/variable/shadow_local.lox', 
    './test/logical_operator/and_truth.lox', 
    './test/logical_operator/and.lox', 
    './test/logical_operator/or.lox', 
    './test/logical_operator/or_truth.lox'
]
"""

from subprocess import Popen, PIPE

def strip_expected(line: str) -> str:
    slashes = line.split("//", maxsplit=1)[1]
    colon = slashes.split(":", maxsplit=1)[1]
    return colon.strip()


def get_expected_from_line(line: str) -> None | str:
    if ("// expect:" in line or
        ("//" in line and "Error at" in line) or
        ("//" in line and "Error: " in line) or
        "// expect runtime error:" in line):

        return strip_expected(line)

    return None


def get_expected_from_file(src: str) -> str:
    results: list[str | None] = []
    for line in src.split("\n"):
        results.append(get_expected_from_line(line.strip()))

    filtered: list[str] = list(filter(lambda x: x is not None, results))  # type: ignore
    return "\n".join(filtered)


def get_src(path: str) -> None | str:
    src = None
    if ".lox" in path:
        with open(path, 'r') as fh:
            src = fh.read()
    
    return src


def get_all_src(directory: str = "./test") -> dict[str, str]:
    all_src: dict[str, str] = {}

    for root, _, files in walk(directory):
        for filename in files:
            full_path = join(root, filename)
            src = get_src(join(root, filename))
            if src is not None:
                all_src[full_path] = src
    
    return all_src
                

def get_output_from_file(path: str) -> tuple[str, str]:
    sp = Popen(["python", "plox/plox/lox.py", path],
               stderr=PIPE,
               stdout=PIPE)
    out, err = sp.communicate()

    return (out.decode(), err.decode())


if __name__ == "__main__":
    from os import walk
    from os.path import join

    from rich.progress import track

    all_src = get_all_src()

    skip = {
        # not relevant for Python VM
        "./test/limit/no_reuse_constants.lox",
        "./test/limit/too_many_constants.lox",
        "./test/limit/loop_too_large.lox",
        # both stderr and stdout non-empty
        "./test/operator/not_class.lox",
        "./test/assignment/local.lox",
    }

    failed, passed, skipped = [], [], []
    for filename, src in track(all_src.items()):
        stdout, stderr = get_output_from_file(filename)
        expected = get_expected_from_file(src)

        if filename in skip:
            skipped.append(filename)
            continue

        try:
            assert stdout == "" or stderr == ""
        except AssertionError:
            skipped.append(filename)
        
        if stderr == "":
            try:
                assert stdout.strip() == expected.strip()
                passed.append(filename)
            except AssertionError:
                failed.append(filename)
        elif stdout == "":
            try:
                for line in expected.split("\n"):
                    assert line.strip() in expected
                passed.append(filename)
            except AssertionError:
                failed.append(filename)
        else:
            print(filename)
            assert False

    print()
    print("skipped:")
    for _ in skipped:
        print(f"\t{_}")
    print("failed:")
    for _ in failed:
        print(f"\t{_}")
