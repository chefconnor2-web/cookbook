# Cookbook

Write your recipes as simple text files and build the two print-ready PDFs that
Amazon KDP (Kindle Direct Publishing) needs to sell your cookbook as a paperback.

## Quick start

```bash
pip install -r requirements.txt
python3 build.py
```

This creates:

| File | Upload on KDP as |
|------|------------------|
| `build/interior.pdf` | **Manuscript** (the inside pages) |
| `build/cover.pdf`    | **Book cover** → "Upload a cover you already have" |

## Adding your recipes

1. Copy a file in `recipes/` (e.g. `recipes/roast-tomato-soup.md`) and fill it in:

   ```markdown
   ---
   title: Roast Tomato Soup
   serves: 4
   prep: 15 min
   cook: 45 min
   image: images/tomato-soup.jpg   # optional photo
   intro: >
     A sentence or two about the dish.
   ---

   ## Ingredients
   - 1.2 kg ripe tomatoes

   ## Method
   1. Heat the oven...

   ## Notes
   Optional tips.
   ```

2. List the file under a chapter in `book.yaml` (recipes print in that order).
3. Run `python3 build.py` again.

Edit `book.yaml` for the title, author, back-cover blurb, cover colours, and the
print options. Edit `front/dedication.md` and `front/introduction.md` for those pages.

## What the build handles for you

- Exact KDP trim size (default 8 × 10 in), with the inside (gutter) margin
  set from the final page count per KDP's table (0.375" up to 150 pages, 0.5"
  up to 300, …).
- Title page, copyright page, dedication, contents with page numbers,
  introduction, chapter openers on right-hand pages, running headers and page numbers.
- Pads the book to KDP's 24-page minimum and an even page count.
- Full wraparound cover sized from the page count: back + spine + front +
  0.125" bleed, using KDP's paper thickness for your paper/ink. Spine text is
  added once the book passes 79 pages (KDP's minimum for spine text).
- Embedded fonts (Lora, SIL Open Font License; see `fonts/OFL.txt`).
- Warns about photos under 300 dpi at print size.

## Publishing on KDP

1. Sign in at kdp.amazon.com → **Create** → **Paperback**.
2. Enter title, author, description and keywords.
3. **Print ISBN**: take the free KDP ISBN, or enter your own (and add it to `book.yaml`).
4. **Print options** must match `book.yaml`: ink & paper, trim size, **No bleed**.
5. Upload `build/interior.pdf` and `build/cover.pdf`, then use **Launch Previewer**.
6. **Order a printed proof copy** before you publish. Check the colours and photos on paper.
7. Set your price and publish.

> Colour photos: set `ink: premium-color` (or `standard-color`) in `book.yaml`,
> and choose the same on KDP. Colour costs more to print than black & white,
> so check the KDP printing-cost calculator before you set a price.
