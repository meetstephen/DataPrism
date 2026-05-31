# Supabase Setup Guide for DataPrism

This guide explains how to configure Supabase as the cloud persistence backend for DataPrism.

## Prerequisites

1. Create a free Supabase project at [supabase.com](https://supabase.com)
2. Get your project URL and anon/public API key from Settings > API

## Configuration

Add your credentials to `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
```

Or set as environment variables:
```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_KEY="your-anon-public-key"
```

## Database Schema

Run the following SQL in your Supabase SQL Editor to create the required tables.

### Core Tables

```sql
-- Saved datasets
create table if not exists public.dp_datasets (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text default '',
    data_csv      text,
    row_count     integer default 0,
    col_count     integer default 0,
    created_at    timestamptz not null default now()
);

-- Saved reports
create table if not exists public.dp_reports (
    id            uuid primary key default gen_random_uuid(),
    title         text not null,
    report_html   text,
    dataset_name  text default '',
    created_at    timestamptz not null default now()
);

-- Saved rule sets (cleaning configurations)
create table if not exists public.dp_rule_sets (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text default '',
    rules_json    jsonb default '[]'::jsonb,
    created_at    timestamptz not null default now()
);

-- Saved insights
create table if not exists public.dp_insights (
    id            uuid primary key default gen_random_uuid(),
    title         text not null,
    content       text default '',
    insight_type  text default 'general',
    dataset_name  text default '',
    created_at    timestamptz not null default now()
);

-- Indexes for core tables
create index if not exists idx_dp_datasets_created on public.dp_datasets (created_at desc);
create index if not exists idx_dp_reports_created on public.dp_reports (created_at desc);
create index if not exists idx_dp_rule_sets_created on public.dp_rule_sets (created_at desc);
create index if not exists idx_dp_insights_created on public.dp_insights (created_at desc);

-- RLS (Row Level Security) for core tables
alter table public.dp_datasets enable row level security;
alter table public.dp_reports enable row level security;
alter table public.dp_rule_sets enable row level security;
alter table public.dp_insights enable row level security;

create policy "dp_datasets anon all" on public.dp_datasets
    for all to anon using (true) with check (true);
create policy "dp_reports anon all" on public.dp_reports
    for all to anon using (true) with check (true);
create policy "dp_rule_sets anon all" on public.dp_rule_sets
    for all to anon using (true) with check (true);
create policy "dp_insights anon all" on public.dp_insights
    for all to anon using (true) with check (true);
```

## Upgrade: Additional Tables (v2)

Run the following SQL to add project management, audit logging, and dataset versioning:

```sql
-- Projects
create table if not exists public.dp_projects (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text default '',
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);

-- Audit log
create table if not exists public.dp_audit_log (
    id            uuid primary key default gen_random_uuid(),
    project_id    uuid references public.dp_projects(id) on delete set null,
    action_type   text not null,
    description   text not null,
    details       jsonb default '{}'::jsonb,
    created_at    timestamptz not null default now()
);

-- Dataset versions
create table if not exists public.dp_dataset_versions (
    id              uuid primary key default gen_random_uuid(),
    project_id      uuid references public.dp_projects(id) on delete set null,
    dataset_name    text not null,
    version_number  integer not null default 1,
    data_csv        text,
    version_note    text default '',
    created_at      timestamptz not null default now()
);

-- Indexes
create index if not exists idx_dp_projects_created on public.dp_projects (created_at desc);
create index if not exists idx_dp_audit_log_project on public.dp_audit_log (project_id, created_at desc);
create index if not exists idx_dp_versions_project on public.dp_dataset_versions (project_id, created_at desc);

-- RLS
alter table public.dp_projects enable row level security;
alter table public.dp_audit_log enable row level security;
alter table public.dp_dataset_versions enable row level security;

create policy "dp_projects anon all" on public.dp_projects
    for all to anon using (true) with check (true);
create policy "dp_audit_log anon all" on public.dp_audit_log
    for all to anon using (true) with check (true);
create policy "dp_versions anon all" on public.dp_dataset_versions
    for all to anon using (true) with check (true);
```

## Security Notes

- The policies above use permissive anon access for simplicity. For production, implement proper user authentication and restrict policies to authenticated users.
- Consider adding `auth.uid()` checks in RLS policies when user auth is enabled.
- The `data_csv` column stores full dataset text. For large datasets (>5MB), consider using Supabase Storage instead.

## Troubleshooting

1. **"Supabase not configured"** - Ensure `SUPABASE_URL` and `SUPABASE_KEY` are set in `.streamlit/secrets.toml`
2. **"relation does not exist"** - Run the SQL above in the Supabase SQL Editor
3. **"permission denied"** - Ensure RLS policies are created (the `create policy` statements above)
4. **"supabase package not installed"** - Run `pip install supabase`
