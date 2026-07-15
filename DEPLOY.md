# Deploying v1fresh

This app is a standard Flask app served by **gunicorn**. Below are two ways to
put it online. The files needed for both are already in this repo: `wsgi.py`
and `requirements.txt` (with gunicorn added).

> **Note on the database:** the app uses a local SQLite file (`v1fresh.db`).
> That's fine for a demo, but on hosts with an ephemeral filesystem the data
> resets on every redeploy. For persistent data, attach a disk/volume (see each
> section) or move to Postgres later.

---

## Option A — Render (easiest, free tier)

1. Push this folder to a GitHub repo.
2. Go to https://render.com → **New → Web Service**, and point it at your repo.
   - Build command: `pip install -r requirements.txt && python seed.py`
   - Start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
   - Add an environment variable `SECRET_KEY` (any long random string).
3. Click **Create Web Service**. First deploy takes a few minutes; you'll get a
   `https://v1fresh.onrender.com` URL.
4. (Optional, persistent DB) In the service **Settings → Disks**, add a disk
   mounted at `/app`, then change the build command to run `python seed.py`
   only once.

## Option B — Railway

1. Push to GitHub.
2. https://railway.app → **New Project → Deploy from GitHub repo**.
3. Railway detects Python. Set the start command to:
   `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
4. Add a variable `SECRET_KEY` (any long random string).
5. Run `python seed.py` once from the Railway shell to seed the DB.

---

## Run locally the production way

```bash
pip install -r requirements.txt
python seed.py            # first time only — creates v1fresh.db
gunicorn wsgi:app --bind 0.0.0.0:8000
# open http://localhost:8000
```

## Before going live — quick checklist

- [ ] Set a strong `SECRET_KEY` env var (never ship the dev default).
- [ ] Seed the database once (`python seed.py`).
- [ ] If you need data to persist, attach a disk/volume or switch to Postgres.
- [ ] Point a custom domain at the host (each platform has a Domains section).
