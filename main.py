from typing import Any

from fastapi import FastAPI, Request, HTTPException, status
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

@app.get("/", include_in_schema=False, name="home")
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={
        "title": "Home",
        "posts": posts
    })

@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        if post.get("id", -1) == post_id:
            return templates.TemplateResponse(request=request, name="post.html", context={
                "title": post.get("title", "post")[:25],
                "post": post
            })
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/api/posts")
def get_posts() -> list[dict[str, Any]]:
    return posts

@app.get("/api/posts/{post_id}")
def get_post(post_id: int) -> dict[str, Any]:
    for post in posts:
        if post.get("id", -1) == post_id:
            return post
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")