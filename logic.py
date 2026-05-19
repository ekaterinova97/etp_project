from collections import Counter, defaultdict
import os
import pickle
import gzip
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

def format_inn(inn: str) -> str:
    """Убирает .0 из ИНН при выводе."""
    try:
        return str(int(float(inn)))
    except (ValueError, TypeError):
        return inn

# ---------------------------------------------------------------
# ЗАГРУЗКА ИНДЕКСОВ
# ---------------------------------------------------------------

def load_indexes(file_path: str) -> dict:
    with gzip.open(file_path, "rb") as f:
        return pickle.load(f)

INDEXES = load_indexes("indeksi.pkl.gz")

item_to_orders                  = INDEXES["item_to_orders"]
order_to_items                  = INDEXES["order_to_items"]
item_to_supplier_count          = INDEXES["item_to_supplier_count"]
item_to_torgs                   = INDEXES["item_to_torgs"]
item_to_category                = INDEXES["item_to_category"]
supplier_to_lots                = INDEXES["supplier_to_lots"]
lot_to_suppliers                = INDEXES["lot_to_suppliers"]
supplier_to_categories          = INDEXES["supplier_to_categories"]
supplier_to_item_categories     = INDEXES["supplier_to_item_categories"]
inn_to_participant               = INDEXES["inn_to_participant"]
participant_to_inn               = INDEXES["participant_to_inn"]
inn_to_lots                     = INDEXES["inn_to_lots"]
item_to_procedure_participants  = INDEXES["item_to_procedure_participants"]


# ---------------------------------------------------------------
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ — определить участника по вводу
# (название или ИНН)
# ---------------------------------------------------------------

def resolve_supplier(query: str):
    query = query.strip()
    if query.isdigit():
        if query in inn_to_participant:
            name = inn_to_participant[query]
            return name, query
        return None, None
    else:
        if query in supplier_to_lots:
            inn = format_inn(participant_to_inn.get(query, ""))
            return query, inn
        return None, None


# ---------------------------------------------------------------
# ФУНКЦИЯ 1 — сопутствующая номенклатура
# ---------------------------------------------------------------

def get_frequent_companions(target_item: str, top_n: int = 10):
    if target_item not in item_to_orders:
        return None, None, f"Номенклатура '{target_item}' не найдена в закупках!"

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

    # блок участников/победителей
    procedures = item_to_procedure_participants.get(target_item, {})
    participants_info = []
    for order_id, entries in procedures.items():
        for participant, inn, status in entries:
            participants_info.append({
                "order_id":    order_id,
                "participant": participant,
                "inn":         format_inn(inn),
                "status":      status,
            })

    status_order = {"Победитель": 0, "Резервист": 1, "Участник": 2}
    participants_info.sort(key=lambda x: (status_order.get(x["status"], 99), x["order_id"]))

    return results_sorted, participants_info, total_orders


# ---------------------------------------------------------------
# ФУНКЦИЯ 2 — конкуренты поставщика (по названию или ИНН)
# ---------------------------------------------------------------

def get_competitors(query: str, top_n: int = 20):
    participant, inn = resolve_supplier(query)

    if participant is None:
        return None, None, None, f"Участник '{query}' не найден в базе. Проверьте название или ИНН."

    # Лоты, где участвовал этот поставщик
    lots = supplier_to_lots.get(participant, set())
    competitor_counter = Counter()

    # Считаем, сколько раз каждый другой поставщик встречается с ним в одном лоте
    for lot_id in lots:
        for supplier in lot_to_suppliers[lot_id]:
            if supplier != participant:
                competitor_counter[supplier] += 1


    results = []
    for supplier, count in sorted(competitor_counter.items(), key=lambda x: -x[1])[:top_n]:
        competitor_inn = participant_to_inn.get(supplier, "")
        results.append((supplier, competitor_inn, count))

    return results, participant, inn, len(lots)


# ---------------------------------------------------------------
# ФУНКЦИЯ 3 — категории НОМЕНКЛАТУРЫ поставщика (по названию или ИНН)
# ---------------------------------------------------------------

def get_supplier_item_categories(query: str):
    participant, inn = resolve_supplier(query)

    if participant is None:
        return None, None, None, f"Участник '{query}' не найден в базе. Проверьте название или ИНН."

    categories = sorted(supplier_to_item_categories.get(participant, set()))
    total_lots = len(supplier_to_lots.get(participant, set()))
    return categories, participant, inn, total_lots


# ---------------------------------------------------------------
# ФУНКЦИЯ 4 — AI-анализ
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
