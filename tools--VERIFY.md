# Verifying a hadith before posting (Shamela)

Every idea has `status`: `verified` or `unverified`. `render` refuses unverified ideas (use `--draft` for a watermarked preview).

For each unverified idea, `arabic_key` holds the phrase written from memory. To verify:

1. Open Shamela and search the `arabic_key` phrase (or ask Claude with the Shamela connector:
   "verify ideas 8-14 on Shamela").
2. Confirm the wording on the page, the book and the hadith number. Copy the exact Arabic from the page.
3. Run:
   python -m sunnah_reels mark-verified 8 --arabic "<exact arabic>" --book-id 1727 --page-id 123

Notes
- Compare the English `quote_en` with a published translation; it is a draft meaning-translation.
- `ref` uses the common numbering (sunnah.com style). Editions on Shamela number differently, so re-check `ref` yourself.
- For non-Bukhari/Muslim sources (Tirmidhi, Abu Dawud, Adab al-Mufrad) check the grading with a qualified source.
- Do not put anything on screen as "hadith" that did not pass these steps.
