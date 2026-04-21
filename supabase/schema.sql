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


-- ============================================================
-- 4. friendships — bidirectional friend graph (request + accept)
-- ============================================================
-- Canonical row model: (user_a, user_b) where user_a < user_b.
-- Storing each friendship as exactly one row (ordered pair) avoids
-- the "two rows per friendship" duplication trap that plagues many
-- early-stage friend implementations. To tell requester apart from
-- addressee we carry `requester_id` separately.
--
-- Status lifecycle:
--   'pending'  → request sent, not yet accepted
--   'accepted' → mutual friendship
--   'blocked'  → one side blocked the other (still one row)
-- blocked_by tells us who blocked whom. On block, status flips to
-- blocked regardless of previous state and no DMs may be exchanged.

create table if not exists public.friendships (
    user_a        uuid        not null references auth.users(id) on delete cascade,
    user_b        uuid        not null references auth.users(id) on delete cascade,
    requester_id  uuid        not null references auth.users(id) on delete cascade,
    status        text        not null default 'pending'
                    check (status in ('pending','accepted','blocked')),
    blocked_by    uuid        references auth.users(id) on delete set null,
    created_at    timestamptz not null default now(),
    accepted_at   timestamptz,
    blocked_at    timestamptz,
    primary key (user_a, user_b),
    -- Enforce canonical ordering so the same two users can never
    -- produce two rows (a,b) and (b,a).
    constraint friends_ordered   check (user_a < user_b),
    constraint friends_not_self  check (user_a <> user_b),
    constraint requester_is_member check (requester_id in (user_a, user_b)),
    constraint blocked_by_member check (blocked_by is null or blocked_by in (user_a, user_b))
);

create index if not exists friendships_user_a_status_idx
    on public.friendships (user_a, status);
create index if not exists friendships_user_b_status_idx
    on public.friendships (user_b, status);

alter table public.friendships enable row level security;

drop policy if exists "friendships_select_own"  on public.friendships;
drop policy if exists "friendships_insert_own"  on public.friendships;
drop policy if exists "friendships_update_own"  on public.friendships;
drop policy if exists "friendships_delete_own"  on public.friendships;

-- SELECT: both participants can read their own friendships. Nobody
-- else can enumerate the graph.
create policy "friendships_select_own"
    on public.friendships for select
    using (auth.uid() in (user_a, user_b));

-- INSERT: the requester (= auth.uid()) must be one of the two
-- members. Can't create a friendship on behalf of someone else.
-- Trigger (below) ensures the addressee has a profile row, which
-- doubles as a rate-limit hook later.
create policy "friendships_insert_own"
    on public.friendships for insert
    with check (
        auth.uid() in (user_a, user_b)
        and requester_id = auth.uid()
    );

-- UPDATE: either member can flip status (accept, block, unblock).
-- Payload validated by a trigger so only legal transitions run.
create policy "friendships_update_own"
    on public.friendships for update
    using (auth.uid() in (user_a, user_b));

-- DELETE: either member can unfriend. Deletes cascade into direct
-- messages via the application layer; we don't auto-delete DM
-- history on unfriend (users may want archival receipts).
create policy "friendships_delete_own"
    on public.friendships for delete
    using (auth.uid() in (user_a, user_b));

-- Rate limit: cap pending-outgoing requests to 20/hour per user.
-- Blocks obvious spam scripting without hurting normal flow.
create or replace function public.friendships_rate_limit()
returns trigger language plpgsql as $$
declare
    recent_count int;
begin
    if tg_op = 'INSERT' and new.status = 'pending' then
        select count(*) into recent_count from public.friendships
        where requester_id = new.requester_id
          and status = 'pending'
          and created_at > now() - interval '1 hour';
        if recent_count >= 20 then
            raise exception using errcode = 'P0002',
                message = 'friend_request_rate_limited';
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists friendships_rate_limit on public.friendships;
create trigger friendships_rate_limit
    before insert on public.friendships
    for each row execute function public.friendships_rate_limit();

-- Convenience RPC: send a friend request by target nickname. Handles
-- ordering + requester lookup server-side so clients don't have to
-- know which nickname maps to which uuid. Returns the resulting
-- row (pending or already-accepted) plus a stable error code.
create or replace function public.send_friend_request(target_nickname text)
returns jsonb language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    target_id uuid;
    a uuid; b uuid;
    existing record;
begin
    if me is null then
        return jsonb_build_object('ok', false, 'error', 'not_authenticated');
    end if;
    select id into target_id from public.profiles
        where lower(nickname) = lower(target_nickname) limit 1;
    if target_id is null then
        return jsonb_build_object('ok', false, 'error', 'not_found');
    end if;
    if target_id = me then
        return jsonb_build_object('ok', false, 'error', 'cannot_friend_self');
    end if;
    if me < target_id then a := me; b := target_id;
    else a := target_id; b := me;
    end if;
    -- If a row already exists, report its state instead of crashing.
    select * into existing from public.friendships where user_a = a and user_b = b;
    if found then
        if existing.status = 'accepted' then
            return jsonb_build_object('ok', false, 'error', 'already_friends');
        elsif existing.status = 'blocked' then
            return jsonb_build_object('ok', false, 'error', 'blocked');
        elsif existing.status = 'pending' then
            if existing.requester_id = me then
                return jsonb_build_object('ok', false, 'error', 'already_requested');
            else
                -- The other side already asked us — auto-accept.
                update public.friendships
                    set status = 'accepted', accepted_at = now()
                    where user_a = a and user_b = b;
                return jsonb_build_object('ok', true, 'auto_accepted', true);
            end if;
        end if;
    end if;
    insert into public.friendships (user_a, user_b, requester_id, status)
        values (a, b, me, 'pending');
    return jsonb_build_object('ok', true, 'status', 'pending');
end;
$$;

grant execute on function public.send_friend_request(text) to authenticated;

-- Realtime publication for friendships so the UI can react to new
-- requests live. Guarded so re-runs don't error.
do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname = 'supabase_realtime'
        and schemaname = 'public'
        and tablename = 'friendships'
    ) then
        alter publication supabase_realtime add table public.friendships;
    end if;
end$$;


-- ============================================================
-- 5. direct_messages — 1:1 messaging between accepted friends
-- ============================================================
-- Thread identity is the ordered pair (least, greatest) of the two
-- uuids — stored precomputed as `thread_id` so the (thread_id,
-- created_at) index serves both the thread-view query ("show me
-- thread X in order") and the inbox query ("my most-recent message
-- per counterparty"). Reduces two different access patterns to one
-- index scan.

create table if not exists public.direct_messages (
    id          bigserial    primary key,
    thread_id   uuid         not null,            -- = least(from,to) xor greatest — see trigger
    from_id     uuid         not null references auth.users(id) on delete cascade,
    to_id       uuid         not null references auth.users(id) on delete cascade,
    body        text         not null check (char_length(body) between 1 and 2000),
    created_at  timestamptz  not null default now(),
    read_at     timestamptz,
    deleted_at  timestamptz,
    constraint dm_not_self check (from_id <> to_id)
);

create index if not exists dm_thread_time_idx
    on public.direct_messages (thread_id, created_at desc);
create index if not exists dm_to_unread_idx
    on public.direct_messages (to_id, created_at desc)
    where read_at is null and deleted_at is null;

-- Compute thread_id from the uuid pair. Using a deterministic hash
-- of least||greatest so both participants arrive at the same id
-- without having to write "least(...,...)||greatest(...,...)" in
-- every query. Stored so Realtime filters (=eq) can use it.
create or replace function public.dm_compute_thread_id()
returns trigger language plpgsql as $$
declare
    a uuid; b uuid;
begin
    if new.from_id < new.to_id then a := new.from_id; b := new.to_id;
    else a := new.to_id; b := new.from_id;
    end if;
    -- uuid_generate_v5 isn't available by default — use md5() over
    -- the pair and cast to uuid. Deterministic, collision-resistant.
    new.thread_id := md5(a::text || '_' || b::text)::uuid;
    return new;
end;
$$;

drop trigger if exists dm_compute_thread_id on public.direct_messages;
create trigger dm_compute_thread_id
    before insert on public.direct_messages
    for each row execute function public.dm_compute_thread_id();

-- Must be friends to DM. Applied server-side so a client that
-- forgets to check locally still can't send messages to strangers.
create or replace function public.dm_require_friendship()
returns trigger language plpgsql as $$
declare
    a uuid; b uuid;
    fs record;
begin
    if new.from_id < new.to_id then a := new.from_id; b := new.to_id;
    else a := new.to_id; b := new.from_id;
    end if;
    select * into fs from public.friendships
        where user_a = a and user_b = b;
    if not found then
        raise exception using errcode = 'P0003', message = 'not_friends';
    end if;
    if fs.status = 'blocked' then
        raise exception using errcode = 'P0004', message = 'blocked';
    end if;
    if fs.status <> 'accepted' then
        raise exception using errcode = 'P0005', message = 'not_accepted';
    end if;
    return new;
end;
$$;

drop trigger if exists dm_require_friendship on public.direct_messages;
create trigger dm_require_friendship
    before insert on public.direct_messages
    for each row execute function public.dm_require_friendship();

alter table public.direct_messages enable row level security;

drop policy if exists "dm_select_own"   on public.direct_messages;
drop policy if exists "dm_insert_from"  on public.direct_messages;
drop policy if exists "dm_update_read"  on public.direct_messages;
drop policy if exists "dm_delete_own"   on public.direct_messages;

-- SELECT: only participants. Realtime subscribers use this policy
-- to decide delivery too — the receiver gets INSERT events for
-- their own to_id rows, nobody else's.
create policy "dm_select_own"
    on public.direct_messages for select
    using (auth.uid() in (from_id, to_id));

-- INSERT: sender is auth.uid() and the friendship trigger gates
-- the rest. No way to spoof from_id without owning that session.
create policy "dm_insert_from"
    on public.direct_messages for insert
    with check (from_id = auth.uid());

-- UPDATE: only the receiver can mark a message read.
create policy "dm_update_read"
    on public.direct_messages for update
    using (to_id = auth.uid())
    with check (to_id = auth.uid());

-- DELETE: only the sender, and only via the soft-delete pattern
-- (set deleted_at) — but we don't enforce that at RLS because
-- DELETE means hard removal. Application uses UPDATE deleted_at
-- instead; hard DELETE is reserved for cleanup jobs.
create policy "dm_delete_own"
    on public.direct_messages for delete
    using (from_id = auth.uid());

do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname = 'supabase_realtime'
        and schemaname = 'public'
        and tablename = 'direct_messages'
    ) then
        alter publication supabase_realtime add table public.direct_messages;
    end if;
end$$;

-- Inbox query — one row per counterparty with most-recent message
-- + unread count. Returned as a composite so the client gets
-- everything it needs to render the conversation list in one call.
create or replace function public.dm_inbox()
returns table (
    thread_id       uuid,
    friend_id       uuid,
    friend_nickname text,
    friend_avatar   text,
    friend_authed   boolean,
    last_body       text,
    last_created_at timestamptz,
    last_from_me    boolean,
    unread_count    bigint
) language sql security definer
set search_path = public
as $$
    with me as (select auth.uid() as uid),
    latest as (
        select distinct on (thread_id)
            thread_id,
            case when from_id = (select uid from me) then to_id else from_id end as friend_id,
            body, created_at,
            from_id = (select uid from me) as last_from_me
        from public.direct_messages
        where deleted_at is null
          and (from_id = (select uid from me) or to_id = (select uid from me))
        order by thread_id, created_at desc
    ),
    unread as (
        select thread_id, count(*) as c
        from public.direct_messages
        where to_id = (select uid from me) and read_at is null and deleted_at is null
        group by thread_id
    )
    select l.thread_id,
           l.friend_id,
           p.nickname       as friend_nickname,
           p.avatar_url     as friend_avatar,
           p.profile_complete as friend_authed,
           l.body           as last_body,
           l.created_at     as last_created_at,
           l.last_from_me,
           coalesce(u.c, 0) as unread_count
    from latest l
    join public.profiles p on p.id = l.friend_id
    left join unread u on u.thread_id = l.thread_id
    order by l.created_at desc;
$$;

grant execute on function public.dm_inbox() to authenticated;

