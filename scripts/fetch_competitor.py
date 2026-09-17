"""
Competitor website (Japan Electronics) se products aur prices nikalta hai.

Chunke competitor bhi Shopify par hai, hum wahi reliable /products.json
endpoint use karte hain jo fetch_shopify.py mein use hota hai — isse
data bohat accurate milta hai (koi guesswork wale CSS selectors nahi chahiye).

Agar kabhi competitor Shopify se hat jaye, to ye script neeche diye gaye
fallback (JSON-LD ya CSS selectors) par khud switch ho jayega.
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


def fetch_shopify_style(store_url: str) -> list:
    """Shopify ke public /products.json endpoint se products nikalna."""
    base_url = clean_url(store_url)
    products = []
    page = 1

    while True:
        endpoint = f"{base_url}/products.json?limit=250&page={page}"
        try:
            resp = requests.get(endpoint, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (price-compare-bot)"
            })
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Shopify endpoint fail hua ({e}), fallback try karenge.")
            return []

        page_products = data.get("products", [])
        if not page_products:
            break

        for p in page_products:
            title = p.get("title", "").strip()
            variants = p.get("variants", [])
            if not variants:
                continue
            price = variants[0].get("price")
            handle = p.get("handle", "")
            product_url = f"{base_url}/products/{handle}"

            products.append({
                "name": title,
                "price": float(price) if price else None,
                "url": product_url,
                "available": any(v.get("available") for v in variants),
            })

        page += 1
        if page > 20:
            break

    return products


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
    """Fallback 1: JSON-LD (schema.org Product) data se products nikalna."""
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
    """Fallback 2: config.json ke CSS selectors se products nikalna."""
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
    url = competitor_config["url"]

    # Pehle Shopify ka reliable tareeqa try karein
    products = fetch_shopify_style(url)
    if products:
        return products

    # Agar Shopify na ho, HTML fallback try karein
    clean = clean_url(url)
    resp = requests.get(clean, timeout=20, headers={
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
    import os
    with open("config.json") as f:
        config = json.load(f)

    comp_config = config["competitor"]
    if "PUT_" in comp_config["url"]:
        print("ERROR: config.json mein competitor ka URL dalein.")
        sys.exit(1)

    result = fetch_competitor_products(comp_config)
    os.makedirs("data", exist_ok=True)
    with open("data/competitor_products.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"{len(result)} competitor products mil gaye aur data/competitor_products.json mein save ho gaye.")
    if not result:
        print("Koi product nahi mila. Shayad is site ke liye config.json mein CSS selectors set karne parenge.")
