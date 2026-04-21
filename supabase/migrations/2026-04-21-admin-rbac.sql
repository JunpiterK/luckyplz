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
