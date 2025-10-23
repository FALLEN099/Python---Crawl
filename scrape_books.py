import os
import re
import time
import csv
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime

URL = "https://books.toscrape.com/"
Browser = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
Rate_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

OUTPUT_DIR = Path("books_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def get_html(url):
    r = requests.get(url, headers=Browser)
    r.raise_for_status()
    return r.text

def get_category_url(name):
    html = get_html(URL)
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("ul.nav-list ul li a"):
        if a.text.strip().lower() == name.lower():
            return urljoin(URL, a["href"])
    raise ValueError(f"Not found category '{name}'")

def parse_star(tag):
    if not tag: return None
    for cls in tag.get("class", []):
        if cls in Rate_MAP:
            return Rate_MAP[cls]
    return None

def scrape_category(category, pages=3):
    url = get_category_url(category)
    cat_dir = OUTPUT_DIR / category.lower().replace(" ", "_")
    html_backup = cat_dir / "html_backup"
    html_backup.mkdir(parents=True, exist_ok=True)
    data = []

    for p in range(pages):
        print(f"Scraping {category} category –  page {p+1}")
        html = get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        books = soup.select("article.product_pod")

        for b in books:
            title = b.h3.a["title"]
            link = urljoin(url, b.h3.a["href"])
            price = b.select_one("p.price_color").text.strip()
            star = parse_star(b.select_one("p.star-rating"))

            detail_html = get_html(link)
            d_soup = BeautifulSoup(detail_html, "html.parser")
            avail = d_soup.select_one("p.instock.availability").text.strip()

            # backup HTML
            html_name = re.sub(r"[^\w\-]+", "_", title)[:80] + ".html"
            (html_backup / html_name).write_text(detail_html, encoding="utf-8")

            data.append({
                "Title": title,
                "Price": price,
                "Availability": avail,
                "Product Page Link": link,
                "Star Rating": star
            })

        next_a = soup.select_one("li.next a")
        if not next_a:
            break
        url = urljoin(url, next_a["href"])

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = cat_dir / f"books_{category.lower()}_{ts}.json"

    with open(json_path, "w", encoding="utf-8") as f:
         json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done: saved {len(data)} books to {json_path}")

    
if __name__ == "__main__":
    for cate in ["Mystery", "Sequential Art", "Health"]:
        scrape_category(cate, pages=3)
