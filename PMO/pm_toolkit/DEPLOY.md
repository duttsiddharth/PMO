# Deployment Guide — IT Infrastructure PM Toolkit

This app is a **Streamlit** application (a live Python server), so GitHub Pages
**cannot** host it. The free, standard path is:

1. Push this code to GitHub (`duttsiddharth/PMO`)
2. Deploy it from GitHub using **Streamlit Community Cloud**

---

## Step 1 — Push the code to GitHub

From inside this project folder (the one containing `app.py`):

```bash
git init
git add .
git commit -m "Initial commit: IT Infrastructure PM Toolkit"
git branch -M main
git remote add origin https://github.com/duttsiddharth/PMO.git
git push -u origin main
```

> If the repo already has commits (e.g. an auto-created README), either pull first
> (`git pull origin main --allow-unrelated-histories`) or force-set with care
> (`git push -u origin main --force` — only if the repo is empty/disposable).

The `.gitignore` is already configured to keep your local database, caches, and
secrets out of the repo.

---

## Step 2 — Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **New app** → **Deploy a public app from GitHub**.
3. Select:
   - **Repository:** `duttsiddharth/PMO`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Deploy**.

Streamlit reads `requirements.txt` automatically and builds the environment.
You'll get a public URL like `https://pmo.streamlit.app`.

Every `git push` to `main` from then on auto-redeploys the app.

---

## Step 3 — Configure secrets (optional but recommended)

In the deployed app: **Manage app → Settings → Secrets**, paste:

```toml
PM_ORG_NAME = "SD Advisory"

# Optional — enables live AI exec summaries / risk prediction
ANTHROPIC_API_KEY = "sk-ant-..."

# Optional — use Postgres instead of ephemeral SQLite (see Step 4)
# PM_DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
```

These are exposed to the app as environment variables — no code change needed.

---

## Step 4 — Database persistence (IMPORTANT)

Streamlit Community Cloud uses an **ephemeral filesystem**. The default SQLite
database file is wiped on every reboot or redeploy.

**Option A — Demo / portfolio use (simplest):**
Leave SQLite as-is. After any reboot, open the **Settings** page in the app and
click **Seed sample data** to reload the 3 demo projects. Perfect for showcasing.

**Option B — Real persistence (Postgres / Supabase):**
You already use Supabase. Grab its connection string and add to Secrets:

```toml
PM_DATABASE_URL = "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"
```

The app already supports this via `config.py` — no code change. `psycopg2-binary`
is already in `requirements.txt`. On first run, open **Settings → Seed sample
data** once to create tables and demo records (or just start adding real
projects).

---

## Local run (for reference)

```bash
pip install -r requirements.txt
python -m core.seed      # loads 3 sample projects
streamlit run app.py
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| App boots but shows no data | Open **Settings → Seed sample data** |
| `psycopg2` build error | Already using `psycopg2-binary`; ensure Postgres URL is correct |
| Data disappears after a while | Expected on SQLite (ephemeral) — switch to Option B |
| AI features show template text | Set `ANTHROPIC_API_KEY` in Secrets |
| Push rejected (non-fast-forward) | Repo has existing commits — `git pull origin main --allow-unrelated-histories` then push |
