"""Save the body text of 4 news articles about nuclear fusion as clean .txt files.

Install once:   pip install requests beautifulsoup4
Run:            python get_fusion_articles.py

Output:         fusion_texts/<name>.txt   (headline, subheadings, body text only)
                fusion_texts/sources.csv  (author, date, URL and word count)

If an article cannot be downloaded in full (paywall or blocked request), open it
in your browser, press Ctrl+S, choose "Webpage, HTML only", and save it in a
folder called saved_pages next to this script, as <name>.html. Then run again.
"""

import csv
import re
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

KEEP_HEADLINE_AND_SUBHEADINGS = True  # set to False for body paragraphs only

BASE = Path(__file__).resolve().parent
SAVED = BASE / "saved_pages"
OUT = BASE / "fusion_texts"

# "select" picks the text blocks of the article itself, so captions, ads,
# related-story boxes, sign-up forms and author bios are left out.
NATURE = "div.c-article-body > p, div.c-article-body > h2, div.c-article-body > h3"
SCIAM = 'article [data-block="sciam/paragraph"], article [data-block="sciam/heading"]'
PHYSWORLD = "div.entry-content > p, div.entry-content > h3"

ARTICLES = [
    {
        "name": "1_nature_ignition",
        "title": "Nuclear-fusion lab achieves 'ignition': what does it mean?",
        "source": "Nature",
        "author": "Jeff Tollefson and Elizabeth Gibney",
        "date": "2022-12-13",
        "url": "https://www.nature.com/articles/d41586-022-04440-7",
        "select": NATURE,
        "min_words": 1150,
    },
    {
        "name": "2_nature_iter_delay",
        "title": "ITER delay: what it means for nuclear fusion",
        "source": "Nature",
        "author": "Elizabeth Gibney",
        "date": "2024-07-08",
        "url": "https://www.nature.com/articles/d41586-024-02247-2",
        "select": NATURE,
        "min_words": 1150,
    },
    {
        "name": "3_sciam_records",
        "title": "Record-Breaking Results Bring Fusion Power Closer to Reality",
        "source": "Scientific American",
        "author": "Tom Metcalfe",
        "date": "2025-07-03",
        "url": "https://www.scientificamerican.com/article/record-breaking-results-bring-fusion-power-closer-to-reality/",
        "select": SCIAM,
        "min_words": 1200,
    },
    {
        "name": "4_physicsworld_investment",
        "title": "Private investment in fusion firms jumps by $4.5bn",
        "source": "Physics World",
        "author": "Michael Banks",
        "date": "2026-07-14",
        "url": "https://physicsworld.com/a/private-investment-in-fusion-firms-jumps-by-4-5bn/",
        "select": PHYSWORLD,
        "min_words": 370,
    },
]


def clean(text):
    """Normalise Unicode and collapse all whitespace to single spaces."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("­", "").replace("​", "")
    return re.sub(r"\s+", " ", text).strip()


def extract(html, article):
    """Return (list of text blocks, number of words in the body paragraphs)."""
    soup = BeautifulSoup(html, "html.parser")
    blocks, words = [], 0
    for element in soup.select(article["select"]):
        text = clean(element.get_text())
        if not text:
            continue
        is_heading = element.name in ("h2", "h3") or "heading" in element.get("data-block", "")
        if is_heading:
            if KEEP_HEADLINE_AND_SUBHEADINGS:
                blocks.append(text)
        else:
            blocks.append(text)
            words += len(text.split())
    return blocks, words


def load_html(article):
    """Use the page saved from the browser if there is one, otherwise download it."""
    saved = SAVED / f"{article['name']}.html"
    if saved.exists():
        return saved.read_bytes(), "saved page"
    response = requests.get(
        article["url"],
        headers={"User-Agent": "Mozilla/5.0 (student text-analysis script)"},
        timeout=30,
    )
    response.raise_for_status()
    return response.content, "download"


def main():
    OUT.mkdir(exist_ok=True)
    SAVED.mkdir(exist_ok=True)
    rows = []

    for article in ARTICLES:
        name = article["name"]
        try:
            html, origin = load_html(article)
            blocks, words = extract(html, article)
            problem = None
            if words < article["min_words"]:
                problem = f"only {words} words found ({origin}), probably incomplete"
        except (requests.RequestException, OSError) as error:
            problem = str(error)

        if problem:
            # Remove any old output so an outdated file is never mistaken for a good one.
            (OUT / f"{name}.txt").unlink(missing_ok=True)
            print(f"FAILED  {name}: {problem}")
            print(f"        Open {article['url']}")
            print(f"        Ctrl+S, 'Webpage, HTML only', save as saved_pages/{name}.html")
            continue

        if KEEP_HEADLINE_AND_SUBHEADINGS:
            blocks.insert(0, article["title"])
        (OUT / f"{name}.txt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        print(f"OK      {name}: {words} words ({origin})")
        rows.append({**{k: article[k] for k in ("name", "title", "source", "author", "date", "url")},
                     "body_words": words})

    if rows:
        with open(OUT / "sources.csv", "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"\n{len(rows)} of {len(ARTICLES)} articles saved in {OUT}")


if __name__ == "__main__":
    main()