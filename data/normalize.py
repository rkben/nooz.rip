from bs4 import BeautifulSoup
import ujson
import csv
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
import httpx
import multiprocessing

files = Path("feedlists").glob("**/*.*")

### TO PARSE
# https://rss.app/blog/top-rss-feeds/30-best-sport-websites-to-get-rss-feeds-from
# https://rss.app/blog/top-rss-feeds/38-best-technology-websites-to-get-rss-feeds-from
# https://rss.app/blog/top-rss-feeds/15-best-crypto-websites-to-get-rss-feeds-from
# https://rss.app/blog/top-rss-feeds/20-best-finance-websites-to-get-rss-feeds-from
# https://www.theguardian.com/help/feeds


@dataclass
class Feed:
    title: str
    url: str
    description: str
    status: int = 0


ALL_FEEDS: list[Feed] = []
ALREADY_RAN: list[str] = []
CLIENT = httpx.Client(follow_redirects=True, timeout=15)


def http_get(entry: Feed) -> Feed | None:
    if entry.url in ALREADY_RAN:
        print(f"SKIP: {entry.url}")
        return None
    if "youtube" in entry.url or "youtu.be" in entry.url:
        print(f"SKIP: Youtube {entry.url}")
        return None
    if "github" in entry.url:
        print(f"SKIP: Github {entry.url}")
        return None
    if len(entry.url) < 2:
        print(f"SKIP: {entry.url}")
        return None
    print(f"GET: {entry.url}")
    try:
        req = CLIENT.get(entry.url)
    except Exception as e:
        print(f"Error: {e}\t\n{entry.url}, setting status to 404")
        entry.status = 404
        ALREADY_RAN.append(entry.url)
        return entry
    if req.status_code == 200:
        if req.text.startswith("<?xml"):
            print("Valid XML")
            soup = BeautifulSoup(req.text, "xml")
            title = soup.find("title")
            if title is not None:
                entry.title = title.text
            entry.status = req.status_code
            ALREADY_RAN.append(entry.url)
            return entry
        else:
            print("Invalid XML, setting status to 404")
            entry.status = 404
            ALREADY_RAN.append(entry.url)
            return entry
    else:
        print(f"Error: {req.status_code}, {entry.url}, setting status to 404")
        entry.status = req.status_code
        ALREADY_RAN.append(entry.url)
        return entry


def write_entry(feeds: list[Feed]):
    con = sqlite3.connect("feeds.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS feeds(title, url, description, status)")
    data = [tuple(asdict(feed).values()) for feed in feeds]
    print(f"Writing {len(data)} items to DB.")
    cur.executemany("INSERT INTO feeds VALUES(?, ?, ?, ?)", data)
    con.commit()


def gen_feed(title: str, url: str, description: str) -> Feed:
    feed = Feed(
        title=title.strip(),
        url=url.strip(),
        description=description.strip(),
    )
    ALL_FEEDS.append(feed)


def load_db():
    con = sqlite3.connect("feeds.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM feeds")
    data = cur.fetchall()
    for row in data:
        feed = Feed(*row)
        ALL_FEEDS.append(feed)
        ALREADY_RAN.append(feed.url)


for f in files:
    print(f.name)
    if f.suffix == ".opml":
        print("OPML")
        xml_file = f.read_text()
        soup = BeautifulSoup(xml_file, "xml")
        listings = soup.find_all("outline")
        for listing in listings:
            if listing.get("type", "") == "rss":
                gen_feed(
                    title=listing.get("text", ""),
                    url=listing.get("xmlUrl", ""),
                    description=listing.get("description", ""),
                )

    if f.suffix == ".json":
        print("JSON")
        json_file = f.read_text()
        j = ujson.loads(json_file)
        if isinstance(j[0], str):
            for entry in j:
                gen_feed(title="", url=entry, description="")

        if isinstance(j[0], dict):
            for entry in j:
                gen_feed(title="", url=entry["rss"], description="")

    if f.suffix == ".csv":
        print("CSV")
        with f.open("r") as csv_file:
            for row in csv.reader(csv_file):
                _, title, url = row
                gen_feed(title=title, url=url, description="")

if f.suffix == ".list":
    print("TEXT")
    txt = f.read_text()
    for line in txt.split("\n"):
        if len(line) > 1:
            gen_feed(title="", url=line.strip(), description="")

load_db()
completed = []
with multiprocessing.Pool(16) as p:
    for result in p.map(http_get, ALL_FEEDS):
        if result is not None:
            completed.append(result)
write_entry(completed)
