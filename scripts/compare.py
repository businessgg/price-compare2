"""
Dono lists (apni store + competitor) ke products ko naam se fuzzy-match
karta hai aur price compare karke ek final report (JSON) banata hai
jo dashboard dikhayega.
"""
import json
from datetime import datetime, timezone
from rapidfuzz import fuzz, process


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def build_comparison(my_products, competitor_products, threshold=70):
    comp_names = [p["name"] for p in competitor_products]
    results = []
    matched_competitor_indices = set()

    for mine in my_products:
        match = process.extractOne(
            mine["name"], comp_names, scorer=fuzz.token_sort_ratio
        )

        row = {
            "product_name": mine["name"],
            "my_price": mine.get("price"),
            "my_available": mine.get("available"),
            "my_url": mine.get("url"),
            "competitor_name": None,
            "competitor_price": None,
            "competitor_available": None,
            "competitor_url": None,
            "match_confidence": 0,
            "status": "only_us",
            "price_diff": None,
            "cheaper": None,
        }

        if match and match[1] >= threshold:
            idx = comp_names.index(match[0])
            comp = competitor_products[idx]
            matched_competitor_indices.add(idx)

            row["competitor_name"] = comp["name"]
            row["competitor_price"] = comp.get("price")
            row["competitor_available"] = comp.get("available")
            row["competitor_url"] = comp.get("url")
            row["match_confidence"] = round(match[1], 1)
            row["status"] = "matched"

            if row["my_price"] is not None and row["competitor_price"] is not None:
                diff = round(row["my_price"] - row["competitor_price"], 2)
                row["price_diff"] = diff
                if diff < 0:
                    row["cheaper"] = "us"
                elif diff > 0:
                    row["cheaper"] = "competitor"
                else:
                    row["cheaper"] = "same"

        results.append(row)

    # Competitor ke wo products jo hamare pass bilkul nahi hain
    for idx, comp in enumerate(competitor_products):
        if idx not in matched_competitor_indices:
            results.append({
                "product_name": comp["name"],
                "my_price": None,
                "my_available": None,
                "my_url": None,
                "competitor_name": comp["name"],
                "competitor_price": comp.get("price"),
                "competitor_available": comp.get("available"),
                "competitor_url": comp.get("url"),
                "match_confidence": 0,
                "status": "only_competitor",
                "price_diff": None,
                "cheaper": None,
            })

    return results


if __name__ == "__main__":
    with open("config.json") as f:
        config = json.load(f)

    threshold = config.get("matching", {}).get("similarity_threshold", 70)

    my_products = load("data/my_products.json")
    competitor_products = load("data/competitor_products.json")

    comparison = build_comparison(my_products, competitor_products, threshold)

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "my_store_name": config["my_store"]["name"],
        "competitor_name": config["competitor"]["name"],
        "total_my_products": len(my_products),
        "total_competitor_products": len(competitor_products),
        "matched_count": sum(1 for r in comparison if r["status"] == "matched"),
        "results": comparison,
    }

    with open("docs/comparison.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Comparison ban gaya: {output['matched_count']} products match hue.")
