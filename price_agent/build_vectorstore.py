import argparse
import random
from typing import List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer


CATEGORIES = [
    "Appliances",
    "Automotive",
    "Cell_Phones_and_Accessories",
    "Electronics",
    "Musical_Instruments",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Toys_and_Games",
]


def make_synthetic_item(category: str, rng: random.Random, idx: int) -> Tuple[str, float]:
    brand = rng.choice(
        [
            "Acme",
            "Nova",
            "Apex",
            "Vertex",
            "Orion",
            "Nimbus",
            "Pulse",
            "Zenith",
            "Everest",
            "Lumen",
        ]
    )

    templates = {
        "Electronics": (
            "{brand} 4K streaming device with Wi‑Fi 6, HDR support, voice remote, and HDMI 2.1 compatibility.",
            (25, 200),
        ),
        "Appliances": (
            "{brand} energy‑efficient countertop appliance with multiple presets, stainless steel finish, and easy‑clean tray.",
            (40, 350),
        ),
        "Automotive": (
            "{brand} car care kit including microfiber towels, pH‑neutral wash, tire shine, and quick detailer spray.",
            (15, 120),
        ),
        "Cell_Phones_and_Accessories": (
            "{brand} phone accessory bundle with fast charger, braided USB‑C cable, MagSafe‑compatible mount, and rugged case.",
            (10, 150),
        ),
        "Musical_Instruments": (
            "{brand} beginner instrument package with tuner, gig bag, strap, picks, and online lesson access.",
            (60, 600),
        ),
        "Office_Products": (
            "{brand} ergonomic office accessory with adjustable height, anti‑slip base, and cable management features.",
            (15, 180),
        ),
        "Tools_and_Home_Improvement": (
            "{brand} cordless tool kit with brushless motor, two batteries, fast charger, and carrying case.",
            (70, 500),
        ),
        "Toys_and_Games": (
            "{brand} family board game with strategy elements, quick setup, and 30–45 minute playtime for ages 10+.",
            (10, 90),
        ),
    }

    template, (low, high) = templates.get(category, (
        "{brand} general product with durable build and practical everyday features.",
        (10, 200),
    ))
    description = template.format(brand=brand)

    # Create a slightly varied price distribution per category
    price = float(rng.randint(low, high))
    description = f"Category: {category}. {description} Model {idx:04d}."
    return description, price


def build_docs(n: int, seed: int) -> Tuple[List[str], List[float], List[str]]:
    rng = random.Random(seed)
    documents: List[str] = []
    prices: List[float] = []
    categories: List[str] = []

    for i in range(n):
        category = rng.choice(CATEGORIES)
        doc, price = make_synthetic_item(category, rng, i)
        documents.append(doc)
        prices.append(price)
        categories.append(category)

    return documents, prices, categories


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local Chroma vectorstore for Week 8 RAG")
    parser.add_argument("--n", type=int, default=500, help="Number of synthetic products to add")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="If set, deletes existing items from the collection before adding new ones",
    )
    args = parser.parse_args()

    client = chromadb.PersistentClient(path="products_vectorstore")
    collection = client.get_or_create_collection("products")

    if args.reset:
        existing = (collection.get().get("ids") or [])
        if existing:
            collection.delete(ids=existing)

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    documents, prices, categories = build_docs(args.n, args.seed)
    embeddings = model.encode(documents)

    ids = [f"item-{i}" for i in range(len(documents))]
    metadatas = [{"price": p, "category": c} for p, c in zip(prices, categories)]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.astype(float).tolist(),
    )

    print(f"Vectorstore built: {len(documents)} documents in products_vectorstore/ (collection='products')")


if __name__ == "__main__":
    main()
