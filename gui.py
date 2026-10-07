"""Simple Tkinter UI for BM7Int.  Run:  python gui.py"""
import tkinter as tk
from tkinter import filedialog, scrolledtext
from BM7int import analyze, run

SAMPLES = {
    "PROG1": 'x: integer;\nx:= 5;\noutput<<x;',
    "PROG2": 'x: integer;\ny: double;\nx:= 3;\ny:= 1.25;\noutput<<x+y;',
    "PROG3": 'x: integer;\ny: double;\nx:= 3;\nif(x<5)\noutput<<x;',
}

root = tk.Tk()
root.title("BM7Int - BM7 Interpreter")
root.geometry("820x720")


def box(label, h):
    tk.Label(root, text=label, anchor="w", font=("Segoe UI", 9, "bold")).pack(fill="x", padx=10, pady=(8, 0))
    w = scrolledtext.ScrolledText(root, height=h, font=("Consolas", 11))
    w.pack(fill="both", expand=True, padx=10)
    return w


src = box("Source code (PROG.BM7)", 9)
status = tk.Label(root, text="-", font=("Consolas", 16, "bold"))
nos = box("NOSPACES.TXT", 5)
res = box("RES_SYM.TXT", 5)
out = box("Program output / errors", 5)

def put(widget, text):
    widget.config(state="normal"); widget.delete("1.0", "end"); widget.insert("1.0", text)


def execute():
    n, r, errs, prog = analyze(src.get("1.0", "end-1c"))
    put(nos, n); put(res, r)
    if errs:
        status.config(text="ERROR", fg="#b3261e")
        put(out, "\n".join(f"Line {l}: {m}" for l, m in errs))
    else:
        status.config(text="NO ERROR(S) FOUND", fg="#1d7a46")
        put(out, run(prog))
    # write the real output files, as in the spec
    open("NOSPACES.TXT", "w").write(n)
    open("RES_SYM.TXT", "w").write(r)


def open_file():
    path = filedialog.askopenfilename(filetypes=[("BM7 files", "*.BM7 *.bm7"), ("All", "*.*")])
    if path:
        put(src, open(path, encoding="utf-8").read()); execute()



