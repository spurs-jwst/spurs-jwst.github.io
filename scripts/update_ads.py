import requests
import os

TOKEN = os.environ["ADS_TOKEN"]

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

LIBRARIES = {
    "spurs_pub.html": "_UXNDXIYTPCQjmT3CouDPg",
    "comm_pub.html": "dTYqgxcTSr2BOuHMLakftA"
}


def fetch_library_bibcodes(library_id):
    url = f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["documents"]


def fetch_paper_details(bibcodes):
    url = "https://api.adsabs.harvard.edu/v1/search/query"

    params = {
        "q": "bibcode:(" + " OR ".join(bibcodes) + ")",
        "fl": "title,author,year,pub,bibcode",
        "rows": 500,
        "sort": "entry_date desc"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["response"]["docs"]


def format_authors(authors):
    if not authors:
        return "Unknown"

    if len(authors) <= 6:
        return ", ".join(authors)

    return ", ".join(authors[:6]) + ", et al."


def generate_html(docs):
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

    bibcodes = fetch_library_bibcodes(library_id)
    docs = fetch_paper_details(bibcodes)
    html = generate_html(docs)

    output_path = f"publications/{filename}"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

print("Finished updating all publication lists.")