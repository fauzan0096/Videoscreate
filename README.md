# sunnah-reels

Offline generator for short vertical (720x1280, 30fps) animated stick-figure reels about forgotten sunnahs.
Style: dark minimal scenes, English captions, Arabic matn, source line, "send this to someone" ending.

## Setup
    pip install -r requirements.txt     # needs ffmpeg installed
    # optional: add Amiri + EB Garamond to assets/fonts/

## Use
    python -m sunnah_reels list                    # all 100 ideas (✓ = verified)
    python -m sunnah_reels check                   # validate data + count verified
    python -m sunnah_reels schedule --start 2026-11-01   # 60-day posting calendar
    python -m sunnah_reels render 1-7              # render verified ideas to out/
    python -m sunnah_reels render 1 --preview      # 4 PNG frames, fast
    python -m sunnah_reels render 8 --draft        # unverified -> watermarked draft
    python -m sunnah_reels render 1 --music bg.mp3 # optional background audio (use rights-free)

Rendering takes roughly 1.5-2 min per 20-25s video on a normal laptop (pure Python/Pillow).

## Content
`data/ideas.json`: 100 ideas. Days 1-60 = daily schedule; 61-100 = spare/seasonal.
Only ideas 1-7 are verified against Shamela so far. Verify the rest in batches: see `tools/VERIFY.md`.

## Add your own scene
Add a function to `sunnah_reels/scenes.py` and register it in `TEMPLATES`; use it via `"template"` in an idea.

## New series (v2): "Sahaba ne poocha" + "Hadith ya Afwah?"
- `data/series_qa.json` (ids 101-104, template `ask`) and `data/series_myth.json` (ids 201-204, template `myth`, `verdict`: sahih | hasan | weak).
- `python -m sunnah_reels list --series myth` · `render 101 --draft` (all new ideas start as *unverified*).
- Myth reels: never give your own ruling. Put the grading scholar + book + page in `ref`, verify on Shamela, then `mark-verified`.
- Phone app: `web/` is a PWA (open `web/index.html` from any static host / GitHub Pages). Pick idea -> Preview -> Record video (saves mp4/webm, 540x960).
  After editing JSON run `python tools/export_web.py` to refresh `web/data.js`.

## v3: "agent" workflow (idea in -> finished 30-60 s reel out)
- `python -m sunnah_reels new qa|myth ...` : adds the idea, renders the video and writes `<name>.txt` (title, description, source, hashtags). `--target 30..60` sets the length (default 40).
- `python -m sunnah_reels daily` : renders the next verified, not-yet-rendered idea. Run it once a day (cron / Task Scheduler).
- `.claude/skills/sunnah-reel-agent/SKILL.md` : the agent. Open this repo in Claude Code / Claude Desktop with the Shamela connector, say
  "aaj ka reel: <hadith ya sawaal>" and it verifies on Shamela, fills the data, renders and hands back the mp4 + text.
- ids 101-104 and 201-204 are verified on Shamela (2026-10-31); `translation_note` on each says what to eyeball before posting.
