# Deploying v1fresh

This app is a standard Flask app served by **gunicorn**. Below are three ways to
put it online. The files needed for all of them are already in this repo:
`wsgi.py`, `Dockerfile`, `.dockerignore`, `render.yaml`, and `requirements.txt`
(with gunicorn added).

> **Note on the database:** the app uses a local SQLite file (`v1fresh.db`).
> That's fine for a demo, but on hosts with an ephemeral filesystem the data
> resets on every redeploy. For persistent data, attach a disk/volume (see each
> section) or move to Postgres later.

---

## Option A — Render (easiest, free tier)

1. Push this folder to a GitHub repo.
2. Go to https://render.com → **New → Blueprint**, and point it at your repo.
   Render reads `render.yaml` automatically and configures the service.
   - Build: `pip install -r requirements.txt && python seed.py`
   - Start: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
   - `SECRET_KEY` is auto-generated.
3. Click **Apply**. First deploy takes a few minutes; you'll get a
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

## Option C — Docker (any VPS: DigitalOcean, EC2, etc.)

```bash
# build
docker build -t v1fresh .

# run (maps container 8000 -> host 80)
docker run -d -p 80:8000 \
  -e SECRET_KEY="change-me-to-a-long-random-string" \
  --name v1fresh v1fresh
```

The image seeds the DB at build time. To keep data across restarts, mount a
volume for the DB instead:

```bash
docker run -d -p 80:8000 \
  -e SECRET_KEY="..." \
  -v v1fresh_data:/app \
  --name v1fresh v1fresh
```

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
