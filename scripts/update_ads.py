import requests
import os
import time

TOKEN = os.environ["ADS_TOKEN"]

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

LIBRARIES = {
    "spurs_pub.html": "_UXNDXIYTPCQjmT3CouDPg",
    "comm_pub.html": "dTYqgxcTSr2BOuHMLakftA"
}


def safe_get(url, headers=None, params=None, retries=5):
    """
    Handles ADS rate limiting (429 errors) by retrying with backoff.
    """
    for attempt in range(retries):
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            wait_time = 10 * (attempt + 1)
            print(f"429 rate limit hit. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        return response

    raise Exception("Too many retries after repeated 429 errors")


def fetch_library_bibcodes(library_id):
    """
    Fetch all bibcodes from a given ADS library.
    """
    url = f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library_id}"

    response = safe_get(url, headers=headers)
    return response.json()["documents"]


def fetch_paper_details(bibcodes):
    """
    Fetch metadata for all papers in the library.
    Sorted newest first using publication date.
    """
    url = "https://api.adsabs.harvard.edu/v1/search/query"

    params = {
        "q": "bibcode:(" + " OR ".join(bibcodes) + ")",
        "fl": "title,author,year,pub,bibcode",
        "rows": 500,
        "sort": "pubdate desc"
    }

    response = safe_get(url, headers=headers, params=params)
    return response.json()["response"]["docs"]


def format_authors(authors):
    """
    Format author list for display.
    """
    if not authors:
        return "Unknown"

    if len(authors) <= 6:
        return ", ".join(authors)

    return ", ".join(authors[:6]) + ", et al."


def generate_html(docs):
    """
    Convert ADS records into HTML <li> entries.
    """
    lines = []

    for paper in docs:
        authors = format_authors(paper.get("author", []))
        title = paper.get("title", ["Untitled"])[0]
        year = paper.get("year", "")
        journal = paper.get("pub", "")
        bibcode = paper.get("bibcode", "")

        line = (
            f'<li>{authors}, "{title}", {year}, '
            f'<i>{journal}</i>, '
            f'<a href="https://ui.adsabs.harvard.edu/abs/{bibcode}" '
            f'target="_blank">ADS Link</a></li>'
        )

        lines.append(line)

    return "\n".join(lines)


for filename, library_id in LIBRARIES.items():
    print(f"Updating {filename}...")

    try:
        # Step 1: Get bibcodes from library
        bibcodes = fetch_library_bibcodes(library_id)

        # Small pause before next ADS request
        time.sleep(5)

        # Step 2: Get paper metadata
        docs = fetch_paper_details(bibcodes)

        # Step 3: Generate HTML
        html = generate_html(docs)

        output_path = f"publications/{filename}"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Finished updating {filename}")

        # Pause before processing next library
        time.sleep(5)

    except Exception as e:
        print(f"Failed updating {filename}: {e}")

print("Finished updating all publication lists.")