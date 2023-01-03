#!/usr/bin/env python3

import re
from pathlib import Path
import sys
import ast
import jsbeautifier


def unminify(code: str) -> str:
    options = jsbeautifier.BeautifierOptions()
    options.brace_preserve_inline = False
    options.comma_first = False
    options.end_with_newline = True
    options.eol = '\n'
    options.indent_char = ' '
    options.indent_empty_lines = False
    options.indent_level = 0
    options.indent_size = 4
    options.indent_with_tabs = False
    options.jslint_happy = True
    options.keep_array_indentation = True
    beautifier = jsbeautifier.Beautifier(options)
    return beautifier.beautify(code)


def main():
    if len(sys.argv) != 3:
        raise RuntimeError(
            'Usage: python3 deobfuscate.py /path/to/code.js /path/to/output')

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        raise RuntimeError(f'{input_path}: File does not exist.')
    if not input_path.is_file():
        raise RuntimeError(f'{input_path}: Not a file.')

    output_path = Path(sys.argv[2])

    with open(input_path, encoding='UTF-8') as f:
        code = f.read()

    # Unminify (format with linebreaks, indentation, and whitespaces) the code.
    code = unminify(code)

    # variable name to literals
    literal_map = {}

    # Assuming the following code structure:
    #
    # $varname0 = $varname1 = $varname2 = [(literal), (literal), ...];
    literals_pattern = re.compile(
        '^(\\$.) = (\\$.) = (\\$.) = (\\[.*?\\]);$', re.MULTILINE)

    m = literals_pattern.search(code)
    if m is None:
        raise RuntimeError(
            'Assumptions about the structure of `code.js` do not hold.')
    elements = m.group(4)
    # There may be regex literals, which cannot be parsed as a Python literal.
    # So, skip them.
    elements = re.sub(', /.*?/g?m?(?=,)', ', None', elements)
    # Parse the array of literals as a Python literal.
    elements = ast.literal_eval(elements)
    literal_map[m.group(1)] = elements
    literal_map[m.group(2)] = elements
    literal_map[m.group(3)] = elements

    m = literals_pattern.search(code, m.end())
    if m is None:
        raise RuntimeError(
            'Assumptions about the structure of `code.js` do not hold.')
    elements = m.group(4)
    # There may be regex literals, which cannot be parsed as a Python literal.
    # So, skip them.
    elements = re.sub(', /.*?/g?m?(?=,)', ', None', elements)
    # Parse the array of literals as a Python literal.
    elements = ast.literal_eval(elements)
    literal_map[m.group(1)] = elements
    literal_map[m.group(2)] = elements
    literal_map[m.group(3)] = elements

    m = literals_pattern.search(code, m.end())
    if m is None:
        raise RuntimeError(
            'Assumptions about the structure of `code.js` do not hold.')
    elements = m.group(4)
    # There may be regex literals, which cannot be parsed as a Python literal.
    # So, skip them.
    elements = re.sub(', /.*?/g?m?(?=,)', ', None', elements)
    # Parse the array of literals as a Python literal.
    elements = ast.literal_eval(elements)
    literal_map[m.group(1)] = elements
    literal_map[m.group(2)] = elements
    literal_map[m.group(3)] = elements

    for var, elements in literal_map.items():
        for i, e in enumerate(elements):
            s = f'{var}[{i}]'
            # Print progress to stderr.
            print(s)
            if e is None:
                # A skipped literal.
                continue
            if isinstance(e, str) and e.find('"') != -1:
                # String literals including double quotations are skipped
                # because they are a little hard to parse.
                continue
            if isinstance(e, str):
                code = code.replace(s, f'"{e}"')
            else:
                code = code.replace(s, str(e))

    with open(output_path, 'w', encoding='UTF-8') as f:
        f.write(code)


if __name__ == '__main__':
    main()
    sys.exit(0)
