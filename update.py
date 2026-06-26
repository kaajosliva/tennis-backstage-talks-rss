import subprocess
import json
import re
import hashlib
from datetime import datetime

FULL_FEED = "tennis-backstage-talks.xml"
TOP_FEED = "tennis-backstage-talks-TOP.xml"

def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"#\S+", "", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip()

def extract_matches(text):
    pattern = r"([A-Za-z .'-]+)\s+(\d{1,3})%\s+[–-]\s+(\d{1,3})%\s+([A-Za-z .'-]+)"
    return re.findall(pattern, text)

def make_guid(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def build_rss(items, title, description):
    rss_items = ""
    for item in items:
        rss_items += f"""
        <item>
            <title>{item['title']}</title>
            <link>{item['link']}</link>
            <guid isPermaLink="false">{item['guid']}</guid>
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
    print("Sťahujem tweety cez snscrape...")

    # Spustíme snscrape a získame JSONL výstup
    result = subprocess.run(
        ["snscrape", "--jsonl", "twitter-user", "TennisEloWorld"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Chyba pri spúšťaní snscrape")
        return

    lines = result.stdout.strip().split("\n")

    full_items = []
    top_items = []

    for line in lines:
        tweet = json.loads(line)

        raw_text = clean_text(tweet["content"])
        matches = extract_matches(raw_text)

        tweet_link = f"https://twitter.com/TennisEloWorld/status/{tweet['id']}"
        pub_date = datetime.fromisoformat(tweet["date"].replace("Z", "+00:00")).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        guid = make_guid(raw_text + pub_date)

        full_items.append({
            "title": raw_text[:40] or "Tweet",
            "content": raw_text,
            "date": pub_date,
            "guid": guid,
            "link": tweet_link
        })

        if matches:
            top_matches = []
            for m in matches:
                p1 = int(m[1])
                p2 = int(m[3])
                if p1 >= 70 or p2 >= 70:
                    top_matches.append(f"{m[0]} {m[1]}% – {m[3]}% {m[4]}")

            if top_matches:
                top_items.append({
                    "title": top_matches[0][:40],
                    "content": "\n".join(top_matches),
                    "date": pub_date,
                    "guid": guid,
                    "link": tweet_link
                })

    print("Generujem FULL feed...")
    with open(FULL_FEED, "w", encoding="utf-8") as f:
        f.write(build_rss(full_items, "Tennis Backstage Talks – Full Feed", "All tweets from TennisEloWorld"))

    print("Generujem TOP feed...")
    with open(TOP_FEED, "w", encoding="utf-8") as f:
        f.write(build_rss(top_items, "Tennis Backstage Talks – TOP Picks", "Only matches with 70%+ predictions"))

    print("Hotovo!")

if __name__ == "__main__":
    main()
