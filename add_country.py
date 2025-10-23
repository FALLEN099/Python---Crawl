import pandas as pd
import requests, random, json
from pathlib import Path
import time
from typing import Optional, List
OUTPUT_DIR = Path("books_output")


COUNTRIES_CACHE_FILE = Path(".countries_cache.json")
Archive_date = 24 * 60 * 60 
def _read_cache() -> Optional[List[str]]:
    if not COUNTRIES_CACHE_FILE.exists():
        return None
    try:
        payload = json.loads(COUNTRIES_CACHE_FILE.read_text(encoding="utf-8"))
        ts = payload.get("cached_at")
        if ts is None:
            return None
        if (time.time() - ts) > Archive_date:
            return None
        countries = payload.get("countries") or []
        if isinstance(countries, list) and countries:
            return countries
    except Exception:
        return None
    return None


def _write_cache(countries: List[str]) -> None:
    payload = {"cached_at": time.time(), "countries": countries}
    COUNTRIES_CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_countries():
    cached = _read_cache()
    if cached:
        print(f" Use cache: {len(cached)} Country ( {Archive_date}s)")
        return cached
    headers = {"User-Agent": "Mozilla/5.0"}
    url_api = "https://restcountries.com/v3.1/all?fields=name"

    r = requests.get(url_api, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    names = []
    for c in data:
        if "name" in c:
            if isinstance(c["name"], dict):
                name = c["name"].get("common") or c["name"].get("official")
            else:
                name = c["name"]
            if name:
                names.append(name)
    if names:
        _write_cache(names)
        return sorted(set(names))
    raise RuntimeError("Error get country!")

def newest_data(cat_dir):
    
    jsons = list(cat_dir.glob("*.json"))
    if not jsons:
        return None
    return max(jsons, key=lambda p: p.stat().st_mtime)

def attach_country(json_path, countries):
    
    df = pd.read_json(json_path)
    df["publisher_country"] = [random.choice(countries) for _ in range(len(df))]

    out_json = json_path.parent / "books_with_country.json"
    df.to_json(out_json, orient="records", force_ascii=False, indent=2)

    print(f"Add country done: {json_path.parent.name}")
    return out_json

if __name__ == "__main__":
    countries = fetch_countries()
    print(f"Get {len(countries)} countries.")

    for cat_dir in OUTPUT_DIR.iterdir():
        if cat_dir.is_dir():
            json_path = newest_data(cat_dir)
            if json_path:
                attach_country(json_path, countries)
