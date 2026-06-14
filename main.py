from typing import Any

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

posts: list[dict[str, Any]] = [
    {
        "id": 1,
        "author": "Someone",
        "title": "Chicken",
        "content": "Who crossed the road again?",
        "date_posted": "June 14, 2026",
    },
    {
        "id": 2,
        "author": "Another",
        "title": "Chicken",
        "content": "Who crossed the road again?",
        "date_posted": "June 14, 2026",
    }
]

@app.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.jinja", context={
        "title": "Home",
        "posts": posts
    })

@app.get("/api/posts")
def get_posts() -> list[dict[str, Any]]:
    return posts