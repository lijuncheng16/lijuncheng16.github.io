"""
Fetches citation stats from Billy Li's Google Scholar profile
and writes them to scholar_data.json in the repo root.
Run locally or via GitHub Actions.
"""
import json
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

SCHOLAR_USER_ID = "fBnAdlkAAAAJ"
OUTPUT_FILE = "scholar_data.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_stats():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_USER_ID}&hl=en"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Stats table: cells alternate all-time / since-2019
    cells = soup.select("#gsc_rsb_st td.gsc_rsb_std")
    if not cells:
        raise ValueError("Could not find Scholar stats table — page structure may have changed.")

    citations = int(cells[0].text.replace(",", ""))
    h_index = int(cells[2].text.replace(",", ""))
    return citations, h_index


def fetch_publication_count():
    """Paginate through all publications to get total count."""
    count = 0
    start = 0
    while True:
        url = (
            f"https://scholar.google.com/citations"
            f"?user={SCHOLAR_USER_ID}&hl=en&cstart={start}&pagesize=100"
        )
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("#gsc_a_b tr.gsc_a_tr")
        count += len(rows)
        if len(rows) < 100:
            break
        start += 100
        time.sleep(1)  # be polite
    return count


def main():
    print("Fetching Google Scholar stats...")
    try:
        citations, h_index = fetch_stats()
        print(f"  Citations: {citations}, H-Index: {h_index}")
    except Exception as e:
        print(f"ERROR fetching stats: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        publications = fetch_publication_count()
        print(f"  Publications: {publications}")
    except Exception as e:
        print(f"WARNING: Could not count publications ({e}), keeping existing value.", file=sys.stderr)
        try:
            with open(OUTPUT_FILE) as f:
                publications = json.load(f).get("publications", 0)
        except Exception:
            publications = 0

    data = {
        "citations": citations,
        "h_index": h_index,
        "publications": publications,
        "last_updated": str(date.today()),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Wrote {OUTPUT_FILE}: {data}")


if __name__ == "__main__":
    main()
