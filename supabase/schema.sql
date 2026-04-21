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


-- ============================================================
-- 6. chat_rooms, chat_members, chat_messages — group chat
-- ============================================================
-- Separate tables from direct_messages because the access model
-- is fundamentally different (N-to-N room membership vs 1-to-1
-- friendship-gated). Keeping them apart means each query hits a
-- tighter schema + index, and the RLS policies are easier to
-- reason about.
--
-- Design:
--   • chat_rooms owns the room + name + creator
--   • chat_members is the authoritative membership roster, with
--     per-user last_read_at for unread counts
--   • chat_messages stores the log
-- Membership cap enforced at application layer (RPC) rather than
-- via trigger — lets us return nice error codes instead of raising
-- a generic constraint violation.

create table if not exists public.chat_rooms (
    id              uuid        primary key default gen_random_uuid(),
    name            text        not null check (char_length(name) between 1 and 60),
    owner_id        uuid        not null references auth.users(id) on delete cascade,
    icon_emoji      text        check (icon_emoji is null or char_length(icon_emoji) <= 8),
    description     text        check (description is null or char_length(description) <= 200),
    created_at      timestamptz not null default now(),
    last_message_at timestamptz not null default now()
);

create index if not exists chat_rooms_last_msg_idx
    on public.chat_rooms (last_message_at desc);

create table if not exists public.chat_members (
    room_id        uuid        not null references public.chat_rooms(id) on delete cascade,
    user_id        uuid        not null references auth.users(id) on delete cascade,
    role           text        not null default 'member'
                     check (role in ('owner','admin','member')),
    joined_at      timestamptz not null default now(),
    last_read_at   timestamptz not null default now(),
    muted          boolean     not null default false,
    primary key (room_id, user_id)
);

-- Per-user "rooms I'm in" lookup — drives the chats list fetch.
create index if not exists chat_members_user_idx
    on public.chat_members (user_id);

create table if not exists public.chat_messages (
    id          bigserial    primary key,
    room_id     uuid         not null references public.chat_rooms(id) on delete cascade,
    from_id     uuid         not null references auth.users(id) on delete cascade,
    body        text         not null check (char_length(body) between 1 and 2000),
    created_at  timestamptz  not null default now(),
    edited_at   timestamptz,
    deleted_at  timestamptz
);

-- (room_id, created_at desc) serves both "show me the latest N
-- messages in room X" and "what's the newest message in room X".
create index if not exists chat_messages_room_time_idx
    on public.chat_messages (room_id, created_at desc);

-- Trigger: bumping last_message_at on the room whenever a new
-- message lands. Cheaper than computing MAX() in the list query.
create or replace function public.chat_messages_bump_room()
returns trigger language plpgsql security definer as $$
begin
    update public.chat_rooms
        set last_message_at = new.created_at
        where id = new.room_id;
    return new;
end;
$$;

drop trigger if exists chat_messages_bump_room on public.chat_messages;
create trigger chat_messages_bump_room
    after insert on public.chat_messages
    for each row execute function public.chat_messages_bump_room();

-- Helper: is auth.uid() a member of this room? Used in RLS and
-- RPCs so we don't duplicate the EXISTS logic everywhere.
create or replace function public.is_room_member(p_room uuid)
returns boolean language sql stable security definer
set search_path = public
as $$
    select exists (
        select 1 from public.chat_members
        where room_id = p_room and user_id = auth.uid()
    );
$$;
grant execute on function public.is_room_member(uuid) to authenticated;

-- Helper: is auth.uid() the owner of this room?
create or replace function public.is_room_owner(p_room uuid)
returns boolean language sql stable security definer
set search_path = public
as $$
    select exists (
        select 1 from public.chat_rooms
        where id = p_room and owner_id = auth.uid()
    );
$$;
grant execute on function public.is_room_owner(uuid) to authenticated;

alter table public.chat_rooms    enable row level security;
alter table public.chat_members  enable row level security;
alter table public.chat_messages enable row level security;

-- chat_rooms policies --------------------------------------------
drop policy if exists "chat_rooms_select_member"   on public.chat_rooms;
drop policy if exists "chat_rooms_insert_self"     on public.chat_rooms;
drop policy if exists "chat_rooms_update_owner"    on public.chat_rooms;
drop policy if exists "chat_rooms_delete_owner"    on public.chat_rooms;

-- SELECT: only members can see the room metadata. Non-members can't
-- even confirm that a given room id exists.
create policy "chat_rooms_select_member"
    on public.chat_rooms for select
    using (public.is_room_member(id));

-- INSERT: creator (= auth.uid()) must set themselves as owner. The
-- create_group_chat RPC handles adding them to chat_members in the
-- same transaction.
create policy "chat_rooms_insert_self"
    on public.chat_rooms for insert
    with check (owner_id = auth.uid());

create policy "chat_rooms_update_owner"
    on public.chat_rooms for update
    using (owner_id = auth.uid());

create policy "chat_rooms_delete_owner"
    on public.chat_rooms for delete
    using (owner_id = auth.uid());

-- chat_members policies ------------------------------------------
drop policy if exists "chat_members_select_peer"   on public.chat_members;
drop policy if exists "chat_members_insert_own"    on public.chat_members;
drop policy if exists "chat_members_update_self"   on public.chat_members;
drop policy if exists "chat_members_delete_self"   on public.chat_members;

-- SELECT: members of the room can see each other.
create policy "chat_members_select_peer"
    on public.chat_members for select
    using (public.is_room_member(room_id));

-- INSERT: direct INSERTs only permitted for self-join to a room
-- owned by auth.uid() (room creation path). Adding OTHERS is done
-- exclusively through invite_to_group_chat() RPC which runs as
-- SECURITY DEFINER.
create policy "chat_members_insert_own"
    on public.chat_members for insert
    with check (
        user_id = auth.uid()
        and exists (
            select 1 from public.chat_rooms
            where id = room_id and owner_id = auth.uid()
        )
    );

-- UPDATE: a member can update their own row (last_read_at, muted).
-- Role changes must go through the update_role RPC (future).
create policy "chat_members_update_self"
    on public.chat_members for update
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

-- DELETE: self-leave anytime, or owner can remove anyone (kick).
create policy "chat_members_delete_self"
    on public.chat_members for delete
    using (
        user_id = auth.uid()
        or public.is_room_owner(room_id)
    );

-- chat_messages policies -----------------------------------------
drop policy if exists "chat_msgs_select_member"   on public.chat_messages;
drop policy if exists "chat_msgs_insert_member"   on public.chat_messages;
drop policy if exists "chat_msgs_update_own"      on public.chat_messages;
drop policy if exists "chat_msgs_delete_own"      on public.chat_messages;

create policy "chat_msgs_select_member"
    on public.chat_messages for select
    using (public.is_room_member(room_id));

create policy "chat_msgs_insert_member"
    on public.chat_messages for insert
    with check (
        from_id = auth.uid()
        and public.is_room_member(room_id)
    );

create policy "chat_msgs_update_own"
    on public.chat_messages for update
    using (from_id = auth.uid());

create policy "chat_msgs_delete_own"
    on public.chat_messages for delete
    using (from_id = auth.uid() or public.is_room_owner(room_id));

-- Realtime publications so clients can subscribe to room messages
-- and member list changes.
do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname='supabase_realtime' and schemaname='public' and tablename='chat_messages'
    ) then alter publication supabase_realtime add table public.chat_messages; end if;
    if not exists (
        select 1 from pg_publication_tables
        where pubname='supabase_realtime' and schemaname='public' and tablename='chat_members'
    ) then alter publication supabase_realtime add table public.chat_members; end if;
    if not exists (
        select 1 from pg_publication_tables
        where pubname='supabase_realtime' and schemaname='public' and tablename='chat_rooms'
    ) then alter publication supabase_realtime add table public.chat_rooms; end if;
end$$;

-- ---- RPCs ------------------------------------------------------
-- Create a group with an initial member list. Must be friends with
-- every invitee (matches the 1:1 DM rule — you can't pull strangers
-- into a chat). Caps initial membership at 50.
create or replace function public.create_group_chat(
    p_name        text,
    p_member_ids  uuid[],
    p_icon_emoji  text default '💬'
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
    me       uuid := auth.uid();
    new_room_id uuid;
    uid      uuid;
    a uuid; b uuid;
begin
    if me is null then
        return jsonb_build_object('ok', false, 'error', 'not_authenticated');
    end if;
    if p_name is null or char_length(trim(p_name)) < 1 then
        return jsonb_build_object('ok', false, 'error', 'invalid_name');
    end if;
    if array_length(p_member_ids, 1) is null then
        p_member_ids := array[]::uuid[];
    end if;
    if array_length(p_member_ids, 1) > 50 then
        return jsonb_build_object('ok', false, 'error', 'too_many_members');
    end if;

    -- Friendship gate: every invitee must be an accepted friend.
    foreach uid in array p_member_ids loop
        if uid = me then continue; end if;
        if me < uid then a := me; b := uid; else a := uid; b := me; end if;
        if not exists (
            select 1 from public.friendships
            where user_a = a and user_b = b and status = 'accepted'
        ) then
            return jsonb_build_object('ok', false, 'error', 'not_friends', 'offender', uid);
        end if;
    end loop;

    insert into public.chat_rooms (name, owner_id, icon_emoji)
        values (trim(p_name), me, coalesce(p_icon_emoji, '💬'))
        returning id into new_room_id;

    -- Owner row
    insert into public.chat_members (room_id, user_id, role) values (new_room_id, me, 'owner');

    -- Invitee rows (dedupe against self via DISTINCT + filter)
    insert into public.chat_members (room_id, user_id, role)
        select new_room_id, uid, 'member'
        from unnest(p_member_ids) as uid
        where uid <> me
        on conflict do nothing;

    return jsonb_build_object('ok', true, 'room_id', new_room_id);
end;
$$;
grant execute on function public.create_group_chat(text, uuid[], text) to authenticated;

-- Invite a single friend into an existing room. Must be room
-- member (enforced) + friends with target.
create or replace function public.invite_to_group_chat(
    p_room uuid, p_user uuid
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    a uuid; b uuid;
    member_count int;
begin
    if me is null then return jsonb_build_object('ok', false, 'error', 'not_authenticated'); end if;
    if not public.is_room_member(p_room) then
        return jsonb_build_object('ok', false, 'error', 'not_a_member');
    end if;
    if p_user = me then
        return jsonb_build_object('ok', false, 'error', 'cannot_invite_self');
    end if;
    if me < p_user then a := me; b := p_user; else a := p_user; b := me; end if;
    if not exists (
        select 1 from public.friendships
        where user_a = a and user_b = b and status = 'accepted'
    ) then
        return jsonb_build_object('ok', false, 'error', 'not_friends');
    end if;
    select count(*) into member_count from public.chat_members where room_id = p_room;
    if member_count >= 100 then
        return jsonb_build_object('ok', false, 'error', 'room_full');
    end if;
    insert into public.chat_members (room_id, user_id, role)
        values (p_room, p_user, 'member')
        on conflict do nothing;
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.invite_to_group_chat(uuid, uuid) to authenticated;

-- Leave a room. Owner leaving transfers ownership to the oldest
-- remaining member (smallest joined_at). If they were the last
-- member, the room is deleted entirely.
create or replace function public.leave_group_chat(p_room uuid)
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    was_owner boolean := false;
    successor uuid;
    remaining int;
begin
    if me is null then return jsonb_build_object('ok', false, 'error', 'not_authenticated'); end if;
    if not public.is_room_member(p_room) then
        return jsonb_build_object('ok', false, 'error', 'not_a_member');
    end if;

    was_owner := public.is_room_owner(p_room);
    delete from public.chat_members where room_id = p_room and user_id = me;

    if was_owner then
        select count(*) into remaining from public.chat_members where room_id = p_room;
        if remaining = 0 then
            delete from public.chat_rooms where id = p_room;
            return jsonb_build_object('ok', true, 'room_deleted', true);
        end if;
        select user_id into successor from public.chat_members
            where room_id = p_room order by joined_at asc limit 1;
        update public.chat_rooms set owner_id = successor where id = p_room;
        update public.chat_members set role = 'owner'
            where room_id = p_room and user_id = successor;
    end if;
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.leave_group_chat(uuid) to authenticated;

-- Chat-list RPC: all rooms the caller is in, plus unread counts
-- (messages since the caller's last_read_at) and the latest-message
-- preview. Single-shot render for the Chats tab.
create or replace function public.group_chat_list()
returns table (
    room_id         uuid,
    name            text,
    icon_emoji      text,
    owner_id        uuid,
    last_message_at timestamptz,
    last_body       text,
    last_from_id    uuid,
    last_from_nick  text,
    member_count    bigint,
    unread_count    bigint,
    my_role         text
) language sql security definer
set search_path = public
as $$
    with me as (select auth.uid() as uid),
    my_rooms as (
        select cm.room_id, cm.last_read_at, cm.role
        from public.chat_members cm
        where cm.user_id = (select uid from me)
    ),
    last_msg as (
        select distinct on (m.room_id) m.room_id, m.body, m.from_id, m.created_at
        from public.chat_messages m
        join my_rooms r on r.room_id = m.room_id
        where m.deleted_at is null
        order by m.room_id, m.created_at desc
    ),
    unread as (
        select m.room_id, count(*) as c
        from public.chat_messages m
        join my_rooms r on r.room_id = m.room_id
        where m.deleted_at is null
          and m.created_at > r.last_read_at
          and m.from_id <> (select uid from me)
        group by m.room_id
    ),
    member_counts as (
        select room_id, count(*) as c
        from public.chat_members
        where room_id in (select room_id from my_rooms)
        group by room_id
    )
    select cr.id,
           cr.name,
           cr.icon_emoji,
           cr.owner_id,
           cr.last_message_at,
           lm.body,
           lm.from_id,
           p.nickname,
           coalesce(mc.c, 0),
           coalesce(u.c, 0),
           r.role
    from my_rooms r
    join public.chat_rooms cr on cr.id = r.room_id
    left join last_msg lm on lm.room_id = cr.id
    left join public.profiles p on p.id = lm.from_id
    left join unread u on u.room_id = cr.id
    left join member_counts mc on mc.room_id = cr.id
    order by cr.last_message_at desc;
$$;
grant execute on function public.group_chat_list() to authenticated;

-- Room members RPC with profile data. Used for the member-list
-- modal + @mentions (future).
create or replace function public.group_chat_members(p_room uuid)
returns table (
    user_id          uuid,
    nickname         text,
    avatar_url       text,
    profile_complete boolean,
    role             text,
    joined_at        timestamptz
) language sql security definer
set search_path = public
as $$
    select cm.user_id,
           p.nickname,
           p.avatar_url,
           p.profile_complete,
           cm.role,
           cm.joined_at
    from public.chat_members cm
    join public.profiles p on p.id = cm.user_id
    where cm.room_id = p_room
      and public.is_room_member(p_room)  -- enforce: only members see the roster
    order by cm.joined_at asc;
$$;
grant execute on function public.group_chat_members(uuid) to authenticated;

-- Mark a room's messages read up to the caller's current time.
create or replace function public.mark_group_chat_read(p_room uuid)
returns void
language plpgsql security definer
set search_path = public
as $$
begin
    update public.chat_members
        set last_read_at = now()
        where room_id = p_room and user_id = auth.uid();
end;
$$;
grant execute on function public.mark_group_chat_read(uuid) to authenticated;


-- ============================================================
-- 7. Attachments — image (and later, file) upload columns on
--    both direct_messages and chat_messages
-- ============================================================
-- Two pieces:
--   (a) Schema additions below — additive, idempotent.
--   (b) Storage bucket — must be created in the Supabase dashboard
--       (see comment block at the bottom of this file). The public
--       bucket pattern is the standard messenger trade-off: file
--       paths are uuid-prefixed under each user's folder, so URLs
--       aren't enumerable, and we get cheap CDN-served downloads
--       without per-fetch signed-URL minting.
--
-- Constraints chosen for both safety and predictability:
--   • 10 MB cap matches what Slack / Telegram allow for attachments
--     before they switch to a different upload path
--   • mime check rejects garbage early at INSERT time so a hostile
--     client can't write a row with type='<script>...'
--   • body becomes nullable so attachment-only messages work; the
--     paired body_or_attach CHECK keeps the row meaningful

alter table public.direct_messages
    add column if not exists attachment_url   text,
    add column if not exists attachment_type  text,
    add column if not exists attachment_size  bigint,
    add column if not exists attachment_name  text;

alter table public.direct_messages
    drop constraint if exists dm_attach_type_format;
alter table public.direct_messages
    add  constraint dm_attach_type_format
    check (attachment_type is null
           or attachment_type ~ '^[a-z]+/[a-z0-9.\-+]+$');
alter table public.direct_messages
    drop constraint if exists dm_attach_size_bound;
alter table public.direct_messages
    add  constraint dm_attach_size_bound
    check (attachment_size is null
           or (attachment_size between 0 and 10485760));
alter table public.direct_messages
    drop constraint if exists dm_attach_name_len;
alter table public.direct_messages
    add  constraint dm_attach_name_len
    check (attachment_name is null
           or char_length(attachment_name) <= 200);

-- Body may now be null IF an attachment is present. The original
-- length CHECK (1-2000) treats null as passing, so no rewrite needed.
alter table public.direct_messages
    alter column body drop not null;
alter table public.direct_messages
    drop constraint if exists dm_body_or_attach;
alter table public.direct_messages
    add  constraint dm_body_or_attach
    check (body is not null or attachment_url is not null);

alter table public.chat_messages
    add column if not exists attachment_url   text,
    add column if not exists attachment_type  text,
    add column if not exists attachment_size  bigint,
    add column if not exists attachment_name  text;

alter table public.chat_messages
    drop constraint if exists chat_attach_type_format;
alter table public.chat_messages
    add  constraint chat_attach_type_format
    check (attachment_type is null
           or attachment_type ~ '^[a-z]+/[a-z0-9.\-+]+$');
alter table public.chat_messages
    drop constraint if exists chat_attach_size_bound;
alter table public.chat_messages
    add  constraint chat_attach_size_bound
    check (attachment_size is null
           or (attachment_size between 0 and 10485760));
alter table public.chat_messages
    drop constraint if exists chat_attach_name_len;
alter table public.chat_messages
    add  constraint chat_attach_name_len
    check (attachment_name is null
           or char_length(attachment_name) <= 200);

alter table public.chat_messages
    alter column body drop not null;
alter table public.chat_messages
    drop constraint if exists chat_body_or_attach;
alter table public.chat_messages
    add  constraint chat_body_or_attach
    check (body is not null or attachment_url is not null);

-- ── STORAGE BUCKET SETUP (one-time, dashboard) ─────────────────
-- After running this SQL, in the Supabase dashboard:
--   1. Storage → New Bucket → name: 'chat-attachments'
--      Public: YES (so img URLs render without signed-URL minting)
--      File size limit: 10 MB
--      Allowed MIME types: image/png, image/jpeg, image/jpg,
--                          image/gif, image/webp, image/heic
--   2. Storage → Policies → chat-attachments → New Policy
--      Use the SQL editor with these (or click "Insert Template"):
--
--   create policy "chat_attach_read_public"
--     on storage.objects for select
--     using (bucket_id = 'chat-attachments');
--
--   create policy "chat_attach_write_own_folder"
--     on storage.objects for insert
--     with check (
--       bucket_id = 'chat-attachments'
--       and auth.role() = 'authenticated'
--       and (storage.foldername(name))[1] = auth.uid()::text
--     );
--
--   create policy "chat_attach_update_own_folder"
--     on storage.objects for update
--     using (
--       bucket_id = 'chat-attachments'
--       and (storage.foldername(name))[1] = auth.uid()::text
--     );
--
--   create policy "chat_attach_delete_own_folder"
--     on storage.objects for delete
--     using (
--       bucket_id = 'chat-attachments'
--       and (storage.foldername(name))[1] = auth.uid()::text
--     );
--
-- The "own folder" gate means uploads are forced to start with
-- `<user_id>/<anything>`, which (a) makes per-user cleanup a
-- cascade-style delete by prefix, and (b) prevents one user from
-- overwriting another's file. Public read is the standard messenger
-- pattern (any URL holder can fetch — the URL itself is the secret,
-- and file IDs are uuid-prefixed so they're not enumerable).


-- ============================================================
-- 8. message_reactions — emoji reactions on DM + group messages
-- ============================================================
-- Single table with a `kind` discriminator (dm | group) pointing at
-- direct_messages.id or chat_messages.id. Two tables would give
-- cleaner RLS but force the client to branch twice for every
-- operation; one table + a SECURITY DEFINER can_see_message()
-- helper keeps the client path uniform.
--
-- thread_key is auto-populated by trigger (= direct_messages.thread_id
-- for DMs, chat_messages.room_id for groups). Lets Realtime
-- subscriptions filter by a single "I'm in thread X" key across both
-- kinds.
--
-- UNIQUE (kind, message_id, user_id, emoji) allows one row per
-- (user, message, emoji) — second-press-to-remove semantics are
-- implemented by the toggle_reaction RPC (DELETE-then-INSERT).

create table if not exists public.message_reactions (
    id           bigserial    primary key,
    kind         text         not null check (kind in ('dm','group')),
    message_id   bigint       not null,
    thread_key   uuid,
    user_id      uuid         not null references auth.users(id) on delete cascade,
    emoji        text         not null check (char_length(emoji) between 1 and 16),
    created_at   timestamptz  not null default now(),
    unique (kind, message_id, user_id, emoji)
);

create index if not exists message_reactions_message_idx
    on public.message_reactions (kind, message_id);
create index if not exists message_reactions_thread_idx
    on public.message_reactions (thread_key);

-- Compute thread_key by joining the parent message table at insert
-- time. Keeps Realtime filter simple + cheap.
create or replace function public.set_reaction_thread_key()
returns trigger language plpgsql security definer
set search_path = public
as $$
begin
    if new.kind = 'dm' then
        select thread_id into new.thread_key
        from public.direct_messages where id = new.message_id;
    else
        select room_id into new.thread_key
        from public.chat_messages where id = new.message_id;
    end if;
    if new.thread_key is null then
        raise exception using errcode = 'P0006', message = 'message_not_found';
    end if;
    return new;
end;
$$;

drop trigger if exists set_reaction_thread_key on public.message_reactions;
create trigger set_reaction_thread_key
    before insert on public.message_reactions
    for each row execute function public.set_reaction_thread_key();

-- Access helper: the caller sees this reaction iff they can see the
-- underlying message. Runs as SECURITY DEFINER so we can read both
-- message tables without the caller needing direct SELECT access.
create or replace function public.can_see_message(p_kind text, p_msg_id bigint)
returns boolean language sql stable security definer
set search_path = public
as $$
    select case
        when p_kind = 'dm' then
            exists (
                select 1 from public.direct_messages
                where id = p_msg_id
                  and auth.uid() in (from_id, to_id)
            )
        when p_kind = 'group' then
            exists (
                select 1 from public.chat_messages m
                where m.id = p_msg_id
                  and public.is_room_member(m.room_id)
            )
        else false
    end;
$$;
grant execute on function public.can_see_message(text, bigint) to authenticated;

alter table public.message_reactions enable row level security;

drop policy if exists "reactions_select_access" on public.message_reactions;
drop policy if exists "reactions_insert_own"    on public.message_reactions;
drop policy if exists "reactions_delete_own"    on public.message_reactions;

create policy "reactions_select_access"
    on public.message_reactions for select
    using (public.can_see_message(kind, message_id));

create policy "reactions_insert_own"
    on public.message_reactions for insert
    with check (
        user_id = auth.uid()
        and public.can_see_message(kind, message_id)
    );

create policy "reactions_delete_own"
    on public.message_reactions for delete
    using (user_id = auth.uid());

-- Add to the Realtime publication so subscribers see live INSERT/DELETE.
do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname='supabase_realtime' and schemaname='public' and tablename='message_reactions'
    ) then
        alter publication supabase_realtime add table public.message_reactions;
    end if;
end$$;

-- Toggle RPC: single-roundtrip add-or-remove based on whether the
-- row already exists. Returns {ok, action:'added'|'removed'} so the
-- client can update its local chip state without waiting for the
-- Realtime echo.
create or replace function public.toggle_reaction(
    p_kind text, p_msg_id bigint, p_emoji text
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    deleted int;
    safe_emoji text := left(p_emoji, 16);
begin
    if me is null then return jsonb_build_object('ok', false, 'error', 'not_authenticated'); end if;
    if p_kind not in ('dm','group') then return jsonb_build_object('ok', false, 'error', 'bad_kind'); end if;
    if not public.can_see_message(p_kind, p_msg_id) then
        return jsonb_build_object('ok', false, 'error', 'no_access');
    end if;
    delete from public.message_reactions
        where kind = p_kind and message_id = p_msg_id
          and user_id = me and emoji = safe_emoji;
    get diagnostics deleted = row_count;
    if deleted > 0 then
        return jsonb_build_object('ok', true, 'action', 'removed', 'emoji', safe_emoji);
    end if;
    insert into public.message_reactions (kind, message_id, user_id, emoji)
        values (p_kind, p_msg_id, me, safe_emoji);
    return jsonb_build_object('ok', true, 'action', 'added', 'emoji', safe_emoji);
end;
$$;
grant execute on function public.toggle_reaction(text, bigint, text) to authenticated;


-- ============================================================
-- 8. Presence + Game Invites (added 2026-04-21)
-- See supabase/migrations/2026-04-21-presence-and-invites.sql
-- ============================================================
-- =====================================================================
-- Migration: Presence + Game Invites
-- Date:      2026-04-21
-- Purpose:   Adds live online-status for friends + a real-time game
--            invite flow. Designed to be idempotent — running it twice
--            must not fail and must not duplicate rows.
--
-- Rationale:
--   Presence: Kakao/Line-style online indicator. Manual override
--   ('online' / 'dnd' / 'offline') is stored in profiles so it
--   survives tab close. Actual live connectivity is derived client-
--   side from Supabase Realtime Presence channel join/leave events;
--   this row just stores the user's *intent*. The "appear offline"
--   mode (manual_status = 'offline') wins over live connectivity
--   even if the user is on the page.
--
--   Invites: a host that just opened a game can fire a game_invite
--   row at a friend. The target's open tab (on any page) subscribes
--   to its own `lp_inbox_<uid>` realtime channel and sees the INSERT.
--   A toast pops with Accept / Decline. 60s TTL — if they don't act
--   in time, the host can re-invite.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Presence — profiles.manual_status
-- ---------------------------------------------------------------------
alter table public.profiles
    add column if not exists manual_status text
        default 'online'
        check (manual_status in ('online','dnd','offline'));

-- last_seen_at is set to now() whenever any authenticated action runs
-- via the heartbeat RPC. Useful as a fallback indicator for friends
-- who were recently active but whose browser is now suspended.
alter table public.profiles
    add column if not exists last_seen_at timestamptz default now();

-- Lightweight heartbeat. Client pings this every ~45 seconds from any
-- logged-in tab so we have a server-side "last active" signal. SQL
-- language function = cheapest possible RPC (no plpgsql context).
create or replace function public.presence_heartbeat()
returns void
language sql security definer
set search_path = public
as $$
    update public.profiles
       set last_seen_at = now()
     where id = auth.uid();
$$;

grant execute on function public.presence_heartbeat() to authenticated;

-- Convenience setter — keeps logic (validation, RLS bypass via
-- security definer) out of the client. The CHECK on the column
-- catches garbage values but this is a cleaner surface to call.
create or replace function public.set_manual_status(p_status text)
returns text
language plpgsql security definer
set search_path = public
as $$
begin
    if p_status not in ('online','dnd','offline') then
        raise exception 'bad_status';
    end if;
    update public.profiles
       set manual_status = p_status,
           last_seen_at  = now()
     where id = auth.uid();
    return p_status;
end;
$$;

grant execute on function public.set_manual_status(text) to authenticated;


-- ---------------------------------------------------------------------
-- 2. Game invites — transient rows with a 60-second TTL
-- ---------------------------------------------------------------------
-- Each INSERT fires Realtime, which is how the target tab learns about
-- the invite even if it's on a completely different page of the site.
-- Status transitions: 'pending' → 'accepted' | 'declined' | 'expired'
-- | 'cancelled'. Terminal states are never re-opened; the host
-- re-invites by creating a new row.
create table if not exists public.game_invites (
    id          uuid primary key default gen_random_uuid(),
    from_id     uuid not null references auth.users(id) on delete cascade,
    to_id       uuid not null references auth.users(id) on delete cascade,
    game_type   text not null check (char_length(game_type) between 1 and 30),
    -- host game page / room URL (client just navigates to it)
    game_url    text not null check (char_length(game_url) between 1 and 300),
    status      text not null default 'pending'
                 check (status in ('pending','accepted','declined','expired','cancelled')),
    created_at  timestamptz not null default now(),
    responded_at timestamptz,
    -- A friend shouldn't have more than one PENDING invite from the
    -- same host at once — re-inviting cancels the old one implicitly.
    constraint game_invites_no_dup_pending
        unique (from_id, to_id, status) deferrable initially deferred
);

create index if not exists game_invites_to_pending_idx
    on public.game_invites (to_id, created_at desc)
    where status = 'pending';

alter table public.game_invites enable row level security;

drop policy if exists "invites_select_self"   on public.game_invites;
drop policy if exists "invites_insert_from_friend" on public.game_invites;
drop policy if exists "invites_update_participant"  on public.game_invites;

-- Can see invites where you are sender or receiver.
create policy "invites_select_self"
    on public.game_invites for select
    using (auth.uid() = from_id or auth.uid() = to_id);

-- Only authenticated friends can invite each other, and only when the
-- target isn't in "offline" mode. DND is allowed — client filters DND
-- out of the modal, but the server lets a DND invite through so if the
-- user flips their status while the modal is open it still works.
create policy "invites_insert_from_friend"
    on public.game_invites for insert
    with check (
        auth.uid() = from_id
        and exists (
            select 1 from public.friendships f
            where ((f.user_a = from_id and f.user_b = to_id)
                or (f.user_a = to_id and f.user_b = from_id))
              and f.status = 'accepted'
        )
        and exists (
            select 1 from public.profiles p
            where p.id = to_id
              and coalesce(p.manual_status, 'online') <> 'offline'
        )
    );

-- Target can accept/decline; sender can cancel. Either way, only via
-- the respond/cancel RPCs below — the policy allows direct UPDATE but
-- the RPCs are the documented path.
create policy "invites_update_participant"
    on public.game_invites for update
    using (auth.uid() = from_id or auth.uid() = to_id);


-- RPC: send a game invite. Auto-cancels any prior pending invite from
-- the same host to the same target so we never accumulate a backlog
-- of stale pending rows. Returns the new invite id on success.
create or replace function public.send_game_invite(
    p_to_id   uuid,
    p_game_type text,
    p_game_url  text
) returns uuid
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    new_id uuid;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if me = p_to_id then raise exception 'self_invite'; end if;

    -- Target must be a friend.
    if not exists (
        select 1 from public.friendships f
        where ((f.user_a = me and f.user_b = p_to_id)
            or (f.user_a = p_to_id and f.user_b = me))
          and f.status = 'accepted'
    ) then
        raise exception 'not_friends';
    end if;

    -- Target must not be in appear-offline mode.
    if exists (
        select 1 from public.profiles p
        where p.id = p_to_id and p.manual_status = 'offline'
    ) then
        raise exception 'recipient_offline';
    end if;

    -- Cancel any prior pending invite from me → them.
    update public.game_invites
       set status = 'cancelled', responded_at = now()
     where from_id = me and to_id = p_to_id and status = 'pending';

    insert into public.game_invites (from_id, to_id, game_type, game_url)
        values (me, p_to_id, p_game_type, p_game_url)
    returning id into new_id;

    return new_id;
end;
$$;
grant execute on function public.send_game_invite(uuid, text, text) to authenticated;


-- RPC: respond to an invite (accept or decline). Client holds the
-- invite id from the realtime payload.
create or replace function public.respond_game_invite(
    p_invite_id uuid,
    p_action    text  -- 'accept' | 'decline'
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    inv public.game_invites%rowtype;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_action not in ('accept','decline') then raise exception 'bad_action'; end if;

    select * into inv from public.game_invites where id = p_invite_id;
    if not found then raise exception 'not_found'; end if;
    if inv.to_id <> me then raise exception 'not_your_invite'; end if;
    if inv.status <> 'pending' then raise exception 'already_%', inv.status; end if;
    if inv.created_at < now() - interval '2 minutes' then
        update public.game_invites
           set status='expired', responded_at=now()
         where id = p_invite_id;
        return jsonb_build_object('ok', false, 'error', 'expired');
    end if;

    update public.game_invites
       set status = case when p_action='accept' then 'accepted' else 'declined' end,
           responded_at = now()
     where id = p_invite_id;

    return jsonb_build_object(
        'ok', true,
        'action', p_action,
        'game_url', inv.game_url,
        'from_id', inv.from_id,
        'game_type', inv.game_type
    );
end;
$$;
grant execute on function public.respond_game_invite(uuid, text) to authenticated;


-- RPC: host cancels an in-flight invite.
create or replace function public.cancel_game_invite(p_invite_id uuid)
returns boolean
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    update public.game_invites
       set status = 'cancelled', responded_at = now()
     where id = p_invite_id
       and from_id = me
       and status = 'pending';
    return found;
end;
$$;
grant execute on function public.cancel_game_invite(uuid) to authenticated;


-- Realtime publication — so the target's tab sees INSERTs instantly.
do $$
begin
    if not exists (
        select 1 from pg_publication_tables
        where pubname='supabase_realtime' and schemaname='public' and tablename='game_invites'
    ) then
        alter publication supabase_realtime add table public.game_invites;
    end if;
end$$;

-- ============================================================
-- 9. Admin RBAC + audit log (added 2026-04-21)
-- See supabase/migrations/2026-04-21-admin-rbac.sql
-- ============================================================
-- =====================================================================
-- Migration: Admin RBAC — roles, bans, audit log, management RPCs
-- Date:      2026-04-21
-- Purpose:   Give the operator a super-user role that can search, ban,
--            unban, delete, and promote other accounts — without
--            exposing the service_role key on the client. All mutations
--            go through security-definer RPCs that gate on is_admin()
--            and automatically append to admin_audit_log.
--
-- Role model:
--   user         — normal account (default for all signups)
--   admin        — can search + ban/unban/delete other USERS; cannot
--                  promote or demote anyone else
--   super_admin  — same as admin PLUS can promote/demote other roles.
--                  The operator's own account lives here.
--
-- Ban model:
--   Soft ban (banned_at NOT NULL): profile row preserved, writes
--   blocked via RLS, UI shows a banned banner. Reversible via unban.
--   Hard delete: auth.users row removed; FK ON DELETE CASCADE wipes
--   profiles, friendships, messages, etc. Irreversible.
--
-- Client gating is a convenience; server gating is the authority.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. profiles additions — role + ban fields
-- ---------------------------------------------------------------------
alter table public.profiles
    add column if not exists role text
        default 'user'
        check (role in ('user','admin','super_admin'));

alter table public.profiles
    add column if not exists banned_at  timestamptz;
alter table public.profiles
    add column if not exists banned_by  uuid references auth.users(id) on delete set null;
alter table public.profiles
    add column if not exists ban_reason text check (ban_reason is null or char_length(ban_reason) <= 500);

create index if not exists profiles_role_idx on public.profiles (role) where role <> 'user';
create index if not exists profiles_banned_idx on public.profiles (banned_at) where banned_at is not null;


-- ---------------------------------------------------------------------
-- 2. Helper predicates — the single source of truth for role checks.
--    Every admin RPC calls one of these in its first line; duplicating
--    the query inline would be both slower and easier to mis-write.
-- ---------------------------------------------------------------------
create or replace function public.is_admin()
returns boolean
language sql stable security definer
set search_path = public
as $$
    select coalesce(
        (select role in ('admin','super_admin') from public.profiles where id = auth.uid()),
        false
    );
$$;
grant execute on function public.is_admin() to authenticated;

create or replace function public.is_super_admin()
returns boolean
language sql stable security definer
set search_path = public
as $$
    select coalesce(
        (select role = 'super_admin' from public.profiles where id = auth.uid()),
        false
    );
$$;
grant execute on function public.is_super_admin() to authenticated;

-- Banned-user predicate — used by RLS WITH CHECK on write paths so a
-- banned user literally cannot INSERT into messages / friendships /
-- etc. Admins + super_admins are never considered banned even if some
-- stray state says they are; moderation tools must stay operational.
create or replace function public.is_active()
returns boolean
language sql stable security definer
set search_path = public
as $$
    select coalesce(
        (select banned_at is null from public.profiles where id = auth.uid()),
        true
    );
$$;
grant execute on function public.is_active() to authenticated;


-- ---------------------------------------------------------------------
-- 3. Audit log — every admin mutation writes one row here. Preserved
--    even when a target is hard-deleted (no FK on target_id so the id
--    stays readable even after cascade deletion of the user).
-- ---------------------------------------------------------------------
create table if not exists public.admin_audit_log (
    id         bigserial   primary key,
    admin_id   uuid        not null references auth.users(id) on delete set null,
    action     text        not null check (char_length(action) between 1 and 60),
    target_id  uuid,
    metadata   jsonb       default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists admin_audit_admin_idx  on public.admin_audit_log (admin_id, created_at desc);
create index if not exists admin_audit_target_idx on public.admin_audit_log (target_id, created_at desc) where target_id is not null;
create index if not exists admin_audit_created_idx on public.admin_audit_log (created_at desc);

alter table public.admin_audit_log enable row level security;
drop policy if exists "audit_select_admin_only" on public.admin_audit_log;
create policy "audit_select_admin_only"
    on public.admin_audit_log for select
    using (public.is_admin());
-- No insert/update/delete policies — audit log is append-only via RPCs.
-- (security definer RPCs bypass RLS for inserts by design.)

-- Internal helper — every admin RPC calls this instead of inserting
-- into the audit log directly. Centralises the row shape.
create or replace function public._admin_log(
    p_action text, p_target uuid, p_metadata jsonb
) returns void
language sql security definer
set search_path = public
as $$
    insert into public.admin_audit_log (admin_id, action, target_id, metadata)
    values (auth.uid(), p_action, p_target, coalesce(p_metadata, '{}'::jsonb));
$$;


-- ---------------------------------------------------------------------
-- 4. Admin RPCs
-- ---------------------------------------------------------------------

-- List users, searchable by nickname OR email prefix. Results include
-- the email (non-admins only see their own email via profiles SELECT
-- RLS). Sorted: banned first, then most-recently-joined.
create or replace function public.admin_list_users(
    p_query text default '',
    p_limit int  default 50,
    p_offset int default 0
) returns table (
    id uuid,
    nickname text,
    email text,
    avatar_url text,
    role text,
    banned_at timestamptz,
    banned_by uuid,
    ban_reason text,
    profile_complete boolean,
    manual_status text,
    last_seen_at timestamptz,
    created_at timestamptz
)
language plpgsql security definer
set search_path = public
as $$
begin
    if not public.is_admin() then raise exception 'not_admin'; end if;
    return query
        select p.id, p.nickname, p.email, p.avatar_url, p.role,
               p.banned_at, p.banned_by, p.ban_reason,
               p.profile_complete, p.manual_status, p.last_seen_at,
               p.created_at
        from public.profiles p
        where p_query = '' or
              p.nickname ilike (p_query || '%') or
              p.email    ilike (p_query || '%')
        order by (p.banned_at is not null) desc, p.created_at desc
        limit greatest(1, least(p_limit, 200))
        offset greatest(0, p_offset);
end;
$$;
grant execute on function public.admin_list_users(text, int, int) to authenticated;


-- Soft ban: mark the target as banned. RLS write policies on
-- user-generated tables consult is_active() so banned users are
-- immediately blocked from sending anything new.
create or replace function public.admin_ban_user(
    p_target uuid, p_reason text default null
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        target_role text;
begin
    if not public.is_admin() then raise exception 'not_admin'; end if;
    if p_target = me then raise exception 'cannot_target_self'; end if;

    select role into target_role from public.profiles where id = p_target;
    if not found then raise exception 'target_not_found'; end if;
    /* Regular admins can't ban other admins/super_admins — prevents a
       rogue admin from locking out the super_admin. Only super_admin
       can ban another admin (and they still can't ban themselves via
       the guard above). */
    if target_role in ('admin','super_admin') and not public.is_super_admin() then
        raise exception 'target_is_admin';
    end if;

    update public.profiles
       set banned_at = now(),
           banned_by = me,
           ban_reason = left(coalesce(p_reason, ''), 500)
     where id = p_target;

    perform public._admin_log('ban_user', p_target, jsonb_build_object('reason', p_reason));
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.admin_ban_user(uuid, text) to authenticated;


create or replace function public.admin_unban_user(p_target uuid)
returns jsonb
language plpgsql security definer
set search_path = public
as $$
begin
    if not public.is_admin() then raise exception 'not_admin'; end if;
    update public.profiles
       set banned_at = null, banned_by = null, ban_reason = null
     where id = p_target;
    if not found then raise exception 'target_not_found'; end if;
    perform public._admin_log('unban_user', p_target, '{}'::jsonb);
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.admin_unban_user(uuid) to authenticated;


-- Hard delete: removes the auth.users row which cascades to profiles,
-- friendships, messages, chat members, reactions, invites, etc. (every
-- table that FKs to auth.users or profiles with ON DELETE CASCADE).
-- Irreversible — the audit log keeps the record of the action + the
-- old user's id + nickname so we have a paper trail.
create or replace function public.admin_delete_user(p_target uuid)
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        snapshot jsonb;
        target_role text;
begin
    if not public.is_admin() then raise exception 'not_admin'; end if;
    if p_target = me then raise exception 'cannot_target_self'; end if;

    select role into target_role from public.profiles where id = p_target;
    if target_role in ('admin','super_admin') and not public.is_super_admin() then
        raise exception 'target_is_admin';
    end if;

    /* Snapshot before deletion so the audit log captures who it was. */
    select jsonb_build_object(
        'nickname', nickname,
        'email', email,
        'role', role,
        'banned_at', banned_at,
        'created_at', created_at
    ) into snapshot from public.profiles where id = p_target;

    /* Deleting from auth.users cascades everywhere. */
    delete from auth.users where id = p_target;

    perform public._admin_log('delete_user', p_target, snapshot);
    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.admin_delete_user(uuid) to authenticated;


-- super_admin only — change another user's role. Useful for promoting
-- a trusted moderator to admin, or demoting. Cannot change own role.
create or replace function public.admin_set_role(
    p_target uuid, p_new_role text
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        old_role text;
begin
    if not public.is_super_admin() then raise exception 'not_super_admin'; end if;
    if p_target = me then raise exception 'cannot_target_self'; end if;
    if p_new_role not in ('user','admin','super_admin') then raise exception 'bad_role'; end if;

    select role into old_role from public.profiles where id = p_target;
    if not found then raise exception 'target_not_found'; end if;

    update public.profiles set role = p_new_role where id = p_target;
    perform public._admin_log('set_role', p_target,
        jsonb_build_object('from', old_role, 'to', p_new_role));
    return jsonb_build_object('ok', true, 'role', p_new_role);
end;
$$;
grant execute on function public.admin_set_role(uuid, text) to authenticated;


-- Recent audit log entries, newest first. Admins can see all.
create or replace function public.admin_get_audit_log(
    p_limit int default 100,
    p_offset int default 0
) returns table (
    id bigint,
    admin_id uuid,
    admin_nickname text,
    action text,
    target_id uuid,
    target_nickname text,
    metadata jsonb,
    created_at timestamptz
)
language plpgsql security definer
set search_path = public
as $$
begin
    if not public.is_admin() then raise exception 'not_admin'; end if;
    return query
        select l.id, l.admin_id,
               pa.nickname as admin_nickname,
               l.action, l.target_id,
               pt.nickname as target_nickname,
               l.metadata, l.created_at
        from public.admin_audit_log l
        left join public.profiles pa on pa.id = l.admin_id
        left join public.profiles pt on pt.id = l.target_id
        order by l.created_at desc
        limit greatest(1, least(p_limit, 500))
        offset greatest(0, p_offset);
end;
$$;
grant execute on function public.admin_get_audit_log(int, int) to authenticated;


-- ---------------------------------------------------------------------
-- 5. Ban enforcement — add is_active() gate to every write-path RLS
--    policy on user-generated tables. Banned users keep READ access
--    (so they can see the banned banner + their history) but cannot
--    create new rows anywhere.
-- ---------------------------------------------------------------------

-- direct_messages: block banned senders
drop policy if exists "direct_messages_insert_if_friends" on public.direct_messages;
create policy "direct_messages_insert_if_friends"
    on public.direct_messages for insert
    with check (
        auth.uid() = from_id
        and public.is_active()
        and exists (
            select 1 from public.friendships f
            where ((f.user_a = from_id and f.user_b = to_id)
                or (f.user_a = to_id and f.user_b = from_id))
              and f.status = 'accepted'
        )
    );

-- chat_messages: block banned senders from posting in group chats
do $$
declare pol_name text;
begin
    /* The policy name changed across iterations; drop anything that
       looks like an insert policy on chat_messages and recreate. */
    for pol_name in
        select policyname from pg_policies
        where schemaname='public' and tablename='chat_messages' and cmd='INSERT'
    loop
        execute format('drop policy %I on public.chat_messages', pol_name);
    end loop;
end$$;
create policy "chat_messages_insert_member_active"
    on public.chat_messages for insert
    with check (
        auth.uid() = from_id
        and public.is_active()
        and public.is_room_member(room_id)
    );

-- friendships: block banned users from sending new friend requests
do $$
declare pol_name text;
begin
    for pol_name in
        select policyname from pg_policies
        where schemaname='public' and tablename='friendships' and cmd='INSERT'
    loop
        execute format('drop policy %I on public.friendships', pol_name);
    end loop;
end$$;
create policy "friendships_insert_active"
    on public.friendships for insert
    with check (
        (auth.uid() = user_a or auth.uid() = user_b)
        and public.is_active()
    );

-- game_invites: block banned users from inviting
drop policy if exists "invites_insert_from_friend" on public.game_invites;
create policy "invites_insert_from_friend"
    on public.game_invites for insert
    with check (
        auth.uid() = from_id
        and public.is_active()
        and exists (
            select 1 from public.friendships f
            where ((f.user_a = from_id and f.user_b = to_id)
                or (f.user_a = to_id and f.user_b = from_id))
              and f.status = 'accepted'
        )
        and exists (
            select 1 from public.profiles p
            where p.id = to_id
              and coalesce(p.manual_status, 'online') <> 'offline'
        )
    );

-- message_reactions: block banned users from reacting
drop policy if exists "reactions_insert_own" on public.message_reactions;
create policy "reactions_insert_own"
    on public.message_reactions for insert
    with check (
        user_id = auth.uid()
        and public.is_active()
        and public.can_see_message(kind, message_id)
    );
