# Going live on Vercel + Google Login

This app now has everything it needs to run on Vercel as a serverless Flask app
with **Sign in with Google**. Follow these steps in order.

> **Important — this is a read-only demo on Vercel.** Vercel's filesystem is
> read-only except `/tmp`, so the SQLite catalog ships pre-seeded and is copied
> to `/tmp` at cold start. Product browsing works great. Logins are kept in the
> signed session cookie (no user table), so they work per-session but don't
> persist a user database. New **orders won't persist** across cold starts.
> When you want real persistence, switch to a hosted Postgres (see the last
> section) — the code is structured so that's a small change.

---

## What was added to the repo

| File | Purpose |
|------|---------|
| `api/index.py` | Vercel serverless entry point — exposes the Flask `app`. |
| `vercel.json` | Tells Vercel to build the Python function and serve `/static`. |
| `routes/auth.py` | Google OAuth login/logout (Authlib). |
| `config.py` | Uses a writable `/tmp` DB on Vercel; reads Google creds from env. |
| `.vercelignore` | Keeps the function bundle small. |
| `requirements.txt` | Added `Authlib`, `requests`, `gunicorn`. |

---

## Step 1 — Commit the seeded database (this was the missing piece)

Your `.gitignore` ignored `*.db`, so the catalog never reached Vercel and the
site came up empty. That's now fixed with a `!v1fresh.db` exception. Make sure
the seeded DB is committed:

```bash
python seed.py            # (re)build v1fresh.db locally if needed
git add -f v1fresh.db     # force-add in case it was ignored before
git add .
git commit -m "Vercel serverless config + Google login + seeded DB"
git push
```

## Step 2 — Create Google OAuth credentials

1. Go to https://console.cloud.google.com/ and create (or pick) a project.
2. **APIs & Services → OAuth consent screen**:
   - User type: **External** → Create.
   - Fill App name, your support email, developer email → Save & continue.
   - Scopes: leave default (email, profile, openid) → Save.
   - Test users: add your own Gmail (needed while the app is in "Testing").
   - (When ready for anyone to log in, click **Publish app**.)
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**.
   - **Authorized redirect URIs** — add BOTH:
     - `https://<your-app>.vercel.app/auth/callback`
     - `http://localhost:5000/auth/callback`  (for local testing)
   - Create, then copy the **Client ID** and **Client secret**.

> The callback path must be exactly `/auth/callback` — that's the route in
> `routes/auth.py`. If your Vercel domain changes, add the new domain's
> `/auth/callback` here too.

## Step 3 — Set environment variables on Vercel

In your Vercel project → **Settings → Environment Variables**, add:

| Name | Value |
|------|-------|
| `GOOGLE_CLIENT_ID` | (from step 2) |
| `GOOGLE_CLIENT_SECRET` | (from step 2) |
| `SECRET_KEY` | any long random string (used to sign the session cookie) |

`VERCEL` is set automatically by the platform — you don't add it.
Redeploy after saving (Vercel → Deployments → Redeploy, or push a commit).

## Step 4 — Deploy

If your GitHub repo is already connected to the Vercel project, every `git push`
deploys automatically. Otherwise, from the project folder:

```bash
npm i -g vercel
vercel            # first run links the project
vercel --prod     # production deploy
```

Open `https://<your-app>.vercel.app` — browse products, then click **Login**
to sign in with Google.

---

## Test it locally first (recommended)

```bash
pip install -r requirements.txt
export SECRET_KEY="local-dev-secret"
export GOOGLE_CLIENT_ID="...."
export GOOGLE_CLIENT_SECRET="...."
python app.py
# open http://localhost:5000  and click Login
```

(Windows PowerShell: use `$env:SECRET_KEY="..."` instead of `export`.)

---

## Troubleshooting

- **`redirect_uri_mismatch` from Google** → the redirect URI in Google Cloud
  doesn't exactly match `https://<domain>/auth/callback`. Add the exact domain.
- **Site loads but no products** → `v1fresh.db` wasn't committed (Step 1).
- **500 on every page** → check the Vercel deployment logs; usually a missing
  env var (`SECRET_KEY`) or a dependency install failure.
- **Login says "not configured"** → `GOOGLE_CLIENT_ID` env var isn't set on Vercel.

---

## Later: real persistence (users + orders that survive)

When the demo isn't enough, move off SQLite to a free hosted Postgres
(Neon / Supabase / Vercel Postgres):

1. Create the DB, copy its connection string.
2. Add `psycopg2-binary` to `requirements.txt`.
3. In `config.py`, use `os.environ["DATABASE_URL"]` when present instead of the
   SQLite URI.
4. Add a `User` model and store the Google profile in `routes/auth.py`'s
   callback instead of only the session.

That's the only structural change needed — the OAuth flow and UI stay the same.
