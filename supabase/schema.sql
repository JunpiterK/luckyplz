-- Lucky Please — saved groups
-- Run this in Supabase SQL Editor once.

create table if not exists public.groups (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references auth.users(id) on delete cascade,
    name        text not null check (char_length(name) between 1 and 40),
    members     jsonb not null default '[]'::jsonb,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index if not exists groups_user_updated_idx
    on public.groups (user_id, updated_at desc);

alter table public.groups enable row level security;

drop policy if exists "groups_select_own" on public.groups;
drop policy if exists "groups_insert_own" on public.groups;
drop policy if exists "groups_update_own" on public.groups;
drop policy if exists "groups_delete_own" on public.groups;

create policy "groups_select_own"
    on public.groups for select
    using (auth.uid() = user_id);

create policy "groups_insert_own"
    on public.groups for insert
    with check (auth.uid() = user_id);

create policy "groups_update_own"
    on public.groups for update
    using (auth.uid() = user_id);

create policy "groups_delete_own"
    on public.groups for delete
    using (auth.uid() = user_id);

create or replace function public.groups_set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists groups_set_updated_at on public.groups;
create trigger groups_set_updated_at
    before update on public.groups
    for each row execute function public.groups_set_updated_at();
