-- =====================================================================
-- Migration: Nickname change cooldown + history (anti-impersonation)
-- Date:      2026-04-30
-- Purpose:   Prevent nickname-squatting / impersonation attacks where a
--            user rapidly cycles through high-profile names. Industry
--            norms: Twitch 60 days, Discord ~14 days, Naver permanent.
--            We pick 30 days as a balance — long enough to deter abuse,
--            short enough that a legitimate rename isn't punishing.
--
-- Schema:
--   - public.nickname_changes — append-only history of every successful
--     nickname change, scoped per user_id. Admin can audit; users see
--     only their own.
--   - public._profile_nickname_cooldown() — BEFORE UPDATE trigger on
--     profiles that:
--       (a) detects a nickname change (NEW.nickname IS DISTINCT FROM OLD)
--       (b) blocks if the user changed within the last 30 days (raise
--           exception with code 'nickname_cooldown:<remaining_sec>' so
--           the UI can parse and show countdown)
--       (c) allows + appends to nickname_changes on success
--       (d) bypassed for super_admin (recovery / moderation cases)
--   - public.nickname_cooldown_remaining() — RPC returning seconds
--     remaining (0 if no cooldown active). Lets the /me/ page disable
--     the nickname input and show a countdown WITHOUT triggering the
--     full save flow.
--
-- Note on backfill:
--   Existing users have an empty nickname_changes history, so their
--   FIRST change after this migration runs without cooldown — desired
--   behaviour (we don't want to punish them for legacy state). The
--   first change records OLD → NEW, after which the cooldown kicks in.
-- =====================================================================

-- ---- History table ---------------------------------------------------
create table if not exists public.nickname_changes (
    id            bigserial   primary key,
    user_id       uuid        not null references auth.users(id) on delete cascade,
    old_nickname  text        not null,
    new_nickname  text        not null,
    changed_at    timestamptz not null default now()
);

create index if not exists nickname_changes_user_idx
    on public.nickname_changes (user_id, changed_at desc);

alter table public.nickname_changes enable row level security;

drop policy if exists "nickname_changes_select_own" on public.nickname_changes;
create policy "nickname_changes_select_own"
    on public.nickname_changes for select
    using (auth.uid() = user_id);

/* Admin policy: super_admin can read everyone's history (moderation /
   sock-puppet investigation). Regular users are restricted to their
   own row by the policy above. */
drop policy if exists "nickname_changes_select_admin" on public.nickname_changes;
create policy "nickname_changes_select_admin"
    on public.nickname_changes for select
    using (
        exists (
            select 1 from public.profiles
            where id = auth.uid() and role in ('admin','super_admin')
        )
    );

/* INSERTs are made by the trigger function (security definer), so RLS
   has no effect there. Explicit policy denies any direct client INSERT
   to be safe — clients should never write to this table directly. */
drop policy if exists "nickname_changes_no_direct_insert" on public.nickname_changes;
create policy "nickname_changes_no_direct_insert"
    on public.nickname_changes for insert
    with check (false);


-- ---- BEFORE UPDATE trigger on profiles -------------------------------
create or replace function public._profile_nickname_cooldown()
returns trigger
language plpgsql security definer
set search_path = public
as $$
declare
    last_change   timestamptz;
    cooldown_days int := 30;
    remaining_sec int;
    is_admin      boolean;
begin
    /* Only act on actual nickname mutations during UPDATE — INSERT (first
       profile creation) and unchanged updates pass through. */
    if TG_OP = 'UPDATE' and NEW.nickname IS DISTINCT FROM OLD.nickname then
        /* super_admin bypass — useful for moderation actions where an
           admin needs to clear a banned/abusive nickname immediately
           without waiting 30 days. Regular admins still face the
           cooldown to keep their own audit trail honest. */
        select (role = 'super_admin') into is_admin
          from public.profiles where id = auth.uid();

        if not coalesce(is_admin, false) then
            select max(changed_at) into last_change
              from public.nickname_changes
             where user_id = NEW.id;

            if last_change is not null
               and (now() - last_change) < (cooldown_days || ' days')::interval then
                remaining_sec := extract(epoch from (
                    last_change + (cooldown_days || ' days')::interval - now()
                ))::int;
                /* Encode remaining seconds in the exception MESSAGE so
                   the UI can parse + show "다음 변경: X일 후" countdown.
                   PostgREST surfaces the message verbatim. */
                raise exception 'nickname_cooldown:%', remaining_sec;
            end if;
        end if;

        /* Allowed — append to history. The new row reflects the change
           that's about to happen on the profiles table (BEFORE trigger). */
        insert into public.nickname_changes (user_id, old_nickname, new_nickname)
        values (NEW.id, OLD.nickname, NEW.nickname);
    end if;
    return NEW;
end;
$$;

drop trigger if exists profile_nickname_cooldown on public.profiles;
create trigger profile_nickname_cooldown
    before update on public.profiles
    for each row execute function public._profile_nickname_cooldown();


-- ---- RPC: ask how many seconds remain in the current cooldown --------
create or replace function public.nickname_cooldown_remaining()
returns int
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    last_change   timestamptz;
    cooldown_days int := 30;
    remaining_sec int;
begin
    if me is null then return 0; end if;
    select max(changed_at) into last_change
      from public.nickname_changes
     where user_id = me;
    if last_change is null then return 0; end if;
    remaining_sec := extract(epoch from (
        last_change + (cooldown_days || ' days')::interval - now()
    ))::int;
    return greatest(0, remaining_sec);
end;
$$;
grant execute on function public.nickname_cooldown_remaining() to authenticated;


-- ---- RPC: list my nickname history (for /me/ "변경 이력" button) -----
create or replace function public.my_nickname_history(p_limit int default 20)
returns table (
    old_nickname text,
    new_nickname text,
    changed_at   timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if me is null then return; end if;
    return query
        select h.old_nickname, h.new_nickname, h.changed_at
          from public.nickname_changes h
         where h.user_id = me
         order by h.changed_at desc
         limit greatest(1, least(p_limit, 100));
end;
$$;
grant execute on function public.my_nickname_history(int) to authenticated;

-- Force PostgREST to refresh its schema cache so the new RPCs become
-- callable immediately.
notify pgrst, 'reload schema';
