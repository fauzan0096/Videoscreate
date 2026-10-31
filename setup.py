"""Arranges this flat folder into the real project layout (run once):  python setup.py
Rule: 'a--b--c.txt' -> a/b/c.txt   and a 'dot_' prefix -> leading '.'  (e.g. dot_claude--skills--... -> .claude/skills/...)"""
import os, shutil, sys
here = os.path.dirname(os.path.abspath(__file__)); dest = os.path.join(here, "sunnah-reels")
for n in sorted(os.listdir(here)):
    if n in ("setup.py", "setup.sh", "FLAT-README.txt") or os.path.isdir(os.path.join(here, n)): continue
    parts = ["." + p[4:] if p.startswith("dot_") else p for p in n.split("--")]
    t = os.path.join(dest, *parts); os.makedirs(os.path.dirname(t), exist_ok=True); shutil.copy2(os.path.join(here, n), t)
os.makedirs(os.path.join(dest, "out"), exist_ok=True)
print("Done ->", dest, "\nNext:  cd sunnah-reels && pip install -r requirements.txt && python -m sunnah_reels check")
