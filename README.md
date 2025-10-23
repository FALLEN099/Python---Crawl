Part 1 – Scraper (scrape_books.py): crawl categories from https://books.toscrape.com
and save JSON per category (+ raw product HTML backup).

Part 2 – External API Integration (add_country.py): call REST Countries (with file cache) and add a random publisher_country for each book → writes books_with_country.json into each category folder.

Part 3 – REST API (app.py): FastAPI that loads books_with_country.json on startup, authorization (header x-api-key), and serves a simple frontend at /frontend.

books_output: folder save scraper data

requirements.txt: required libraries



# 0) Install the required libraries in requirements.txt
pip install -r requirements.txt


# 1) Part 1 Scrape
Run python scrape_books.py
# 2)Part 2 External API Integration Add country
Run python add_country.py

# 3)Part 3 Build Your Own REST API (with auth header API Key = "myapikey" )
Run sever:
uvicorn app:app --reload --port 8000

# 4) Use it with API Swagger or web interface
# Swagger:  http://127.0.0.1:8000/docs
# Frontend: http://127.0.0.1:8000/frontend
