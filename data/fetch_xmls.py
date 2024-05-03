#!/usr/bin/env python3
import httpx
import bs4
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0"
}


def govwire():
    url = "http://www.govwire.co.uk/rss"
    client = httpx.Client(follow_redirects=True, timeout=15, headers=HEADERS)
    req = client.get(url)
    if req.status_code == 200:
        soup = bs4.BeautifulSoup(req.text, "lxml")
        for element in soup.find_all("p", {"class": "rssFeed"}):
            url = element.find("span").text
            print(url)


def grab_xml(url: str):
    client = httpx.Client(follow_redirects=True, timeout=15, headers=HEADERS)
    req = client.get(url)
    if req.status_code == 200:
        soup = bs4.BeautifulSoup(req.text, "lxml")
        for element in soup.find_all("a"):
            href_text = element.get("href", "")
            if (
                href_text.endswith(".xml")
                or href_text.endswith(".rss")
                or href_text.endswith("/feed/")
                or href_text.endswith("/feed")
                or href_text.endswith("/feeds")
                or href_text.endswith("/rss")
            ):
                print(href_text)


if __name__ == "__main__":
    # govwire()
    grab_xml(sys.argv[1])
