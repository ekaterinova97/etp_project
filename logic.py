from collections import Counter, defaultdict
import os
import pickle
import pandas as pd
import serpapi
from dotenv import load_dotenv
import gzip

load_dotenv()

API_KEY = os.getenv("SERPAPI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Не найден SERPAPI_API_KEY в .env. "
        "Создайте файл .env и добавьте строку SERPAPI_API_KEY=ваш_ключ"
    )
client = serpapi.Client(api_key=API_KEY)


# ---------------------------------------------------------------
# ЗАГРУЗКА ИНДЕКСОВ
# ---------------------------------------------------------------

# в logic.py — замени load_indexes на это:

def load_indexes(file_path):
    with gzip.open(file_path, "rb") as f:
        return pickle.load(f)

INDEXES = load_indexes("indexes.pkl.gz")

item_to_orders          = INDEXES["item_to_orders"]
order_to_items          = INDEXES["order_to_items"]
item_to_supplier_count  = INDEXES["item_to_supplier_count"]
item_to_torgs           = INDEXES["item_to_torgs"]
supplier_to_lots        = INDEXES["supplier_to_lots"]
lot_to_suppliers        = INDEXES["lot_to_suppliers"]
supplier_to_categories  = INDEXES["supplier_to_categories"]


# ---------------------------------------------------------------
# ФУНКЦИЯ 1 — сопутствующая номенклатура (была раньше)
# ---------------------------------------------------------------

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


# ---------------------------------------------------------------
# ФУНКЦИЯ 2 — конкуренты поставщика
# ---------------------------------------------------------------

def get_competitors(target_supplier: str, top_n: int = 20):
    """
    Возвращает список конкурентов — организаций, которые участвовали
    в тех же лотах что и target_supplier.

    Возвращает: (results, total_lots) или (None, сообщение_об_ошибке)

    results — список кортежей (competitor_name, count_together)
    отсортированных по убыванию совместных лотов.
    """
    if target_supplier not in supplier_to_lots:
        return None, f"Участник '{target_supplier}' не найден в базе!"

    lots = supplier_to_lots[target_supplier]
    competitor_counter = Counter()

    for lot_id in lots:
        for supplier in lot_to_suppliers[lot_id]:
            if supplier != target_supplier:
                competitor_counter[supplier] += 1

    results = sorted(competitor_counter.items(), key=lambda x: -x[1])[:top_n]
    return results, len(lots)


# ---------------------------------------------------------------
# ФУНКЦИЯ 3 — категории торгов поставщика
# ---------------------------------------------------------------

def get_supplier_categories(target_supplier: str):
    """
    Возвращает дедуплицированный список категорий торгов,
    в которых участвовал target_supplier.

    Возвращает: (categories, total_lots) или (None, сообщение_об_ошибке)
    """
    if target_supplier not in supplier_to_categories:
        return None, f"Участник '{target_supplier}' не найден в базе!"

    categories = sorted(supplier_to_categories[target_supplier])
    total_lots = len(supplier_to_lots[target_supplier])
    return categories, total_lots


# ---------------------------------------------------------------
# ФУНКЦИЯ 4 — AI-анализ (была раньше)
# ---------------------------------------------------------------

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
