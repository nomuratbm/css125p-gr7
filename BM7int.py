"""BM7Int - a simple interpreter for the hypothetical language "BM7".

Process: read source -> NOSPACES.TXT -> RES_SYM.TXT -> syntax check -> run.
Usage:   python BM7int.py samples/PROG1.BM7
"""
import re
import sys

RESERVED = ("integer", "double", "if", "output")
SYMBOLS = ("<<", ":=", "==", "!=", ";", ":", "=", "+", "-", "<", ">", "(", ")")


class BM7Error(Exception):
    def __init__(self, msg, line):
        super().__init__(msg)
        self.msg, self.line = msg, line


# ---------------------------------------------------------------- lexer
def lex(src):
    """Split source into tokens: (kind, value, line). Returns (tokens, errors)."""
    toks, errs = [], []
    i, line = 0, 1
    while i < len(src):
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c.isspace():
            i += 1; continue
        if c == '"':                                   # string literal
            j = i + 1
            while j < len(src) and src[j] not in '"\n':
                j += 1
            if j >= len(src) or src[j] != '"':
                errs.append((line, "Unterminated string")); i = j; continue
            toks.append(("str", src[i + 1:j], line)); i = j + 1; continue
        m = re.match(r"\d+(\.\d+)?", src[i:])          # number
        if m:
            v = m.group()
            bad = len(v.split(".")[1]) > 2 if "." in v else len(v) > 1
            if bad:
                errs.append((line, f'Number "{v}" not allowed (single-digit integers, '
                                   f'doubles up to 2 decimals)'))
            toks.append(("dbl" if "." in v else "int", v, line)); i += len(v); continue
        m = re.match(r"[A-Za-z_]\w*", src[i:])         # keyword / identifier
        if m:
            v = m.group(); low = v.lower()
            toks.append(("kw", low, line) if low in RESERVED else ("id", low, line, v))
            i += len(v); continue
        sym = next((s for s in SYMBOLS if src.startswith(s, i)), None)
        if sym:
            toks.append(("sym", sym, line)); i += len(sym); continue
        errs.append((line, f'Unexpected character "{c}"')); i += 1
    return toks, errs