# Flask Finance Tracker 🏦

A clean, production-ready **personal finance tracker** built with Flask and SQLite.
Designed as a reusable template — spin up a new project by editing a single file.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Auth** | Register, login, logout with hashed passwords |
| **Expenses** | Add, edit, delete with category, date, and notes |
| **Dashboard** | Filterable table + donut & line charts |
| **Budgets** | Monthly limits per category with progress bars |
| **Reports** | 6-month trends, stacked charts, top expenses, MoM % |
| **Config-driven** | Rebrand & reconfigure entirely via `config.py` |
| **Tests** | pytest suite covering auth & expense CRUD |

---

## 🚀 Quick Start

```bash
# 1. Clone / unzip the project
cd flask-finance-tracker

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and set a strong SECRET_KEY

# 5. Run the app
python run.py
```

Open **http://localhost:5001** in your browser.

**Demo login:** `demo@spendbetter.com` / `SpendBetter@1`

---

## 🗂️ Project Structure

```
flask-finance-tracker/
│
├── config.py               ← ★ ALL customisation lives here
├── run.py                  ← Entry point
│
├── app/
│   ├── __init__.py         ← App factory (create_app)
│   ├── db.py               ← Database helpers (get_db, init_db, seed_db)
│   ├── helpers.py          ← login_required decorator, validators
│   ├── auth.py             ← Blueprint: register, login, logout
│   ├── expenses.py         ← Blueprint: dashboard, add, edit, delete
│   ├── budgets.py          ← Blueprint: monthly budget management
│   └── reports.py          ← Blueprint: analytics & charts
│
├── templates/
│   ├── base.html           ← Master layout (navbar, flash, footer)
│   ├── landing.html        ← Public landing page
│   ├── auth/               ← login.html, register.html
│   ├── expenses/           ← dashboard.html, form.html
│   ├── budgets/            ← index.html
│   ├── reports/            ← index.html
│   └── errors/             ← 404.html, 500.html
│
├── static/
│   ├── css/style.css       ← Global styles (CSS custom properties)
│   └── js/main.js          ← Minimal JS (flash auto-dismiss)
│
├── database/
│   ├── schema.sql          ← CREATE TABLE statements (version-controlled)
│   └── seed.py             ← Demo data loader
│
├── tests/
│   ├── conftest.py         ← pytest fixtures (app, client, auth_client)
│   ├── test_auth.py        ← Auth route tests
│   └── test_expenses.py    ← Expense CRUD tests
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🔧 Creating a New Project from This Template

All customisation is isolated to **`config.py`**. Here's what to change:

### 1. Rebrand the app
```python
APP_NAME    = "MyBudgetApp"
APP_TAGLINE = "Your money, your rules."
APP_ICON    = "💰"
```

### 2. Change currency
```python
CURRENCY_SYMBOL = "$"
CURRENCY_CODE   = "USD"
CURRENCY_LOCALE = "en-US"
```

### 3. Add / remove / rename categories
```python
CATEGORIES = [
    {"name": "Rent",       "color": "#1a472a", "bg": "#e8f0eb", "icon": "🏠"},
    {"name": "Groceries",  "color": "#c17f24", "bg": "#fdf3e3", "icon": "🛒"},
    {"name": "Utilities",  "color": "#2c4fa3", "bg": "#e8edf7", "icon": "💡"},
    # ... add as many as you need
]
```

### 4. Set default budgets
```python
DEFAULT_BUDGETS = {
    "Rent":      1500,
    "Groceries": 400,
    "Utilities": 200,
}
```

### 5. Toggle features
```python
FEATURES = {
    "budgets":   True,
    "reports":   True,
    "charts":    True,
    "seed_data": False,   # disable demo data in production
}
```

**That's it.** The entire app — routes, templates, charts, seed data — updates automatically.

---

## 🧪 Running Tests

```bash
pytest           # run all tests
pytest -v        # verbose
pytest tests/test_auth.py    # single file
```

---

## 🌐 Deployment (Render / Railway / Fly.io)

1. Set `DEBUG=false` and a strong `SECRET_KEY` in your host's environment variables.
2. Set `DATABASE_PATH` to a persistent volume path (e.g. `/data/app.db`).
3. Start command: `gunicorn "run:app"` (install gunicorn: `pip install gunicorn`).

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | Flask 3.x |
| Database | SQLite (via stdlib `sqlite3`) |
| Auth | Werkzeug `pbkdf2:sha256` password hashing |
| Charts | Chart.js 4 (CDN) |
| Fonts | Google Fonts — DM Sans + DM Serif Display |
| Tests | pytest + pytest-flask |

---

## 📄 License

MIT — free to use, modify, and distribute.
