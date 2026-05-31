# Supabase Cloud Workspace — Setup Guide

DataPrism can optionally persist your work to a [Supabase](https://supabase.com)
Postgres database so it survives across sessions and devices. This powers the
**☁️ Cloud Workspace** page and the "Save to cloud" buttons on the Upload,
Data Cleaning, AI Insights, and Report Generator pages.

> **The app works fine without this.** If Supabase is not configured, cloud
> features simply show a "connect a database" hint and everything else keeps
> working with local session persistence.

---

## What gets stored

| Table | Stores | Written from |
|-------|--------|--------------|
| `dp_datasets` | Saved datasets (CSV text + metadata) | Upload & Analyze, Data Cleaning, Cloud Workspace |
| `dp_reports` | Generated HTML reports | Report Generator |
| `dp_validation_rule_sets` | Reusable validation rule sets (JSON) | Data Cleaning |
| `dp_insights` | Saved AI / rule-based insights + confidence | AI Insights Engine |

---

## Step 1 — Create a Supabase project

1. Sign up at [supabase.com](https://supabase.com) (the free tier is enough).
2. Create a new project. Pick a strong database password and a region close to you.
3. Wait for the project to finish provisioning (about a minute).

## Step 2 — Create the tables

Open **SQL Editor** in the Supabase dashboard, paste the **entire** script below,
and click **Run**. It is idempotent — safe to run more than once.

```sql
-- DataPrism schema -----------------------------------------------------------
-- Needed for gen_random_uuid() (enabled by default on Supabase, kept for safety)
create extension if not exists "pgcrypto";

-- Saved datasets (stored as CSV text for easy round-tripping with pandas)
create table if not exists public.dp_datasets (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text default '',
    row_count     integer default 0,
    column_count  integer default 0,
    columns       jsonb default '[]'::jsonb,
    data_csv      text,
    created_at    timestamptz not null default now()
);

-- Saved HTML reports
create table if not exists public.dp_reports (
    id            uuid primary key default gen_random_uuid(),
    title         text not null,
    dataset_name  text default '',
    html          text,
    created_at    timestamptz not null default now()
);

-- Reusable validation rule sets
create table if not exists public.dp_validation_rule_sets (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    rules         jsonb not null default '[]'::jsonb,
    created_at    timestamptz not null default now()
);

-- Saved AI / rule-based insights
create table if not exists public.dp_insights (
    id                uuid primary key default gen_random_uuid(),
    dataset_name      text default '',
    source            text default 'ai',
    confidence_level  text default '',
    confidence_score  integer default 0,
    content           text,
    created_at        timestamptz not null default now()
);

-- Indexes for fast "most recent first" listing
create index if not exists idx_dp_datasets_created  on public.dp_datasets        (created_at desc);
create index if not exists idx_dp_reports_created    on public.dp_reports         (created_at desc);
create index if not exists idx_dp_rule_sets_created  on public.dp_validation_rule_sets (created_at desc);
create index if not exists idx_dp_insights_created   on public.dp_insights        (created_at desc);

-- Row Level Security ---------------------------------------------------------
alter table public.dp_datasets             enable row level security;
alter table public.dp_reports              enable row level security;
alter table public.dp_validation_rule_sets enable row level security;
alter table public.dp_insights             enable row level security;

-- Permissive policies for the anon (public) key — suitable for a personal,
-- single-tenant app. See "Securing your data" below before going public.
create policy "dp_datasets anon all"  on public.dp_datasets
    for all to anon using (true) with check (true);
create policy "dp_reports anon all"   on public.dp_reports
    for all to anon using (true) with check (true);
create policy "dp_rule_sets anon all" on public.dp_validation_rule_sets
    for all to anon using (true) with check (true);
create policy "dp_insights anon all"  on public.dp_insights
    for all to anon using (true) with check (true);
```

## Step 3 — Get your project URL and API key

In the Supabase dashboard go to **Project Settings → API** and copy:

- **Project URL** → use as `SUPABASE_URL` (e.g. `https://abcd1234.supabase.co`)
- **Project API keys → `anon` `public`** → use as `SUPABASE_KEY`

> Use the **anon** key, not the `service_role` key, for this app. The anon key
> is safe to use from the client *as long as RLS is enabled* (it is, per Step 2).

## Step 4 — Configure secrets

### Local development

1. Copy the template: `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
2. Fill in your values:

   ```toml
   SUPABASE_URL = "https://your-project-ref.supabase.co"
   SUPABASE_KEY = "your-supabase-anon-key"
   ```

`.streamlit/secrets.toml` is gitignored, so your credentials are never committed.

Environment variables also work (handy for Docker/CI):

```bash
export SUPABASE_URL="https://your-project-ref.supabase.co"
export SUPABASE_KEY="your-supabase-anon-key"
```

### Streamlit Community Cloud

Open your app → **Settings → Secrets** and paste:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
```

## Step 5 — Install the dependency

The `supabase` package is already listed in `requirements.txt`. Install with:

```bash
pip install -r requirements.txt
```

## Step 6 — Verify

1. Run the app: `streamlit run app.py`
2. Open the **☁️ Cloud Workspace** page. You should see **"Connected to Supabase."**
3. Upload a dataset on **Upload & Analyze** and click **Save to cloud**, then
   return to Cloud Workspace and confirm it appears under **Datasets**.

---

## Securing your data

The policies in Step 2 let **anyone with your project URL + anon key** read and
write these tables. That is fine for a private/personal deployment, but if your
app is public you should lock it down. Two common options:

1. **Add Supabase Auth** and scope rows to the signed-in user. Add a
   `user_id uuid default auth.uid()` column to each table and replace the
   permissive policies, for example:

   ```sql
   alter table public.dp_datasets add column if not exists user_id uuid default auth.uid();

   drop policy if exists "dp_datasets anon all" on public.dp_datasets;
   create policy "dp_datasets owner" on public.dp_datasets
       for all to authenticated
       using (auth.uid() = user_id) with check (auth.uid() = user_id);
   ```

2. **Keep it private** — do not publish the app or its anon key, and restrict
   access at the hosting layer.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| "Supabase is not configured" | `SUPABASE_URL` or `SUPABASE_KEY` missing from secrets/env. |
| "The 'supabase' package is not installed" | Run `pip install -r requirements.txt`. |
| "Could not initialize Supabase client" | Check the URL is the full `https://...supabase.co` project URL. |
| Saves silently fail / permission errors | RLS is on but policies weren't created — re-run the SQL in Step 2. |
| `relation "dp_datasets" does not exist` | The schema SQL wasn't run in this project — run Step 2. |

---

## Reference: data-access code

The integration lives in:

- `utils/supabase_client.py` — credential loading + cached client (degrades gracefully).
- `utils/database.py` — `save_*` / `list_*` / `get_*` / `delete_*` functions, each
  returning an `(ok, payload)` tuple.
- `pages/9_Cloud_Workspace.py` — the browse/load/delete UI.

No code changes are needed to enable the feature — just add the secrets and run
the SQL.
