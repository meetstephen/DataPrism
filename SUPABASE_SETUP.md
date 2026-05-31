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
| `dp_projects` | Named projects grouping work items | Cloud Workspace |
| `dp_audit_log` | Every significant action logged | All pages |
| `dp_dataset_versions` | Cleaning step snapshots (restorable) | Data Cleaning |
| `dp_feedback` | Tester/user feedback (bugs, suggestions, UX) | Sidebar feedback widget |

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

-- Tester / user feedback
create table if not exists public.dp_feedback (
    id            uuid primary key default gen_random_uuid(),
    type          text not null default '',
    page          text not null default '',
    text          text not null default '',
    timestamp     timestamptz not null default now()
);

-- Indexes for fast "most recent first" listing
create index if not exists idx_dp_datasets_created  on public.dp_datasets        (created_at desc);
create index if not exists idx_dp_reports_created    on public.dp_reports         (created_at desc);
create index if not exists idx_dp_rule_sets_created  on public.dp_validation_rule_sets (created_at desc);
create index if not exists idx_dp_insights_created   on public.dp_insights        (created_at desc);
create index if not exists idx_dp_feedback_created   on public.dp_feedback        (timestamp desc);

-- Row Level Security ---------------------------------------------------------
alter table public.dp_datasets             enable row level security;
alter table public.dp_reports              enable row level security;
alter table public.dp_validation_rule_sets enable row level security;
alter table public.dp_insights             enable row level security;
alter table public.dp_feedback             enable row level security;

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
create policy "dp_feedback anon all"  on public.dp_feedback
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
- `utils/workspace.py` — projects, audit log, and dataset versioning functions.
- `pages/9_Cloud_Workspace.py` — the browse/load/delete UI.

No code changes are needed to enable the feature — just add the secrets and run
the SQL.

---

## Enterprise Tables (Projects, Audit Log, Dataset Versions)

The enterprise upgrade adds three additional tables for workspace management.
Run the SQL below in the Supabase SQL Editor (same as Step 2):

```sql
-- Enterprise workspace tables ------------------------------------------------

-- Projects: organize work into named projects
create table if not exists public.dp_projects (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text default '',
    metadata      jsonb default '{}'::jsonb,
    created_at    timestamptz not null default now()
);

-- Audit log: track all user actions
create table if not exists public.dp_audit_log (
    id            uuid primary key default gen_random_uuid(),
    action        text not null,
    details       text default '',
    created_at    timestamptz not null default now()
);

-- Dataset versions: versioned snapshots for reproducibility
create table if not exists public.dp_dataset_versions (
    id              uuid primary key default gen_random_uuid(),
    dataset_name    text not null,
    version_note    text default '',
    row_count       integer default 0,
    column_count    integer default 0,
    columns         jsonb default '[]'::jsonb,
    data_csv        text,
    created_at      timestamptz not null default now()
);

-- Indexes
create index if not exists idx_dp_projects_created on public.dp_projects (created_at desc);
create index if not exists idx_dp_audit_log_created on public.dp_audit_log (created_at desc);
create index if not exists idx_dp_dataset_versions_created on public.dp_dataset_versions (created_at desc);

-- Row Level Security
alter table public.dp_projects enable row level security;
alter table public.dp_audit_log enable row level security;
alter table public.dp_dataset_versions enable row level security;

-- Permissive policies for single-tenant use
create policy "dp_projects anon all" on public.dp_projects
    for all to anon using (true) with check (true);
create policy "dp_audit_log anon all" on public.dp_audit_log
    for all to anon using (true) with check (true);
create policy "dp_dataset_versions anon all" on public.dp_dataset_versions
    for all to anon using (true) with check (true);
```

These tables power:
- **Projects tab** in Cloud Workspace - organize analyses by project
- **Audit Log tab** - automatic tracking of platform actions
- **Dataset Versions tab** - save/restore dataset snapshots for reproducibility

---

## Authentication & User Management Tables

The authentication system adds user accounts, role-based access control, and
activity logging. Run this SQL in the Supabase SQL Editor:

```sql
-- Authentication & User Management -------------------------------------------

-- User profiles linked to Supabase Auth
create table if not exists public.dp_users (
    id              uuid primary key default gen_random_uuid(),
    auth_id         uuid unique,
    email           text unique not null,
    display_name    text default '',
    role            text not null default 'viewer',
    created_at      timestamptz not null default now(),
    last_login      timestamptz,
    is_active       boolean not null default true
);

-- Activity log: track user actions across the platform
create table if not exists public.dp_activity_log (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid references public.dp_users(id) on delete set null,
    action          text not null,
    details         text default '',
    page            text default '',
    created_at      timestamptz not null default now()
);

-- Indexes for performance
create index if not exists idx_dp_users_email on public.dp_users (email);
create index if not exists idx_dp_users_auth_id on public.dp_users (auth_id);
create index if not exists idx_dp_activity_log_user_created
    on public.dp_activity_log (user_id, created_at desc);
create index if not exists idx_dp_activity_log_created
    on public.dp_activity_log (created_at desc);

-- Row Level Security
alter table public.dp_users enable row level security;
alter table public.dp_activity_log enable row level security;

-- Policies: authenticated users can read their own profile; admins can read all
create policy "dp_users_self_read" on public.dp_users
    for select to authenticated
    using (auth.uid() = auth_id);

create policy "dp_users_admin_all" on public.dp_users
    for all to authenticated
    using (
        exists (
            select 1 from public.dp_users u
            where u.auth_id = auth.uid() and u.role = 'admin'
        )
    )
    with check (
        exists (
            select 1 from public.dp_users u
            where u.auth_id = auth.uid() and u.role = 'admin'
        )
    );

-- Allow anon key insert (for sign-up flow before user is fully authenticated)
create policy "dp_users_anon_insert" on public.dp_users
    for insert to anon
    with check (true);

-- Allow anon key select/update (needed during sign-in to fetch/update profile)
create policy "dp_users_anon_select" on public.dp_users
    for select to anon
    using (true);

create policy "dp_users_anon_update" on public.dp_users
    for update to anon
    using (true)
    with check (true);

-- Activity log: anon can insert (logging during session); admins can read all
create policy "dp_activity_log_anon_insert" on public.dp_activity_log
    for insert to anon
    with check (true);

create policy "dp_activity_log_anon_select" on public.dp_activity_log
    for select to anon
    using (true);

-- Add user_id column to existing data tables for multi-user scoping
-- (These are safe to run even if the column already exists)
alter table public.dp_datasets add column if not exists user_id uuid;
alter table public.dp_reports add column if not exists user_id uuid;
alter table public.dp_validation_rule_sets add column if not exists user_id uuid;
alter table public.dp_insights add column if not exists user_id uuid;

-- Indexes on user_id for filtered queries
create index if not exists idx_dp_datasets_user_id on public.dp_datasets (user_id);
create index if not exists idx_dp_reports_user_id on public.dp_reports (user_id);
create index if not exists idx_dp_rule_sets_user_id on public.dp_validation_rule_sets (user_id);
create index if not exists idx_dp_insights_user_id on public.dp_insights (user_id);

-- Optional: trigger to auto-create dp_users row when a new user signs up via Auth
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.dp_users (auth_id, email, display_name, role)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1)),
        'viewer'
    )
    on conflict (auth_id) do nothing;
    return new;
end;
$$ language plpgsql security definer;

-- Drop and recreate the trigger (idempotent)
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();
```

### Admin email configuration

Set the `ADMIN_EMAIL` secret (in `.streamlit/secrets.toml` or environment) to
the email address that should automatically receive the `admin` role on sign-up.
The first user who registers with that email gets admin privileges.

### Role hierarchy

| Role | Level | Access |
|------|-------|--------|
| `admin` | 3 | Full access: all data, user management, activity logs |
| `analyst` | 2 | Full feature access, sees only own data |
| `viewer` | 1 | Read-only (future enforcement on individual pages) |

### Multi-user data scoping

When a user is logged in, `save_*` functions in `utils/database.py` automatically
attach their `user_id`. The `list_*` functions filter by `user_id` for non-admin
users, so each user sees only their own data. Admins see all data across users.
