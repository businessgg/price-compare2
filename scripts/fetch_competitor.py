"""
Competitor website se products aur prices nikalta hai.

Ye script 2 tareeqon se try karta hai:
1. JSON-LD structured data (bohat sari ecommerce sites SEO ke liye ye data
   apne HTML mein chupa ke rakhti hain — is se sabse reliable data milta hai)
2. Agar JSON-LD na mile, to config.json mein diye gaye CSS selectors use karta hai
   (ye competitor site dekh kar set karne parte hain, kyunke har website ka
   HTML structure alag hota hai)
"""
import json
import re
import requests
from bs4 import BeautifulSoup


def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def extract_price(text: str):
    if not text:
        return None
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def try_jsonld(soup: BeautifulSoup) -> list:
    """JSON-LD (schema.org Product) data se products nikalne ki koshish."""
    products = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "Product":
                name = item.get("name")
                offers = item.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = offers.get("price")
                availability = offers.get("availability", "")
                url = item.get("url", "")
                if name and price:
                    products.append({
                        "name": name.strip(),
                        "price": float(price),
                        "url": url,
                        "available": "OutOfStock" not in availability,
                    })
    return products


def try_selectors(soup: BeautifulSoup, config: dict) -> list:
    """config.json mein diye gaye CSS selectors se products nikalna."""
    products = []
    product_sel = config.get("product_selector")
    name_sel = config.get("name_selector")
    price_sel = config.get("price_selector")

    if not product_sel:
        return products

    for card in soup.select(product_sel):
        name_el = card.select_one(name_sel) if name_sel else None
        price_el = card.select_one(price_sel) if price_sel else None

        name = name_el.get_text(strip=True) if name_el else None
        price = extract_price(price_el.get_text(strip=True)) if price_el else None

        if name and price:
            products.append({
                "name": name,
                "price": price,
                "url": "",
                "available": True,
            })
    return products


def fetch_competitor_products(competitor_config: dict) -> list:
    url = clean_url(competitor_config["url"])
    resp = requests.get(url, timeout=20, headers={
        "User-Agent": "Mozilla/5.0 (price-compare-bot)"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    products = try_jsonld(soup)
    if not products:
        products = try_selectors(soup, competitor_config)

    return products


if __name__ == "__main__":
    import sys
    with open("config.json") as f:
        config = json.load(f)

    comp_config = config["competitor"]
    if "PUT_" in comp_config["url"]:
        print("ERROR: config.json mein competitor ka URL dalein.")
        sys.exit(1)

    result = fetch_competitor_products(comp_config)
    with open("data/competitor_products.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"{len(result)} competitor products mil gaye aur data/competitor_products.json mein save ho gaye.")
    if not result:
        print("Koi product nahi mila. Shayad is site ke liye config.json mein CSS selectors set karne parenge.")
