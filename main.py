import os
import re
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional, Tuple

load_dotenv(override=True)

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_KEY:
    raise SystemExit(
        "ERROR: OPENAI_API_KEY not found. Set it in the environment or .env file.")

client = OpenAI(api_key=OPENAI_KEY)    


def fetch_products() -> List[dict]:
    url = "https://hackathon-apis.vercel.app/api/products"
    resp = requests.get(url, timeout=10)
    return resp.json() if resp.status_code == 200 else []


def filter_products(products: List[dict], max_price: Optional[float] = None, keyword: Optional[str] = None) -> List[dict]:
    results = products
    if max_price is not None:
        results = [p for p in results if (
            p.get("price") is not None and float(p.get("price", 0)) <= max_price)]
    if keyword:
        kw = keyword.lower()
        results = [p for p in results if kw in (
            p.get("name", "").lower() + " " + p.get("description", "").lower())]
    return results


def parse_user_query(query: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Try to extract a max_price and a keyword from a user query.
    Examples handled:
      - "Show me products under $300"
      - "Find chairs under 200"
      - "Find me a blue lamp"
      - "chairs"
    Returns (max_price_or_None, keyword_or_None)
    """
    q = query.lower().strip()

    price_match = re.search(
        r"(?:under|below|less than|<|<=)\s*\$?\s*([0-9]+(?:\.[0-9]+)?)", q)
    if not price_match:
        # fallback if they typed $300
        price_match = re.search(r"\$([0-9]+(?:\.[0-9]+)?)", q)
    max_price = float(price_match.group(1)) if price_match else None

    cleaned = re.sub(r"\$[0-9]+(?:\.[0-9]+)?", " ", q)
    cleaned = re.sub(
        r"\b(under|below|less than|find|show|me|products|product|for|a|an|the|in|with|and|to|i|want)\b", " ", cleaned)
    cleaned = re.sub(r"[^\w\s\-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    keyword = cleaned if cleaned else None
    if keyword:
        if re.fullmatch(r"[0-9\s]+", keyword):
            keyword = None

    return max_price, keyword


def build_prompt_for_model(query: str, products: List[dict], filtered: List[dict]) -> str:
    """
    Build a strict prompt that instructs the model to answer ONLY using the given products.
    Provide filtered list first for the model to base its answer on.
    """
    def short(p):
        return {
            "name": p.get("name"),
            "price": p.get("price"),
            "_id": p.get("_id"),
            "category": p.get("category", {}).get("name") if isinstance(p.get("category"), dict) else p.get("category"),
            "description": p.get("description", "")
        }

    context = (
        "You are a shopping assistant. You MUST answer only using the product list provided. "
        "Do NOT invent products or prices. If nothing matches, say: 'No matching products found.'\n\n"
    )

    items = filtered if filtered else products[:10]
    items_short = [short(p) for p in items]

    prompt = (
        context
        + "User query:\n"
        + query
        + "\n\nProducts (JSON array):\n"
        + json.dumps(items_short, indent=2)
        + "\n\nAnswer concisely and refer to product names and exact prices from the list above."
    )
    return prompt


def shopping_agent_query(query: str, products: List[dict]) -> str:
    max_price, keyword = parse_user_query(query)

    filtered = filter_products(products, max_price=max_price, keyword=keyword)

    if filtered:
        deterministic_lines = []
        for p in filtered:
            deterministic_lines.append(
                f"- {p.get('name')} (ID: {p.get('_id')}): ${p.get('price')} — {p.get('category', {}).get('name') if isinstance(p.get('category'), dict) else p.get('category')}")
        deterministic_result = "MATCHING PRODUCTS:\n" + \
            "\n".join(deterministic_lines)
    else:
        deterministic_result = "No matching products found (based on exact filter)."

    prompt = build_prompt_for_model(query, products, filtered)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only uses the provided product list."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        model_answer = response.choices[0].message.content.strip()
    except Exception as e:
        model_answer = f"[Model call failed] {e}"

    return deterministic_result + "\n\nAI Summary:\n" + model_answer


def pretty_print_products(products: List[dict], limit: int = 10):
    for i, p in enumerate(products[:limit], start=1):
        print(f"{i}. {p.get('name')} — ${p.get('price')}")
        if p.get("category"):
            cat = p.get("category").get("name") if isinstance(
                p.get("category"), dict) else p.get("category")
            print(f"   Category: {cat}")
        desc = p.get("description", "")
        if desc:
            print(f"   {desc[:120]}{'...' if len(desc) > 120 else ''}")
        print()


if __name__ == "__main__":
    print("Fetching products...")
    products = fetch_products()
    print(f"Products fetched: {len(products)}\n")

    print("Type queries like:")
    print("  - Show me products under $300")
    print("  - Find chairs under 200")
    print("  - Find blue lamp")
    print("Type 'exit' to quit.\n")

    while True:
        user_q = input("Your query: ").strip()
        if not user_q:
            continue
        if user_q.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        result = shopping_agent_query(user_q, products)
        print("\n" + "=" * 60 + "\n")
        print(result)
        print("\n" + "=" * 60 + "\n")
