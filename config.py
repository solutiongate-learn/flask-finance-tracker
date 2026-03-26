"""
config.py — The single source of truth for ALL app customisation.
=================================================================

HOW TO CREATE A NEW PROJECT FROM THIS TEMPLATE
───────────────────────────────────────────────
1.  Change APP_NAME, APP_TAGLINE, APP_ICON, FOOTER_TEXT         → rebrand
2.  Edit CURRENCY_SYMBOL / CURRENCY_CODE / CURRENCY_LOCALE       → localise
3.  Replace CATEGORIES list with your own names, colors, icons   → domain fit
4.  Adjust DEFAULT_BUDGETS to sensible limits for your context   → budgets
5.  Tweak THEME dict for your brand palette                      → look & feel
6.  Toggle FEATURES flags to enable/disable entire sections      → scope

That's it — the entire app (routes, templates, DB seed, charts)
reads from this file and adapts automatically.
"""

import os

# ╔══════════════════════════════════════════════════════╗
# ║  APP IDENTITY                                        ║
# ║  Change these lines to instantly rebrand the app.   ║
# ╚══════════════════════════════════════════════════════╝

APP_NAME        = "SpendBetter"
APP_TAGLINE     = "Spend smarter. Live better."
APP_DESCRIPTION = "A smart personal finance tracker."
APP_ICON        = "◈"          # Rendered in the navbar & footer
FOOTER_TEXT     = "Spend smarter. Live better."


# ╔══════════════════════════════════════════════════════╗
# ║  CURRENCY                                            ║
# ╚══════════════════════════════════════════════════════╝

CURRENCY_SYMBOL = "₹"       # Examples: "$", "€", "£", "₹", "¥"
CURRENCY_CODE   = "INR"     # Examples: "USD", "EUR", "GBP", "INR"
CURRENCY_LOCALE = "en-IN"   # Used in JavaScript toLocaleString()
                             # Examples: "en-US", "de-DE", "ja-JP"


# ╔══════════════════════════════════════════════════════╗
# ║  CATEGORIES                                          ║
# ║  Add, remove, or rename entries freely.             ║
# ║  Every page (dashboard, budgets, reports, charts)   ║
# ║  reads from this list automatically.                ║
# ╚══════════════════════════════════════════════════════╝
#
# Required keys per category:
#   name  : str  — unique label used in the DB and UI
#   color : str  — hex color for charts and badges
#   bg    : str  — light background hex for badge chips
#   icon  : str  — emoji shown in category labels

CATEGORIES = [
    {"name": "Bills",          "color": "#1a472a", "bg": "#e8f0eb", "icon": "⚡"},
    {"name": "Food",           "color": "#c17f24", "bg": "#fdf3e3", "icon": "🍽️"},
    {"name": "Transport",      "color": "#2c4fa3", "bg": "#e8edf7", "icon": "🚗"},
    {"name": "Health",         "color": "#a32c5a", "bg": "#fde8f0", "icon": "💊"},
    {"name": "Shopping",       "color": "#6e2ca3", "bg": "#f3e8fd", "icon": "🛍️"},
    {"name": "Entertainment",  "color": "#2ca38c", "bg": "#e8f7f3", "icon": "🎬"},
    {"name": "Education",      "color": "#b8860b", "bg": "#fff8e1", "icon": "📚"},
    {"name": "Other",          "color": "#777777", "bg": "#f0f0f0", "icon": "📌"},
]

# Derived helpers — do not edit these directly
CATEGORY_NAMES  = [c["name"]  for c in CATEGORIES]
CATEGORY_COLORS = {c["name"]: c["color"] for c in CATEGORIES}
CATEGORY_BG     = {c["name"]: c["bg"]    for c in CATEGORIES}
CATEGORY_ICONS  = {c["name"]: c["icon"]  for c in CATEGORIES}


# ╔══════════════════════════════════════════════════════╗
# ║  DEFAULT MONTHLY BUDGETS                             ║
# ║  Set to 0 to start a category with no budget.       ║
# ╚══════════════════════════════════════════════════════╝

DEFAULT_BUDGETS = {
    "Bills":         8000,
    "Food":          6000,
    "Transport":     2000,
    "Health":        3000,
    "Shopping":      5000,
    "Entertainment": 3000,
    "Education":     2000,
    "Other":         1000,
}


# ╔══════════════════════════════════════════════════════╗
# ║  THEME                                               ║
# ║  CSS custom-properties are generated from this dict. ║
# ╚══════════════════════════════════════════════════════╝

THEME = {
    "ink":           "#1e2235",   # Primary text
    "ink_soft":      "#2d3a50",   # Secondary text
    "ink_muted":     "#5a6580",   # Muted labels
    "ink_faint":     "#9aa3b8",   # Placeholder / disabled
    "paper":         "#f1f3f9",   # Page background  (cool slate)
    "paper_warm":    "#e8eaf3",   # Section background
    "paper_card":    "#ffffff",   # Card background
    "accent":        "#3d52d5",   # Primary action  (bright indigo)
    "accent_light":  "#e8ebfb",   # Accent tint
    "accent2":       "#f59e0b",   # Secondary accent (amber)
    "accent2_light": "#fef3c7",   # Secondary accent tint
    "navbar":        "#2d3a6b",   # Navbar background (deep navy-indigo)
    "danger":        "#e53e3e",   # Error / delete
    "danger_light":  "#fff5f5",   # Error tint
    "border":        "#dde1ef",   # Card borders
    "border_soft":   "#eaecf4",   # Subtle dividers
}


# ╔══════════════════════════════════════════════════════╗
# ║  FEATURES                                            ║
# ║  Toggle entire sections without touching code.      ║
# ╚══════════════════════════════════════════════════════╝

FEATURES = {
    "budgets":   True,   # Monthly budget tracking page
    "reports":   True,   # Analytics & reports page
    "charts":    True,   # Chart.js visualisations (requires CDN)
    "seed_data": True,   # Pre-load demo data on very first run
}


# ╔══════════════════════════════════════════════════════╗
# ║  PAGINATION                                          ║
# ╚══════════════════════════════════════════════════════╝

EXPENSES_PER_PAGE = 25   # Rows shown per dashboard page


# ╔══════════════════════════════════════════════════════╗
# ║  FLASK / ENVIRONMENT SETTINGS                        ║
# ║  These are overridden by .env at runtime.           ║
# ╚══════════════════════════════════════════════════════╝

SECRET_KEY    = os.environ.get("SECRET_KEY",    "change-me-in-production-please")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "database/app.db")
DEBUG         = os.environ.get("DEBUG",         "true").lower() == "true"
PORT          = int(os.environ.get("PORT",      5001))
