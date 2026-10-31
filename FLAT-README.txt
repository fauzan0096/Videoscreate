Flat folder - every file sits here, no sub-folders.
1) python setup.py   (or: sh setup.sh)  -> builds ./sunnah-reels/ with the real layout (also .claude/skills/...).
2) cd sunnah-reels && pip install -r requirements.txt   (needs ffmpeg)
3) python -m sunnah_reels check
GitHub web upload: upload the built sunnah-reels/ contents (GitHub web can't create folders from flat names).
Web app only: run setup, host the web/ folder (index.html, data.js, sw.js, manifest.webmanifest, icon.svg).
Full instructions: README.md
