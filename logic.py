from collections import Counter, defaultdict
import os
import pickle
import pandas as pd
import serpapi
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SERPAPI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Не найден SERPAPI_API_KEY в .env. "
        "Создайте файл .env и добавьте строку SERPAPI_API_KEY=ваш_ключ"
    )
client = serpapi.Client(api_key=API_KEY)

# ✅ 1. Определяем функцию
def load_indexes(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        return pickle.load(f)

# ✅ 2. Загружаем и сразу распаковываем в переменные
INDEXES = load_indexes("indexes.pkl")
item_to_orders          = INDEXES["item_to_orders"]
order_to_items          = INDEXES["order_to_items"]
item_to_supplier_count  = INDEXES["item_to_supplier_count"]
item_to_torgs           = INDEXES["item_to_torgs"]


def get_frequent_companions(
    target_item: str,
    item_to_orders,
    order_to_items,
    item_to_supplier_count,
    item_to_torgs,
    top_n: int = 10,
):
    if target_item not in item_to_orders:
        return None, f"Номенклатура '{target_item}' не найдена в закупках!"

    related_items = Counter()
    orders_with_target = item_to_orders[target_item]

    for order_id in orders_with_target:
        for item in order_to_items[order_id]:
            if item != target_item:
                related_items[item] += 1

    results = []
    for item, count_ab in related_items.items():
        count_b = len(item_to_orders[item])
        probability = count_ab / count_b

        if count_b > 1:
            supplier_count = item_to_supplier_count.get(item, 0)
            results.append(
                (item, count_ab, count_b, round(probability, 3), supplier_count, item_to_torgs.get(item, ""))
            )

    results_sorted = sorted(results, key=lambda x: (-x[3], -x[1]))[:top_n]
    total_orders = len(orders_with_target)

    return results_sorted, total_orders


def search_ai(target_item: str) -> str:
    query = (
        "Проанализируй, какие материалы и услуги покупаются совместно с "
        + target_item
    )
    results_ai = client.search(
        {
            "engine": "google_ai_mode",
            "q": query,
            "hl": "ru",
            "gl": "ru",
        }
    )
    markdown = (
        results_ai.get("reconstructed_markdown")
        or results_ai.get("answer")
        or ""
    )
    return markdown
