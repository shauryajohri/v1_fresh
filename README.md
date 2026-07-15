# v1fresh — Fresh Fruits & Vegetables Online (Flask Clone)

A learning clone of v1fresh.com, built with Flask + SQLite + vanilla HTML/CSS/JS.
No accounts/login — cart and checkout work as a guest, and orders are tracked
by order number + phone number instead of an account system.

## Project status: Phase 1 complete

- Homepage, product listing, product detail pages — all working, pulling real
  data from the database.
- Cart page, checkout, and order-tracking pages exist but are **not yet wired
  up** (Phase 2/3). Right now they render correctly but don't save anything.

## Setup

### 1. Open a terminal in this folder
Make sure you can see `app.py`, `seed.py`, `models.py` when you list files
(`dir` on Windows, `ls` on Mac/Linux). If you don't see them, you're in the
wrong folder.

### 2. Create the virtual environment (one-time)

**Windows (PowerShell):**
```powershell
python -m venv v1env
.\v1env\Scripts\Activate.ps1
```
If you get an "execution policy" error when activating, run this once, then
try activating again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Mac/Linux:**
```bash
python3 -m venv v1env
source v1env/bin/activate
```

Once activated, your prompt should show `(v1env)` at the start of the line.
That confirms you're using the project's Python, not your system Python.

### 3. Install dependencies (one-time, after activating)
```bash
pip install -r requirements.txt
```

### 4. Seed the database (run once, or anytime you want to reset the data)
```bash
python seed.py
```
This creates `v1fresh.db` with 6 categories and 36 products.

### 5. Run the app
```bash
python app.py
```
Then open **http://127.0.0.1:5000** in your browser.

## Every time you come back to work on this

```bash
# Windows
.\v1env\Scripts\Activate.ps1
python app.py

# Mac/Linux
source v1env/bin/activate
python app.py
```
You only need to re-run `pip install -r requirements.txt` if you pull new
code that added something to `requirements.txt`. You don't need to re-run
`seed.py` unless you want to reset the catalog.

## Project structure

```
v1fresh/
├── app.py                # Flask app factory + entry point
├── config.py              # secret key, DB path, delivery fee rules
├── extensions.py          # shared db = SQLAlchemy() instance
├── models.py               # Category, Product, Order, OrderItem
├── seed.py                  # populates the database with demo data
├── requirements.txt
├── routes/
│   ├── main.py             # home, about, contact
│   ├── products.py         # listing, detail
│   ├── cart.py              # cart page
│   └── orders.py           # checkout, track-order
├── templates/               # Jinja2 templates, mirrors routes/ structure
└── static/
    ├── css/style.css
    ├── js/main.js
    └── images/
```

## Roadmap

- **Phase 2** — working cart (add/update/remove via session), search
- **Phase 3** — checkout form, order placement, order tracking by order number + phone
- **Phase 4** — responsive polish, empty/error states, final pass


for admin feature use admin in url
username: shaurya johri
password: sai@2006