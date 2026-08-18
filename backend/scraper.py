import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pymongo import MongoClient
from datetime import datetime
import re

# =========================
# CONFIG
# =========================

BASE_URL = "https://bodex.io"

START_URLS = [
    "https://bodex.io/",
    "https://bodex.io/who-we-are/",
    "https://bodex.io/what-we-do/",
    "https://bodex.io/products/",
    "https://bodex.io/federal/",
    "https://bodex.io/manufacturing-2/",
    "https://bodex.io/what-we-do/data-management/",
    "https://bodex.io/products/recordex/",
]

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "bodex_ai"
COLLECTION_NAME = "knowledge"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "Chrome/150.0 Safari/537.36"
    )
}

# =========================
# DATABASE
# =========================

mongo = MongoClient(MONGO_URI)

db = mongo[DB_NAME]

collection = db[COLLECTION_NAME]

# =========================
# CLEAN TEXT
# =========================

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================
# SCRAPE PAGE
# =========================

def scrape_page(url):

    print(f"Scraping: {url}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

    except Exception as e:
        print("ERROR:", url)
        print(e)
        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Remove unnecessary elements
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer"
    ]):
        tag.decompose()

    title = ""

    if soup.title:
        title = clean_text(
            soup.title.get_text()
        )

    main = soup.find("main")

    if main:
        content = main.get_text(
            separator="\n"
        )
    else:
        content = soup.get_text(
            separator="\n"
        )

    lines = []

    for line in content.splitlines():

        line = clean_text(line)

        if line:
            lines.append(line)

    text = "\n".join(lines)

    return {
        "url": url,
        "title": title,
        "content": text,
        "scraped_at": datetime.utcnow()
    }

# =========================
# FIND BODEX LINKS
# =========================

def find_links(url):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = set()

        for a in soup.find_all("a", href=True):

            href = a["href"]

            full_url = urljoin(
                url,
                href
            )

            parsed = urlparse(full_url)

            # Only BODEX website
            if parsed.netloc != "bodex.io":
                continue

            # Remove fragments
            full_url = full_url.split("#")[0]

            links.add(full_url)

        return links

    except Exception as e:
        print("LINK ERROR:", e)
        return set()

# =========================
# SAVE PAGE
# =========================

def save_page(data):

    if not data:
        return

    collection.update_one(
        {
            "url": data["url"]
        },
        {
            "$set": data
        },
        upsert=True
    )

    print(
        f"Saved: {data['title'] or data['url']}"
    )

# =========================
# MAIN SCRAPER
# =========================

def run_scraper():

    print("\n==============================")
    print("BODEX WEBSITE SCRAPER")
    print("==============================\n")

    visited = set()

    # First scrape important pages
    for url in START_URLS:

        if url in visited:
            continue

        visited.add(url)

        data = scrape_page(url)

        save_page(data)

    # Discover more BODEX pages
    for start_url in START_URLS:

        links = find_links(
            start_url
        )

        for url in links:

            # Skip unwanted files
            if any(
                url.lower().endswith(ext)
                for ext in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".webp",
                    ".pdf",
                    ".zip"
                ]
            ):
                continue

            if url in visited:
                continue

            # Keep scraper controlled
            if len(visited) >= 50:
                break

            visited.add(url)

            data = scrape_page(url)

            save_page(data)

    print("\n==============================")
    print("SCRAPING COMPLETE")
    print(
        "Pages saved:",
        collection.count_documents({})
    )
    print("==============================\n")


if __name__ == "__main__":
    run_scraper()