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


-- ============================================================
-- 3. profiles — authenticated user identity (nickname + avatar)
-- ============================================================
-- Why a separate table instead of auth.users.user_metadata?
--   user_metadata is client-mutable via updateUser() — anyone can
--   call it and set whatever. For an identity anchor like nickname
--   that MUST be globally unique, validated, and visible to other
--   users, we need a proper table with UNIQUE + CHECK + RLS that
--   only the owner can write and that's queryable by everyone.
--
-- Key design choices:
--   • id = auth.uid (1:1 with auth.users)
--   • nickname: 2-20 chars, whitelist (latin + digits + 한글 + _-),
--     case-insensitively unique, not reserved
--   • email stored separately from auth.users so users can opt to
--     expose a different contact address (also lets us add column-
--     level grants later without touching auth schema)
--   • profile_complete flag gates social features client-side;
--     defaults false until the signup-completion flow writes the
--     profile for the first time
--   • updated_at auto-maintained via trigger for cache invalidation

create table if not exists public.profiles (
    id               uuid        primary key references auth.users(id) on delete cascade,
    nickname         text        not null,
    email            text,
    avatar_url       text,
    bio              text        check (bio is null or char_length(bio) <= 160),
    profile_complete boolean     not null default false,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),
    constraint nickname_length check (char_length(nickname) between 2 and 20),
    -- Whitelist: A-Z, a-z, 0-9, 한글, underscore, hyphen. No spaces,
    -- no HTML-breakers, no invisible unicode. Keeps display rendering
    -- predictable across every surface without needing per-render
    -- sanitisation. DB rejects violations symmetrically with client.
    constraint nickname_chars  check (nickname ~ '^[A-Za-z0-9_\-가-힣]+$')
);

-- Case-insensitive nickname uniqueness. "Alice" and "alice" collide,
-- which matches user intuition ("that name is taken").
create unique index if not exists profiles_nickname_lower_idx
    on public.profiles (lower(nickname));

create index if not exists profiles_updated_idx
    on public.profiles (updated_at desc);

alter table public.profiles enable row level security;

-- READ: everyone can select. Client code is responsible for only
-- including email in queries where the row is the user's own. If
-- the product later requires true column-level isolation for email,
-- replace this with a view + split policy.
drop policy if exists "profiles_select_public" on public.profiles;
drop policy if exists "profiles_insert_own"    on public.profiles;
drop policy if exists "profiles_update_own"    on public.profiles;

create policy "profiles_select_public"
    on public.profiles for select using (true);

-- WRITE: strictly own row only. Supabase RLS pins auth.uid() from
-- the JWT, so there's no way a guest token can forge another user's
-- id (the FK on id → auth.users would fail regardless).
create policy "profiles_insert_own"
    on public.profiles for insert
    with check (auth.uid() = id);

create policy "profiles_update_own"
    on public.profiles for update
    using (auth.uid() = id);

-- Reserved nicknames — names users shouldn't be able to claim so
-- nobody can impersonate staff/system/etc. Extend over time.
create table if not exists public.reserved_nicknames (
    nickname_lower text primary key
);

insert into public.reserved_nicknames (nickname_lower) values
    ('admin'),('administrator'),('moderator'),('mod'),('system'),
    ('host'),('luckyplz'),('lucky'),('support'),('help'),
    ('official'),('bot'),('null'),('undefined'),('root'),
    ('guest'),('anonymous'),('anon'),('test'),('staff'),('api'),
    ('관리자'),('운영자'),('고객센터'),('운영팀'),('스태프'),('공지')
on conflict do nothing;

-- Guard trigger: enforce reserved-list check and keep updated_at
-- fresh on every write. Raising a custom exception gives the client
-- a machine-readable error code it can branch on.
create or replace function public.profiles_before_write()
returns trigger language plpgsql as $$
begin
    if exists (
        select 1 from public.reserved_nicknames
        where nickname_lower = lower(new.nickname)
    ) then
        raise exception using errcode = 'P0001',
            message = 'nickname_reserved';
    end if;
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists profiles_before_write on public.profiles;
create trigger profiles_before_write
    before insert or update on public.profiles
    for each row execute function public.profiles_before_write();

-- Availability RPC — client calls this while the user types. Kept as
-- security definer so the caller doesn't need select-on-reserved
-- privileges (keeps that table readable only via this RPC's filter).
-- Returns a strict enum-like reason so the UI can localise the
-- message. Own user's existing nickname returns available=true so
-- the edit-profile flow never false-positives on itself.
create or replace function public.check_nickname_available(candidate text)
returns table(available boolean, reason text)
language plpgsql security definer
set search_path = public
as $$
declare
    lc text;
begin
    if candidate is null then
        return query select false, 'invalid'::text; return;
    end if;
    lc := lower(candidate);
    if char_length(candidate) < 2 or char_length(candidate) > 20 then
        return query select false, 'invalid'::text; return;
    end if;
    if candidate !~ '^[A-Za-z0-9_\-가-힣]+$' then
        return query select false, 'invalid'::text; return;
    end if;
    if exists (select 1 from public.reserved_nicknames where nickname_lower = lc) then
        return query select false, 'reserved'::text; return;
    end if;
    if exists (
        select 1 from public.profiles
        where lower(nickname) = lc
          and id <> coalesce(auth.uid(), '00000000-0000-0000-0000-000000000000'::uuid)
    ) then
        return query select false, 'taken'::text; return;
    end if;
    return query select true, null::text;
end;
$$;

grant execute on function public.check_nickname_available(text) to authenticated, anon;

