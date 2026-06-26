import requests
import re
from datetime import datetime

# Twitter API cez Nitter (bez tokenu)
NITTER_URL = "NITTER_URL = "https://nitter.poast.org/TennisEloWorld/rss"

# Súbory, ktoré budeme generovať
FULL_FEED = "tennis-backstage-talks.xml"
TOP_FEED = "tennis-backstage-talks-TOP.xml"

def clean_text(text):
    # Odstránenie hashtagov, emotikonov, URL, komentárov
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"#\S+", "", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    text = text.strip()
    return text

def extract_matches(text):
    # Formát: "Meno 32% – 68% Meno"
    pattern = r"([A-Za-z .'-]+)\s+(\d{1,3})%\s+[–-]\s+(\d{1,3})%\s+([A-Za-z .'-]+)"
    return re.findall(pattern, text)

def build_rss(items, title, description):
    rss_items = ""
    for item in items:
        rss_items += f"""
        <item>
            <title>{item['title']}</title>
            <description><![CDATA[{item['content']}]]></description>
            <pubDate>{item['date']}</pubDate>
        </item>
        """

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{title}</title>
    <link>https://twitter.com/TennisEloWorld</link>
    <description>{description}</description>
    {rss_items}
  </channel>
</rss>
"""

def main():
    print("Sťahujem tweety...")
    r = requests.get(NITTER_URL)
    if r.status_code != 200:
        print("Chyba pri sťahovaní tweetov")
        return

    xml = r.text

    # Extrakcia položiek z RSS
    entries = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)

    full_items = []
    top_items = []

    for entry in entries:
        title = re.search(r"<title>(.*?)</title>", entry)
        desc = re.search(r"<description>(.*?)</description>", entry, re.DOTALL)
        date = re.search(r"<pubDate>(.*?)</pubDate>", entry)

        if not desc:
            continue

        raw_text = clean_text(desc.group(1))
        matches = extract_matches(raw_text)

        if not matches:
            continue

        # FULL FEED
        full_items.append({
            "title": "Tennis Backstage Talks",
            "content": raw_text,
            "date": date.group(1) if date else datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        })

        # TOP FEED (≥ 70 %)
        top_matches = []
        for m in matches:
            p1 = int(m[1])
            p2 = int(m[3])
            if p1 >= 70 or p2 >= 70:
                top_matches.append(f"{m[0]} {m[1]}% – {m[3]}% {m[4]}")

        if top_matches:
            top_items.append({
                "title": "TOP Picks",
                "content": "\n".join(top_matches),
                "date": date.group(1) if date else datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            })

    # Uloženie feedov
    print("Generujem FULL feed...")
    with open(FULL_FEED, "w", encoding="utf-8") as f:
        f.write(build_rss(full_items, "Tennis Backstage Talks – Full Feed", "All matches + tournaments"))

    print("Generujem TOP feed...")
    with open(TOP_FEED, "w", encoding="utf-8") as f:
        f.write(build_rss(top_items, "Tennis Backstage Talks – TOP Picks", "Only matches with 70%+"))

    print("Hotovo!")

if __name__ == "__main__":
    main()
