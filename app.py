import os, json, logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Header, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "books_output")).resolve()
API_KEY = os.getenv("API_KEY", "myapikey").strip() 
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("books_api")


class Book(BaseModel):
    title: str = Field(..., description="Book title")
    price: Optional[str] = None
    availability: Optional[str] = None
    product_page_link: Optional[str] = None
    star_rating: Optional[int] = None
    publisher_country: Optional[str] = None


BOOKS_DB: List[Book] = []


Books = {
    "title": ["Title", "title"],
    "price": ["Price", "price"],
    "availability": ["Availability", "availability"],
    "product_page_link": ["Product Page Link", "ProductPageURL", "product_page_link", "Product Page URL"],
    "star_rating": ["Star Rating", "StarRating", "star_rating"],
    "publisher_country": ["publisher_country", "Publisher Country"],
}

def pick_first(d: Dict[str, Any], keys: List[str]):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None

def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title":              pick_first(row, Books["title"]),
        "price":              pick_first(row, Books["price"]),
        "availability":       pick_first(row, Books["availability"]),
        "product_page_link":  pick_first(row, Books["product_page_link"]),
        "star_rating":        pick_first(row, Books["star_rating"]),
        "publisher_country":  pick_first(row, Books["publisher_country"]),
    }


def load_books_from_output(output_dir: Path) -> List[Book]:
    books: List[Book] = []
    if not output_dir.exists():
        log.warning("OUTPUT_DIR not found: %s", output_dir)
        return books

    candidate_files: List[Path] = []
    for sub in output_dir.iterdir():
        if not sub.is_dir():
            continue
        candidate_files.extend(sub.glob("books_with_country.json"))

    for f in candidate_files:
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
            for r in rows:
                n = normalize_row(r)
                if not n.get("title"):
                    continue
                books.append(Book(**n))
        except Exception as e:
            log.error("Cannot read %s: %s", f, e)

    log.info("Loaded %d books from %d file(s)", len(books), len(candidate_files))
    return books


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-api-key header")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid x-api-key")
    return True


app = FastAPI(title="Books API (Protected)", version="1.0.0")

@app.on_event("startup")
def startup():
    global BOOKS_DB
    BOOKS_DB = load_books_from_output(OUTPUT_DIR)


@app.get("/books", response_model=List[Book], dependencies=[Depends(require_api_key)])
def get_books(country: Optional[str] = Query(default=None, description="Filter by publisher_country")):
    if country:
        return [b for b in BOOKS_DB if (b.publisher_country or "").strip().lower() == country.strip().lower()]
    return BOOKS_DB


@app.post("/books", response_model=Book, status_code=201, dependencies=[Depends(require_api_key)])
def add_book(book: Book):
    for b in BOOKS_DB:
        if b.title.strip().lower() == book.title.strip().lower():
            raise HTTPException(status_code=409, detail="Book already exists")
    BOOKS_DB.append(book)
    return book


@app.delete("/books/{title}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_book(title: str):
    global BOOKS_DB
    idx = next((i for i, b in enumerate(BOOKS_DB) if b.title.strip().lower() == title.strip().lower()), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Book not found")
    BOOKS_DB.pop(idx)
    return JSONResponse(status_code=204, content=None)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "books_loaded": len(BOOKS_DB), "output_dir": str(OUTPUT_DIR)}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return HTMLResponse(status_code=204)
# phục vụ thư mục static/
app.mount("/static", StaticFiles(directory="static"), name="static")

# route tiện lợi để mở giao diện
@app.get("/frontend", include_in_schema=False)
def serve_frontend():
    file_path = Path("static/frontend.html")
    if not file_path.exists():
        return HTMLResponse("<h3>frontend.html not found in /static</h3>", status_code=404)
    return FileResponse(file_path)
