-- =====================================================================
-- Migration: Per-thread mute + group chat kick (Phase G)
-- Date:      2026-04-22
-- Purpose:
--   1. thread_mutes table — per-user list of DMs / group rooms the
--      user has silenced. Messages still arrive via Realtime and the
--      inbox badge still counts them; only OS / in-page notifications
--      (LpNotify) consult this list before firing.
--   2. kick_group_chat_member(room, target) RPC — lets a group chat
--      owner remove another member (matches Slack "Remove from
--      channel" / Discord "Kick member" conventions).
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. thread_mutes
-- ---------------------------------------------------------------------
-- We use a flat (user_id, kind, key) composite PK instead of one row
-- per thread per side, because the inverse (I silenced friend X)
-- shouldn't reveal anything to X. RLS locks reads + writes to the
-- owner.
create table if not exists public.thread_mutes (
    user_id     uuid        not null references auth.users(id) on delete cascade,
    kind        text        not null check (kind in ('dm','group')),
    thread_key  text        not null check (char_length(thread_key) between 1 and 80),
    muted_at    timestamptz not null default now(),
    primary key (user_id, kind, thread_key)
);

create index if not exists thread_mutes_user_idx on public.thread_mutes (user_id);

alter table public.thread_mutes enable row level security;

drop policy if exists "thread_mutes_select_own" on public.thread_mutes;
drop policy if exists "thread_mutes_insert_own" on public.thread_mutes;
drop policy if exists "thread_mutes_delete_own" on public.thread_mutes;

create policy "thread_mutes_select_own"
    on public.thread_mutes for select
    using (user_id = auth.uid());

create policy "thread_mutes_insert_own"
    on public.thread_mutes for insert
    with check (user_id = auth.uid());

create policy "thread_mutes_delete_own"
    on public.thread_mutes for delete
    using (user_id = auth.uid());


-- ---------------------------------------------------------------------
-- 2. kick_group_chat_member — owner-only removal
-- ---------------------------------------------------------------------
-- We intentionally don't allow a regular admin role in a group chat to
-- kick (we haven't modelled admin distinct from owner yet). Only the
-- row whose chat_rooms.created_by matches auth.uid() can kick. The
-- creator cannot kick themselves via this RPC — to leave the group
-- they use the existing leave_group_chat RPC, which transfers
-- ownership to another member if any remain.
create or replace function public.kick_group_chat_member(
    p_room uuid, p_target uuid
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        room_creator uuid;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_target = me then raise exception 'cannot_kick_self'; end if;

    select created_by into room_creator
      from public.chat_rooms where id = p_room;
    if not found then raise exception 'room_not_found'; end if;
    if room_creator <> me then raise exception 'not_owner'; end if;

    /* Target must be a current member. If they aren't, surface a
       friendly error instead of silently no-op'ing so the UI can
       tell the owner why the button did nothing. */
    if not exists (
        select 1 from public.chat_members
        where room_id = p_room and user_id = p_target
    ) then
        raise exception 'not_a_member';
    end if;

    delete from public.chat_members
     where room_id = p_room and user_id = p_target;

    return jsonb_build_object('ok', true);
end;
$$;
grant execute on function public.kick_group_chat_member(uuid, uuid) to authenticated;
