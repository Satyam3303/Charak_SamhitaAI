"""
STEP 1: Scrape all pages from carakasamhitaonline.com
Run: python step1_scrape.py
"""

import requests
import json
import time
import os

API_URL = "https://www.carakasamhitaonline.com/api.php"
OUTPUT_FILE = "charak_samhita_raw.json"

def get_all_page_titles():
    """Fetch all page titles using MediaWiki API"""
    titles = []
    params = {
        "action": "query",
        "list": "allpages",
        "aplimit": "500",
        "apnamespace": "0",  # main content only
        "format": "json"
    }

    print("📚 Fetching all page titles...")
    while True:
        response = requests.get(API_URL, params=params, timeout=30)
        data = response.json()
        pages = data["query"]["allpages"]
        titles.extend([p["title"] for p in pages])
        print(f"  Found {len(titles)} titles so far...")

        if "continue" in data:
            params["apcontinue"] = data["continue"]["apcontinue"]
        else:
            break

    print(f"✅ Total pages found: {len(titles)}")
    return titles


def get_page_content(title):
    """Get plain text content of a single page"""
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "format": "json"
    }
    response = requests.get(API_URL, params=params, timeout=30)
    data = response.json()
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    return page.get("extract", "")


def scrape_all():
    # Load already scraped titles to resume if interrupted
    already_scraped = set()
    all_data = []

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            already_scraped = {d["title"] for d in all_data}
        print(f"🔄 Resuming... already have {len(already_scraped)} pages")

    titles = get_all_page_titles()

    for i, title in enumerate(titles):
        if title in already_scraped:
            continue

        try:
            print(f"[{i+1}/{len(titles)}] Scraping: {title}")
            content = get_page_content(title)
            if content and len(content) > 100:
                all_data.append({
                    "title": title,
                    "url": f"https://www.carakasamhitaonline.com/index.php/{title.replace(' ', '_')}",
                    "content": content
                })
        except Exception as e:
            print(f"  ⚠️ Error scraping {title}: {e}")

        # Save every 50 pages to avoid losing progress
        if (i + 1) % 50 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"  💾 Saved {len(all_data)} pages so far...")

        time.sleep(0.5)  # be respectful to the server

    # Final save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! Scraped {len(all_data)} pages → saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape_all()
