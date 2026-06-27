# FastAPI Blog Site

A small full-stack blog application built with FastAPI, SQLAlchemy, Jinja2, and JWT-based authentication. The project is based on Corey Schafer's FastAPI tutorial series, but it follows a more structured layout with a dedicated service layer and clearer separation of concerns.

## Overview

This app lets users:

- register and log in securely
- create, edit, and delete blog posts
- view posts by author
- upload and manage a profile picture
- browse paginated content through a server-rendered interface

It combines a REST-style API with server-rendered templates, so it can serve both interactive browser pages and API endpoints from the same application.

## Features

- User authentication with JWT
- Password hashing using Argon2
- CRUD operations for posts
- Author-based post views
- Profile picture upload and deletion
- Responsive templates with Jinja2
- Custom pagination with skip/limit controls and page-window navigation
- Async SQLAlchemy with SQLite

## Tech Stack

- FastAPI
- SQLAlchemy (async)
- Pydantic
- Jinja2
- JWT authentication
- Python-Multipart for form/file uploads
- SQLite

## Project Structure

```text
.
├── core/              # app and template setup
├── exceptions/        # custom exception classes
├── handlers/          # exception handlers
├── routers/           # API routes
├── security/          # auth-related helpers
├── services/          # business logic layer
├── static/            # CSS, JS, media assets
├── templates/         # Jinja templates
├── config.py          # app settings
├── database.py        # database connection and base model
├── main.py            # app entrypoint and page routes
├── models.py          # SQLAlchemy models
├── schemas.py         # request/response schemas
└── requirements.txt   # Python dependencies
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/HyperNaser/blog-site
cd blog-site
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with at least:

```env
SECRET_KEY=your-secret-key
```

### 5. Run the development server

```bash
fastapi dev main.py
```

Then open your browser at:

```text
http://127.0.0.1:8000
```

## API Overview

The app exposes API routes under:

- `/api/users` for registration, login, profile data, and profile image management
- `/api/posts` for creating, reading, updating, and deleting posts

The browser pages are served through routes like:

- `/` for the home page
- `/posts/{post_id}` for single-post pages
- `/users/{user_id}/posts` for author-specific post lists
- `/login`, `/register`, and `/account`

## Pagination Approach

Pagination is implemented with a simple `skip`/`limit` approach and is passed into the templates for page navigation. This differs slightly from the original tutorial flow and gives the project a more customized browsing experience.

## Notes

This project is a solid foundation for a personal blog and learning project. I plan to continue improving it over time with features such as:

- AI-assisted post generation or summaries
- comments and likes
- richer admin tools
- better testing coverage
- deployment to a cloud platform

## Inspiration

This project was developed based on the FastAPI tutorial playlist by Corey Schafer, while keeping the implementation aligned with my own preferred structure and refactoring style:

- https://www.youtube.com/playlist?list=PL-osiE80TeTsak-c-QsVeg0YYG_0TeyXI
- https://www.youtube.com/@coreyms
