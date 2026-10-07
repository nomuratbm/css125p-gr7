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



