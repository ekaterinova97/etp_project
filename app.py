import os
import pickle
from flask import Flask, request, render_template_string
from logic import (
    get_frequent_companions,
    get_competitors,
    get_supplier_categories,
    search_ai,
    item_to_orders,
    order_to_items,
    item_to_supplier_count,
    item_to_torgs,
)

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Анализ закупок</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Georgia', serif;
      background: #f5f2ed;
      color: #2a2420;
      min-height: 100vh;
      padding: 3rem 1.5rem;
    }

    .container {
      max-width: 860px;
      margin: 0 auto;
    }

    header {
      margin-bottom: 2rem;
      border-bottom: 2px solid #2a2420;
      padding-bottom: 1.5rem;
    }

    h1 {
      font-size: 2rem;
      font-weight: normal;
      letter-spacing: -0.02em;
      margin-bottom: 0.4rem;
    }

    .subtitle {
      font-size: 0.95rem;
      color: #6b5e56;
      font-style: italic;
    }

    /* ТАБЫ */
    .tabs {
      display: flex;
      gap: 0;
      margin-bottom: 2rem;
      border-bottom: 2px solid #2a2420;
    }

    .tab-link {
      padding: 0.7rem 1.4rem;
      font-size: 0.9rem;
      font-family: inherit;
      background: none;
      border: none;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
      cursor: pointer;
      color: #6b5e56;
      letter-spacing: 0.02em;
      text-decoration: none;
      display: inline-block;
      transition: color 0.15s;
    }

    .tab-link:hover { color: #2a2420; }

    .tab-link.active {
      color: #2a2420;
      border-bottom: 3px solid #2a2420;
      font-weight: bold;
    }

    /* ФОРМА */
    .search-block {
      display: flex;
      gap: 12px;
      margin-bottom: 2.5rem;
      align-items: stretch;
    }

    input[type="text"] {
      flex: 1;
      padding: 0.85rem 1.1rem;
      font-size: 1rem;
      font-family: inherit;
      border: 1.5px solid #2a2420;
      background: #fff;
      outline: none;
      border-radius: 2px;
      transition: border-color 0.15s;
    }

    input[type="text"]:focus { border-color: #8b5e3c; }

    button[type="submit"] {
      padding: 0.85rem 1.8rem;
      font-size: 1rem;
      font-family: inherit;
      background: #2a2420;
      color: #f5f2ed;
      border: none;
      cursor: pointer;
      border-radius: 2px;
      letter-spacing: 0.02em;
      transition: background 0.15s;
      white-space: nowrap;
    }

    button[type="submit"]:hover { background: #4a3830; }
    button[type="submit"]:active { background: #1a1510; }

    .loading {
      display: none;
      font-style: italic;
      color: #6b5e56;
      margin-bottom: 1.5rem;
    }

    .error-block {
      background: #fdecea;
      border: 1px solid #e8b4ae;
      padding: 1rem 1.2rem;
      border-radius: 2px;
      color: #7a2a22;
      margin-bottom: 2rem;
    }

    .result-header {
      margin-bottom: 1.5rem;
    }

    .result-header h2 {
      font-size: 1.25rem;
      font-weight: normal;
      margin-bottom: 0.3rem;
    }

    .result-header .meta {
      font-size: 0.9rem;
      color: #6b5e56;
      font-style: italic;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
      margin-bottom: 1rem;
      background: #fff;
    }

    thead tr { background: #2a2420; color: #f5f2ed; }

    thead th {
      padding: 0.65rem 0.9rem;
      text-align: left;
      font-weight: normal;
      letter-spacing: 0.02em;
      white-space: nowrap;
    }

    tbody tr:nth-child(odd) { background: #faf8f5; }
    tbody tr:nth-child(even) { background: #fff; }
    tbody tr:hover { background: #f0ebe3; }

    tbody td {
      padding: 0.6rem 0.9rem;
      border-bottom: 1px solid #e8e0d6;
    }

    .legend {
      font-size: 0.82rem;
      color: #6b5e56;
      line-height: 1.8;
      margin-top: 0.75rem;
    }

    .ai-block {
      margin-top: 2.5rem;
      padding-top: 2rem;
      border-top: 1px solid #c8bfb4;
    }

    .ai-block h3 {
      font-size: 1rem;
      font-weight: normal;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #6b5e56;
      margin-bottom: 1rem;
    }

    .ai-content {
      font-size: 0.95rem;
      line-height: 1.75;
      color: #2a2420;
      white-space: pre-wrap;
      background: #fff;
      padding: 1.2rem 1.4rem;
      border: 1px solid #e0d8ce;
      border-radius: 2px;
    }

    .no-results { font-style: italic; color: #6b5e56; }

    /* Список категорий */
    .category-list {
      list-style: none;
      background: #fff;
      border: 1px solid #e0d8ce;
      border-radius: 2px;
    }

    .category-list li {
      padding: 0.6rem 0.9rem;
      border-bottom: 1px solid #e8e0d6;
      font-size: 0.92rem;
    }

    .category-list li:last-child { border-bottom: none; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Анализ закупок</h1>
      <p class="subtitle">Инструмент для работы с данными тендеров</p>
    </header>

    <!-- ТАБЫ -->
    <nav class="tabs">
      <a class="tab-link {% if tab == 'items' %}active{% endif %}" href="/">Сопутствующая номенклатура</a>
      <a class="tab-link {% if tab == 'competitors' %}active{% endif %}" href="/competitors">Конкуренты поставщика</a>
      <a class="tab-link {% if tab == 'categories' %}active{% endif %}" href="/categories">Категории поставщика</a>
    </nav>

    <!-- ФОРМА -->
    <form method="POST" action="{{ action }}" onsubmit="document.querySelector('.loading').style.display='block'">
      <div class="search-block">
        <input
          type="text"
          name="query"
          placeholder="{{ placeholder }}"
          value="{{ query or '' }}"
          autofocus
          autocomplete="off"
        />
        <button type="submit">Найти</button>
      </div>
    </form>

    <p class="loading">Ищем...</p>

    {% if error %}
      <div class="error-block">{{ error }}</div>
    {% endif %}

    <!-- РЕЗУЛЬТАТЫ: номенклатура -->
    {% if tab == 'items' and results is not none %}
      <div class="result-header">
        <h2>Результаты для: «{{ query }}»</h2>
        <p class="meta">Всего заказов с этим товаром: {{ total }}</p>
      </div>
      {% if results %}
        <table>
          <thead>
            <tr>
              <th>№</th>
              <th>Номенклатура</th>
              <th>A∩B</th>
              <th>B всего</th>
              <th>Вероятность</th>
              <th>Предложений</th>
              <th>Категория торгов</th>
            </tr>
          </thead>
          <tbody>
            {% for item, count_ab, count_b, prob, sup_count, torgs in results %}
            <tr>
              <td>{{ loop.index }}</td>
              <td>{{ item }}</td>
              <td>{{ count_ab }}</td>
              <td>{{ count_b }}</td>
              <td>{{ "%.1f%%"|format(prob * 100) }}</td>
              <td>{{ sup_count }}</td>
              <td>{{ torgs }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="legend">
          A∩B — сколько раз куплены вместе &nbsp;·&nbsp;
          B всего — сколько раз товар B куплен во всех заказах &nbsp;·&nbsp;
          Вероятность = A∩B / B всего
        </div>
      {% else %}
        <p class="no-results">Этот товар не покупался вместе с другими.</p>
      {% endif %}
      {% if ai_answer %}
        <div class="ai-block">
          <h3>AI-анализ</h3>
          <div class="ai-content">{{ ai_answer }}</div>
        </div>
      {% endif %}
    {% endif %}

    <!-- РЕЗУЛЬТАТЫ: конкуренты -->
    {% if tab == 'competitors' and results is not none %}
      <div class="result-header">
        <h2>Конкуренты: «{{ query }}»</h2>
        <p class="meta">Участвовал в {{ total }} лотах. Встречался с:</p>
      </div>
      {% if results %}
        <table>
          <thead>
            <tr>
              <th>№</th>
              <th>Организация</th>
              <th>Совместных лотов</th>
            </tr>
          </thead>
          <tbody>
            {% for name, count in results %}
            <tr>
              <td>{{ loop.index }}</td>
              <td>{{ name }}</td>
              <td>{{ count }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p class="no-results">Конкурентов не найдено.</p>
      {% endif %}
    {% endif %}

    <!-- РЕЗУЛЬТАТЫ: категории -->
    {% if tab == 'categories' and results is not none %}
      <div class="result-header">
        <h2>Категории торгов: «{{ query }}»</h2>
        <p class="meta">Участвовал в {{ total }} лотах. Категории:</p>
      </div>
      {% if results %}
        <ul class="category-list">
          {% for cat in results %}
          <li>{{ loop.index }}. {{ cat }}</li>
          {% endfor %}
        </ul>
      {% else %}
        <p class="no-results">Категории не найдены.</p>
      {% endif %}
    {% endif %}

  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    ctx = dict(tab="items", action="/", placeholder="Введите номенклатуру...")

    if request.method == "GET":
        return render_template_string(HTML, **ctx)

    query = request.form.get("query", "").strip()
    if not query:
        return render_template_string(HTML, error="Введите название номенклатуры.", **ctx)

    results, total = get_frequent_companions(
        query, item_to_orders, order_to_items, item_to_supplier_count, item_to_torgs, top_n=10
    )

    if results is None:
        return render_template_string(HTML, query=query, error=total, **ctx)

    ai_answer = search_ai(query)
    return render_template_string(HTML, query=query, results=results, total=total, ai_answer=ai_answer, **ctx)


@app.route("/competitors", methods=["GET", "POST"])
def competitors():
    ctx = dict(tab="competitors", action="/competitors", placeholder="Введите название организации...")

    if request.method == "GET":
        return render_template_string(HTML, **ctx)

    query = request.form.get("query", "").strip()
    if not query:
        return render_template_string(HTML, error="Введите название организации.", **ctx)

    results, total = get_competitors(query, top_n=20)

    if results is None:
        return render_template_string(HTML, query=query, error=total, **ctx)

    return render_template_string(HTML, query=query, results=results, total=total, **ctx)


@app.route("/categories", methods=["GET", "POST"])
def categories():
    ctx = dict(tab="categories", action="/categories", placeholder="Введите название организации...")

    if request.method == "GET":
        return render_template_string(HTML, **ctx)

    query = request.form.get("query", "").strip()
    if not query:
        return render_template_string(HTML, error="Введите название организации.", **ctx)

    results, total = get_supplier_categories(query)

    if results is None:
        return render_template_string(HTML, query=query, error=total, **ctx)

    return render_template_string(HTML, query=query, results=results, total=total, **ctx)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
