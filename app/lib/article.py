import random
import re
import time
from datetime import datetime

import httpx
from bs4 import BeautifulSoup, NavigableString
from loguru import logger
from settings import settings
from trafilatura import extract
from ulid import ULID

from lib.schema import Article #, Keyword

RE_MD_IMG = r"!\[(.+?)\]\((.+)\)"
RE_MD_LINK = r"\[(.+?)\]\((.+)\)"
RE_IMG = re.compile(RE_MD_IMG)
RE_LINK = re.compile(RE_MD_LINK)
HOST = settings.HOST
PORT = settings.PORT
URL = f"http://{HOST}:{PORT}/"
# TODO: NRE=booll
# import spacy
# NLP = spacy.load("en_core_web_lg")
label_colors = {
    "PERSON": "rgba(0, 191, 255, 1)",
    "NORP": "rgba(255, 64, 0, 1)",
    "FAC": "rgba(255, 0, 0, 1)",
    "ORG": "rgba(255, 191, 0, 1)",
    "GPE": "rgba(255, 255, 0, 1)",
    "LOC": "rgba(95, 229, 95, 1)",
    "PRODUCT": "rgba(95, 229, 208, 1)",
    "EVENT": "rgba(95, 167, 229, 1)",
    # "WORK_OF_ART": "rgba(255, 0, 0, 1)",
    "LAW": "rgba(95, 109, 229, 1)",
    "LANGUAGE": "rgba(201, 123, 251, 1)",
    # "DATE": "rgba(0, 255, 191, 1)",
    # "TIME": "rgba(251, 123, 218, 1)",
    # "PERCENT": "rgba(251, 123, 123, 1)",
    # "MONEY": "rgba(162, 251, 123, 1)",
    # "QUANTITY": "rgba(123, 251, 196, 1)",
    # "ORDINAL": "rgba(207, 251, 123, 1)",
    # "CARDINAL": "rgba(207, 251, 123, 1)",
}

highlight_colors = {
    "PERSON": "rgba(0, 191, 255, 0.7)",
    "NORP": "rgba(255, 64, 0, 0.7)",
    "FAC": "rgba(255, 0, 0, 0.7)",
    "ORG": "rgba(255, 191, 0, 0.7)",
    "GPE": "rgba(255, 255, 0, 0.7)",
    "LOC": "rgba(95, 229, 95, 0.7)",
    "PRODUCT": "rgba(95, 229, 208, 0.7)",
    "EVENT": "rgba(95, 167, 229, 0.7)",
    # "WORK_OF_ART": "rgba(255, 0, 0, 0.7)",
    "LAW": "rgba(95, 109, 229, 0.7)",
    # "LANGUAGE": "rgba(201, 123, 251, 0.7)",
    # "DATE": "rgba(0, 255, 191, 0.7)",
    # "TIME": "rgba(251, 123, 218, 0.7)",
    # "PERCENT": "rgba(251, 123, 123, 0.7)",
    # "MONEY": "rgba(162, 251, 123, 0.7)",
    # "QUANTITY": "rgba(123, 251, 196, 0.7)",
    # "ORDINAL": "rgba(207, 251, 123, 0.7)",
    # "CARDINAL": "rgba(207, 251, 123, 0.7)",
}

# degen trekkies
quotes = [
    "A man either lives life as it happens to him, meets it head-on and licks it, or he turns his back on it and starts to wither away. — Dr. Boyce",
    "Logic is the beginning of wisdom, not the end. — Spock",
    "You may find that having is not so pleasing a thing as wanting. This is not logical, but it is often true. — Spock",
    "Live now; make now always the most precious time. Now will never come again. — Jean-Luc Picard",
    "Sometimes a feeling is all we humans have to go on. — Captain Kirk",
    "With the first link, the chain is forged. The first speech censored, the first thought forbidden, the first freedom denied, chains us all irrevocably. — Jean-Luc Picard",
    "The prejudices people feel about each other disappear when they get to know each other. — Captain Kirk",
    "If we’re going to be damned, let’s be damned for what we really are. — Jean-Luc Picard",
    "Insufficient facts always invite danger. — Spock",
    "Perhaps man wasn’t meant for paradise. Maybe he was meant to claw, to scratch all the way. — Captain Kirk",
    "In critical moments, men sometimes see exactly what they wish to see. — Spock",
    "Compassion: that’s the one thing no machine ever had. Maybe it’s the one thing that keeps men ahead of them. — Dr. McCoy",
    "Change is the essential process of all existence. — Spock",
    "Without followers, evil cannot spread. — Spock",
    "Our species can only survive if we have obstacles to overcome. You remove those obstacles. Without them to strengthen us, we will weaken and die. — Captain Kirk",
    "Curious, how often you humans manage to obtain that which you do not want. — Spock",
    "One man cannot summon the future. But one man can change the present! — Spock",
    "To all mankind — may we never find space so vast, planets so cold, heart and mind so empty that we cannot fill them with love and warmth. — Garth",
    "You know the greatest danger facing us is ourselves, and irrational fear of the unknown. There is no such thing as the unknown. Only things temporarily hidden, temporarily not understood. — Captain Kirk",
    "A species that enslaves other beings is hardly superior — mentally or otherwise. — Captain Kirk",
]


# async def ner(text: str) -> str:
#     # we do NER here and replace text inline with a HTML span elem
#     if "http" in text:
#         return text
#     doc = NLP(text)
#     offset = 0
#     fancy = '<span style="background-color: {color0}; color: #262626; padding: 3px; border-radius: 5px;">{text}<span style="background-color: {color1}; font-size: 12px; padding: 0.3em; text-decoration: overline;"> {label}</span></span>'
#     for ent in doc.ents:
#         if ent.label_ not in highlight_colors:
#             # bail if we dont care about the label, hence the comments
#             continue
#         t = {}
#         t["text"] = ent.text
#         t["start_char"] = ent.start_char + offset
#         t["end_char"] = ent.end_char + offset
#         t["label"] = ent.label_
#         t["color0"] = highlight_colors[ent.label_]
#         t["color1"] = label_colors[ent.label_]
#         abc = fancy.format(**t)
#         # replace in line
#         text = text[: ent.start_char + offset] + abc + text[ent.end_char + offset :]
#         offset += len(abc) - len(ent.text)
#         # TODO better keyword handling
#         # kw = await Keyword.get_or_none(keyword=ent.text)
#         # if kw is not None:
#         #     kw.count += 1
#         # else:
#         #     kw = Keyword(
#         #         keyword=ent.text,
#         #         count=1,
#         #     )
#         # # logger.debug(f"Create/Update {kw}")
#         # await kw.save()
#     return text


async def probably_banner(text: str) -> str:
    soup = BeautifulSoup(text, "lxml")
    meta_tags = soup.find_all("meta")
    for elem in meta_tags:
        if elem.attrs.get("property", False) == "og:image":
            return elem.attrs.get("content", None)
        elif elem.attrs.get("name", False) == "twitter:image":
            return elem.attrs.get("content", None)


async def links(element, text: str) -> str:
    link = ' <a href="/{}">{}</a> '
    text = text.replace(
        element.text.strip(),
        link.format(
            element.attrs["target"],
            element.text.strip(),
        ),
    )
    return text


async def banner_img(element) -> str | None:
    print(element)
    src = element.attrs.get("src", "https://placehold.co/600x400.png")
    if src.startswith("/"):
        return None
    return src


async def img(element) -> str | None:
    print(element)
    src = element.attrs.get("src", "https://placehold.co/600x400.png")
    alt = element.attrs.get("alt", "N/A")
    if src.startswith("/"):
        return None
    image = f'<img src="{src}" alt="{alt}" style="max-width:480px;">\n'
    figcaption = f"<figcaption>{alt}</figcaption>\n"
    return f"<figure>{image} {figcaption}</figure>"


async def header(element):
    return f"<h2>{element.text.strip()}</h2>\n"


async def paragraph(element) -> str:
    # TODO: check settings, NER=bool
    # text = await ner(element.text.strip())
    text = element.text
    if isinstance(element, NavigableString):
        return f"<p>{text.strip()}</p>\n"
    for tag in element.children:
        if tag.name == "ref":
            try:
                text = await links(tag, text)
            # GROK
            except:
                pass
    return f"<p>{text.strip()}</p>\n"


async def errored_article(url: str, fetch: float) -> Article:
    article = Article(
        version="N/A",
        date=datetime.utcnow(),
        url=f'<a href="{url}">{url}</a>',
        source_name="N/A",
        title="Oh No!!",
        authors="N/A",
        banner_img="https://placehold.co/600x400.png",
        body=f"<i>{random.choice(quotes)}</i>",
        summary="<p>There was a error trying to parse this page, we've logged it and will attempt to address it at some point</p>",
        errors=True,
        parse_time=0.0,
        ner_time=0.0,
        fetch_time=fetch,
    )
    return article


async def new_article(url: str) -> Article:
    logger.info(f"Fetching new URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Accept-Language": "en-US,en;q=0.9,la;q=0.8",
        "Referer": "https://www.bbc.com/",
    }
    fetch_start = time.time()
    async with httpx.AsyncClient(
        headers=headers, follow_redirects=True, timeout=10
    ) as client:
        req = await client.get(url=url, headers=headers, follow_redirects=True)
    fetch_end = time.time()
    if req.status_code != 200:
        return await errored_article(url, round(fetch_end - fetch_start, 2))
    else:
        parse_start = time.time()
        bare = extract(
            req.text,
            output_format="xml",
            include_images=True,
            include_links=True,
            include_comments=False,
            favor_recall=True,
            include_formatting=True,
            include_tables=True,
        )
        first_img = None
        if bare is None:
            return await errored_article(url, round(fetch_end - fetch_start, 2))

        # grab banner image?????
        first_img = await probably_banner(req.text)

        # parse XML result from trafilacunt
        soup = BeautifulSoup(bare, "lxml")
        document = soup.find("doc").attrs
        main = soup.find("main")
        parsed = ""
        # OH DEAR
        for elem in main.children:
            match elem.name:
                case "p":
                    parsed += await paragraph(elem)
                case "graphic":
                    if first_img is None:
                        first_img = await banner_img(elem)
                case "hi":
                    parsed += await header(elem)
                case _:
                    if len(elem.text) > 2:
                        parsed += await header(elem)

        parse_end = time.time()
        article = Article(
            version=str(ULID()),
            date=document.get("date", datetime.utcnow()),
            url=url.strip(),
            source_name=document.get("sitename", "Unknown"),
            title=document.get("title", "Unknown"),
            authors=document.get("author", "Unknown"),
            banner_img=(
                first_img
                if first_img is not None
                else "https://placehold.co/600x400.png"
            ),
            body=parsed,
            summary=document.get("description", "Unknown"),
            errors=False,
            parse_time=round(parse_end - parse_start, 2),
            ner_time=0.0,
            fetch_time=round(fetch_end - fetch_start, 2),
        )
        return article
