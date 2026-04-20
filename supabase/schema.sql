-- Lucky Please — Supabase schema.
-- Run this in the Supabase SQL Editor. Idempotent (re-run safe).
-- Sections:
--   1. groups          — authenticated user's saved groups (auth.uid RLS)
--   2. bingo_winners   — realtime winner claims for multiplayer bingo
--                        (public reads/writes gated by room_code secret)

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


-- ============================================================
-- 2. bingo_winners — realtime winner claims (max 100 concurrent)
-- ============================================================
-- Replaces the old broadcast-relay flow. Each player INSERTs a row
-- when they get bingo; host + every guest subscribes via
-- postgres_changes and rebuilds the winner list from DB state. DB
-- becomes the single source of truth — handles the claim storm
-- naturally (100 simultaneous inserts queue cleanly, unique index
-- prevents double-claim).
--
-- Auth model: rooms are code-gated, not user-gated. Anyone with the
-- code can read/write that room's rows. Field constraints prevent
-- obvious abuse (oversized nicknames, draws, lines). If abuse
-- becomes an issue later, tighten with an Edge Function that
-- re-validates.
create table if not exists public.bingo_winners (
    id          bigserial   primary key,
    room_code   text        not null,
    nickname    text        not null check (char_length(nickname) between 1 and 30),
    at_draw     int         not null check (at_draw between 0 and 500),
    lines       int         not null check (lines between 1 and 30),
    claimed_at  timestamptz not null default now()
);

-- One claim per (room, nickname). Second INSERT fails with 23505,
-- which the client silently ignores (covers "user clicks BINGO
-- twice" + "optimistic local + echoed insert" dedupe).
create unique index if not exists bingo_winners_one_per_player
    on public.bingo_winners (room_code, lower(nickname));

-- Query helper: fetch a room's winners in claim order.
create index if not exists bingo_winners_room_time
    on public.bingo_winners (room_code, claimed_at);

alter table public.bingo_winners enable row level security;

-- Open SELECT — realtime subscribers need this to receive INSERTs.
-- Scoped via the filter=room_code=eq.X client-side, not at RLS.
drop policy if exists "bingo_winners_select_all" on public.bingo_winners;
create policy "bingo_winners_select_all"
    on public.bingo_winners for select using (true);

-- Open INSERT with value validation. Room code is the shared secret
-- that separates rooms; anyone who has it can write to it, which
-- matches the broadcast-channel trust model we were already using.
drop policy if exists "bingo_winners_insert_all" on public.bingo_winners;
create policy "bingo_winners_insert_all"
    on public.bingo_winners for insert with check (
        char_length(room_code) between 3 and 12
        and char_length(nickname) between 1 and 30
        and at_draw between 0 and 500
        and lines between 1 and 30
    );

-- Realtime publication — required for postgres_changes subscriptions.
-- Wrapped in DO block because `add table` errors if already a member
-- (pg doesn't have IF NOT EXISTS for publication members).
do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname = 'supabase_realtime'
        and schemaname = 'public'
        and tablename = 'bingo_winners'
    ) then
        alter publication supabase_realtime add table public.bingo_winners;
    end if;
end$$;

-- Housekeeping recommendation: purge rows > 24h old periodically.
-- Not automated here — add via pg_cron when row count grows:
--   delete from public.bingo_winners where claimed_at < now() - interval '24 hours';
