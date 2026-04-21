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
    if inv.status <> 'pending' then raise exception 'already_'||inv.status; end if;
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
