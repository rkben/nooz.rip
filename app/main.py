from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from tortoise.contrib.fastapi import register_tortoise

from lib import article, schema
from settings import settings

current_dir = Path(__file__).parent
data_dir = (current_dir.parent / "data")
templates = Jinja2Templates(directory=str(current_dir / "templates"))


app = FastAPI()
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")

if settings.DEBUG:
    logger.info("DEBUG MODE ENABLED")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS WILDCARD ENABLED")

register_tortoise(
    app,
    db_url="sqlite://{}".format(str(data_dir / settings.DB)),
    modules={"models": ["lib.schema"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("/favicon.ico")
async def favicon(_: Request):
    return FileResponse(str(current_dir / "static" / "favicon.ico"))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    article_count = await schema.Article.all().count()
    return templates.TemplateResponse(
        "index.tmpl",
        {"request": request, "count": article_count},
    )


@app.get("/articles/{page}", response_class=HTMLResponse)
async def page(request: Request, page: int):
    if page == 1:
        articles = await schema.Article.all().order_by("-date").limit(20)
    else:
        articles = (
            await schema.Article.all().order_by("-date").offset(page * 20).limit(20)
        )
    return templates.TemplateResponse(
        "cards.tmpl",
        {"request": request, "articles": articles, "page": page + 1},
    )


@app.get("/{url:path}", response_class=HTMLResponse)
async def article_by_url(request: Request, url: str):
    the_article = await schema.Article.get_or_none(url=url).all().first()
    if the_article is None:
        the_article = await article.new_article(url=url)
    if the_article.errors is False and settings.WRITE_DB:
        await the_article.save()
    return templates.TemplateResponse(
        "article.tmpl", {"request": request, "article": the_article}
    )
