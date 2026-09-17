"""
Shopify store se products aur prices nikalta hai.
Shopify ka public /products.json endpoint use hota hai — kisi API key ki zaroorat nahi
agar store normal/public hai.
"""
import json
import requests


def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def fetch_shopify_products(store_url: str) -> list:
    """
    Shopify store ke saare products (naam + price) list karta hai.
    Pagination handle karta hai (250 products per page, Shopify ka max).
    """
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
            print(f"Error fetching {endpoint}: {e}")
            break

        page_products = data.get("products", [])
        if not page_products:
            break

        for p in page_products:
            title = p.get("title", "").strip()
            variants = p.get("variants", [])
            if not variants:
                continue
            # Sabse pehla variant ka price le lete hain (aam tor par default)
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
        if page > 20:  # safety limit
            break

    return products


if __name__ == "__main__":
    import os
    import sys
    with open("config.json") as f:
        config = json.load(f)

    store_url = config["my_store"]["url"]
    if "PUT_YOUR" in store_url:
        print("ERROR: config.json mein apni Shopify store ka URL dalein.")
        sys.exit(1)

    result = fetch_shopify_products(store_url)
    os.makedirs("data", exist_ok=True)
    with open("data/my_products.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"{len(result)} products mil gaye aur data/my_products.json mein save ho gaye.")
