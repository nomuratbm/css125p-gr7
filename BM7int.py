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

# --------------------------------------------------------------- parser
class Parser:
    def __init__(self, toks):
        self.t, self.p = toks, 0
        self.decl = {}        # variable name -> type
        self.prog, self.errs = [], []

    def peek(self):
        return self.t[self.p] if self.p < len(self.t) else None

    def next(self):
        tok = self.t[self.p]; self.p += 1; return tok

    def is_(self, v):
        tok = self.peek()
        return tok is not None and tok[1] == v and tok[0] in ("sym", "kw")

    def need(self, v):
        if not self.is_(v):
            tok = self.peek()
            found = f' but found "{tok[-1] if tok[0] == "id" else tok[1]}"' if tok else " at end of program"
            raise BM7Error(f'Expected "{v}"{found}', tok[2] if tok else self.t[-1][2])
        return self.next()

    def operand(self):
        tok = self.peek()
        if tok is None or tok[0] not in ("int", "dbl", "id"):
            raise BM7Error("Expected a number or variable", tok[2] if tok else self.t[-1][2])
        self.next()
        if tok[0] == "id":
            if tok[1] not in self.decl:
                raise BM7Error(f'Variable "{tok[3]}" is not declared', tok[2])
            return ("var", tok[1], self.decl[tok[1]])
        return ("num", float(tok[1]), "double" if tok[0] == "dbl" else "integer")

    def expr(self):
        terms, ops = [self.operand()], []
        while self.is_("+") or self.is_("-"):
            ops.append(self.next()[1]); terms.append(self.operand())
        typ = "double" if any(t[2] == "double" for t in terms) else "integer"
        return (terms, ops, typ)

    def stmt(self):
        tok = self.peek()
        if tok is None:
            raise BM7Error("Unexpected end of program", self.t[-1][2])
        kind, val, line = tok[0], tok[1], tok[2]

        if kind == "id":                                   # declaration / assignment
            self.next()
            name, raw = val, tok[3]
            if self.is_(":"):
                self.next(); ty = self.peek()
                if ty is None or ty[0] != "kw" or ty[1] not in ("integer", "double"):
                    raise BM7Error('Expected data type "integer" or "double"', ty[2] if ty else line)
                self.next(); self.need(";")
                if name in self.decl:
                    raise BM7Error(f'Variable "{raw}" already declared', line)
                self.decl[name] = ty[1]
                return ("decl", name, ty[1])
            if self.is_(":=") or self.is_("="):
                self.next(); e = self.expr(); self.need(";")
                if name not in self.decl:
                    raise BM7Error(f'Variable "{raw}" is not declared', line)
                if self.decl[name] == "integer" and e[2] == "double":
                    raise BM7Error(f'Cannot assign a double value to integer "{raw}"', line)
                return ("assign", name, e)
            raise BM7Error('Expected ":" or ":=" after variable name', line)

        if kind == "kw" and val == "output":
            self.next(); self.need("<<")
            nxt = self.peek()
            if nxt and nxt[0] == "str":
                s = self.next()[1]; self.need(";")
                return ("out_str", s)
            e = self.expr(); self.need(";")
            return ("out", e)

        if kind == "kw" and val == "if":
            self.next(); self.need("("); a = self.operand()
            c = self.peek()
            if c is None or c[0] != "sym" or c[1] not in (">", "<", "==", "!="):
                raise BM7Error("Expected comparison operator (>, <, ==, !=)", c[2] if c else line)
            self.next(); b = self.operand(); self.need(")")
            if self.is_("if"):
                raise BM7Error('Nested "if" is not supported (one-way if only)', self.peek()[2])
            return ("if", a, c[1], b, self.stmt())

        raise BM7Error(f'Unexpected "{tok[-1] if kind == "id" else val}" at start of statement', line)

    def parse(self):
        while self.p < len(self.t):
            start = self.p
            try:
                self.prog.append(self.stmt())
            except BM7Error as e:                            # record error, resync at next ';'
                self.errs.append((e.line, e.msg))
                if self.p == start:
                    self.p += 1
                while self.p < len(self.t) and self.t[self.p - 1][1] != ";":
                    self.p += 1
        return self.prog, self.errs