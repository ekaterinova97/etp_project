import os
from flask import Flask, request, render_template_string
from logic import (
    get_frequent_companions,
    get_competitors,
    get_supplier_item_categories,
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

    .container { max-width: 960px; margin: 0 auto; }

    header {
      margin-bottom: 2rem;
      border-bottom: 2px solid #2a2420;
      padding-bottom: 1.5rem;
    }

    h1 { font-size: 2rem; font-weight: normal; letter-spacing: -0.02em; margin-bottom: 0.4rem; }
    .subtitle { font-size: 0.95rem; color: #6b5e56; font-style: italic; }

    .tabs {
      display: flex;
      margin-bottom: 2rem;
      border-bottom: 2px solid #2a2420;
      flex-wrap: wrap;
    }

    .tab-link {
      padding: 0.7rem 1.2rem;
      font-size: 0.88rem;
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
    .tab-link.active { color: #2a2420; border-bottom: 3px solid #2a2420; font-weight: bold; }

    .search-block { display: flex; gap: 12px; margin-bottom: 0.6rem; align-items: stretch; }

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
      transition: background 0.15s;
      white-space: nowrap;
    }

    button[type="submit"]:hover { background: #4a3830; }

    .search-hint {
      font-size: 0.82rem;
      color: #6b5e56;
      font-style: italic;
      margin-bottom: 2rem;
    }

    .loading { display: none; font-style: italic; color: #6b5e56; margin-bottom: 1.5rem; }

    .error-block {
      background: #fdecea;
      border: 1px solid #e8b4ae;
      padding: 1rem 1.2rem;
      border-radius: 2px;
      color: #7a2a22;
      margin-bottom: 2rem;
    }

    .result-header { margin-bottom: 1.5rem; }
    .result-header h2 { font-size: 1.25rem; font-weight: normal; margin-bottom: 0.3rem; }
    .result-header .meta { font-size: 0.9rem; color: #6b5e56; font-style: italic; }

    .supplier-meta {
      background: #fff;
      border: 1px solid #e0d8ce;
      padding: 0.8rem 1rem;
      border-radius: 2px;
      margin-bottom: 1.5rem;
      font-size: 0.92rem;
      color: #4a3830;
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
    tbody td { padding: 0.6rem 0.9rem; border-bottom: 1px solid #e8e0d6; }

    .legend { font-size: 0.82rem; color: #6b5e56; line-height: 1.8; margin-top: 0.75rem; }

    .status-badge {
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 2px;
      font-size: 0.8rem;
    }
    .status-Победитель { background: #e6f4ea; color: #1e6e3a; }
    .status-Резервист  { background: #fff3e0; color: #8a5a00; }
    .status-Участник   { background: #f0ebe3; color: #4a3830; }

    .participants-block {
      margin-top: 2.5rem;
      padding-top: 2rem;
      border-top: 1px solid #c8bfb4;
    }

    .participants-block h3 {
      font-size: 1rem;
      font-weight: normal;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #6b5e56;
      margin-bottom: 1rem;
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

    <nav class="tabs">
      <a class="tab-link {% if tab == 'items' %}active{% endif %}" href="/">ML-модель анализа совместных закупок</a>
      <a class="tab-link {% if tab == 'competitors' %}active{% endif %}" href="/competitors">ML-модель анализа участников закупок</a>
      <a class="tab-link {% if tab == 'item_categories' %}active{% endif %}" href="/item_categories">ML-модель участия в закупках по категориям</a>
    </nav>

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
    <p class="search-hint">{{ hint }}</p>

    <p class="loading">Ищем...</p>

    {% if error %}
      <div class="error-block">{{ error }}</div>
    {% endif %}

    <!-- ВКЛ 1: сопутствующая номенклатура -->
    {% if tab == 'items' and results is not none %}
      <div class="result-header">
        <h2>Результаты для: «{{ query }}»</h2>
        <p class="meta">Всего лотов с этой номенклатурой: {{ total }}</p>
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
              <th>Категория номенклатуры</th>
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
          B всего — сколько раз товар B куплен во всех лотах &nbsp;·&nbsp;
          Вероятность = A∩B / B всего
        </div>
      {% else %}
        <p class="no-results">Эта номенклатура не покупалась вместе с другими.</p>
      {% endif %}

      {% if participants_info %}
        <div class="participants-block">
          <h3>Участники и победители торгов</h3>
          <table>
            <thead>
              <tr>
                <th>№</th>
                <th>Процедура</th>
                <th>Участник</th>
                <th>ИНН</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {% for p in participants_info %}
              <tr>
                <td>{{ loop.index }}</td>
                <td>{{ p.order_id }}</td>
                <td>{{ p.participant }}</td>
                <td>{{ p.inn }}</td>
                <td><span class="status-badge status-{{ p.status }}">{{ p.status }}</span></td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% endif %}

      {% if ai_answer %}
        <div class="ai-block">
          <h3>AI-анализ</h3>
          <div class="ai-content">{{ ai_answer }}</div>
        </div>
      {% endif %}
    {% endif %}

    <!-- ВКЛ 2: конкуренты -->
    {% if tab == 'competitors' and results is not none %}
      <div class="supplier-meta">
        Участник: <strong>{{ participant_name }}</strong>
        {% if participant_inn %} &nbsp;·&nbsp; ИНН: {{ participant_inn }}{% endif %}
        &nbsp;·&nbsp; Лотов: {{ total }}
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

    <!-- ВКЛ 3: категории номенклатуры поставщика -->
    {% if tab == 'item_categories' and results is not none %}
      <div class="supplier-meta">
        Участник: <strong>{{ participant_name }}</strong>
        {% if participant_inn %} &nbsp;·&nbsp; ИНН: {{ participant_inn }}{% endif %}
        &nbsp;·&nbsp; Лотов: {{ total }}
      </div>
      {% if results %}
        <ul class="category-list">
          {% for cat in results %}
          <li>{{ loop.index }}. {{ cat }}</li>
          {% endfor %}
        </ul>
      {% else %}
        <p class="no-results">Категории номенклатуры не найдены.</p>
      {% endif %}
    {% endif %}

  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    ctx = dict(
        tab="items",
        action="/",
        placeholder="Введите номенклатуру...",
        hint="Введите точное название номенклатуры"
    )

    if request.method == "GET":
        return render_template_string(HTML, **ctx)

    query = request.form.get("query", "").strip()
    if not query:
        return render_template_string(HTML, error="Введите название номенклатуры.", **ctx)

    results, participants_info, total = get_frequent_companions(query, top_n=10)

    if results is None:
        return render_template_string(HTML, query=query, error=total, **ctx)

    ai_answer = search_ai(query)
    return render_template_string(
        HTML,
        query=query,
        results=results,
        participants_info=participants_info,
        total=total,
        ai_answer=ai_answer,
        **ctx
    )


@app.route("/competitors", methods=["GET", "POST"])
def competitors():
    ctx = dict(
        tab="competitors",
        action="/competitors",
        placeholder="Введите название организации или ИНН...",
        hint="Можно ввести название участника торгов или его ИНН"
    )

    if request.method == "GET":
        return render_template_string(HTML, **ctx)

    query = request.form.get("query", "").strip()
    if not query:
        return render_template_string(HTML, error="Введите название или ИНН.", **ctx)

    results, participant_name, participant_inn, total = get_competitors(query, top_n=20)

    if results is None:
        return render_template_string(HTML, query=query, error=total, **ctx)

    return render_template_string(
        HTML,
        query=query,
        results=results,
        participant_name=participant_name,
        participant_inn=participant_inn,
        total=total,
        **ctx
    )


@app.route("/item_categories", methods=["GET", "POST"])
def item_categories():
    ctx = dict(
        tab="item_categories",
        action="/item_categories",
        placeholder="Введите название организации или ИНН...",
        hint="Можно ввести название участника торгов или его ИНН"
    )

    if request.method == "GET":
        return render_template_string(HTML, **ctx)

    query = request.form.get("query", "").strip()
    if not query:
        return render_template_string(HTML, error="Введите название или ИНН.", **ctx)

    results, participant_name, participant_inn, total = get_supplier_item_categories(query)

    if results is None:
        return render_template_string(HTML, query=query, error=total, **ctx)

    return render_template_string(
        HTML,
        query=query,
        results=results,
        participant_name=participant_name,
        participant_inn=participant_inn,
        total=total,
        **ctx
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
