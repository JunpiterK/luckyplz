-- =====================================================================
-- Migration: 30-minute TTL on unverified email signups
-- Date:      2026-04-30
-- Purpose:   When a user clicks "Sign Up" but never confirms their
--            email, their auth.users + profiles + any cascaded rows
--            sit in the database forever. This migration cleans them
--            up automatically every 5 minutes via pg_cron.
--
-- Why we need this:
--   1. Privacy / KISA compliance — KISA 개인정보보호법 §29 "처리목적
--      달성 후 지체 없이 파기". An unverified signup never produced a
--      consenting user, so storing their email + IP indefinitely
--      violates the spirit of that requirement.
--   2. Squat prevention — without TTL, a malicious actor could
--      register lucky_admin@somewhere.com, never verify, and lock
--      that nickname/email out of the system forever.
--   3. Hygiene — bots that probe signup pages create thousands of
--      zombie auth.users rows that never become real users.
--
-- How it works:
--   • pg_cron schedules `delete_unverified_signups()` to run every
--     5 minutes (Supabase enables pg_cron on all plans).
--   • The function deletes auth.users rows where:
--       - email_confirmed_at IS NULL  (still unverified)
--       - created_at < now() - 30 minutes  (waited the full window)
--   • OAuth users (Google/Kakao) auto-pass email_confirmed_at on
--     creation, so they never match this filter — safe.
--   • The auth.users delete cascades to public.profiles via the FK
--     `profiles.id REFERENCES auth.users(id) ON DELETE CASCADE`,
--     and from profiles to every other table that FKs user_id with
--     CASCADE (game records, friendships, messages, nickname_changes,
--     etc).
--
-- Worst-case timing:
--   User signs up at T=0, never clicks the email.
--   Next cron tick at T<5min. Won't match (created_at > now()-30m).
--   Cron tick at T=30m+ε. Matches. Deleted within 5 minutes max.
--   So actual deletion lands between 30 and 35 minutes after signup.
--
-- Recovery:
--   If the user comes back at T=20min and clicks the verification
--   link, email_confirmed_at gets set, they no longer match the
--   cleanup filter. Safe.
--
-- Operator notes:
--   • To pause the job:    select cron.unschedule('delete-unverified-signups');
--   • To resume:           re-run this migration (idempotent).
--   • To check status:     select * from cron.job where jobname='delete-unverified-signups';
--   • To see recent runs:  select * from cron.job_run_details
--                              where jobid = (select jobid from cron.job
--                                             where jobname='delete-unverified-signups')
--                              order by start_time desc limit 20;
--   • To run on demand:    select public.delete_unverified_signups();
-- =====================================================================

-- ---- pg_cron extension (idempotent) ---------------------------------
-- Supabase's standard `extensions` schema is the conventional location
-- for pg_cron. If this fails with "permission denied" the project's
-- pg_cron isn't enabled — go to Dashboard → Database → Extensions and
-- toggle pg_cron ON, then re-run.
create extension if not exists pg_cron with schema extensions;


-- ---- Function: delete unverified signups older than 30 minutes ------
/* Returns the number of rows actually deleted so the cron job log
   shows useful diagnostic info ("removed N rows"). Wrapped in
   security definer because auth.users belongs to supabase_auth_admin
   and only the postgres-owned function can DELETE there.

   The query uses simple AND clauses so the planner can use the
   default btree index on auth.users(created_at) to scan only rows
   in the cleanup window — no full table scan even with millions
   of users. */
create or replace function public.delete_unverified_signups()
returns int
language plpgsql
security definer
set search_path = public, auth, extensions
as $$
declare
    cnt int;
begin
    delete from auth.users u
    where u.email_confirmed_at is null
      and u.email is not null
      and u.email <> ''
      and u.created_at < now() - interval '30 minutes';

    get diagnostics cnt = row_count;

    if cnt > 0 then
        raise notice '[delete_unverified_signups] removed % unverified signup row(s) older than 30 minutes', cnt;
    end if;

    return cnt;
end;
$$;

/* Only the service_role (Supabase's privileged backend role) and
   postgres can call this function. Anon/authenticated users CANNOT
   trigger arbitrary cleanups — they'd have to wait for cron. */
revoke all on function public.delete_unverified_signups() from public, anon, authenticated;
grant execute on function public.delete_unverified_signups() to service_role;


-- ---- Schedule: every 5 minutes --------------------------------------
/* cron.schedule() upserts by job name — calling it again with the
   same name updates the existing schedule rather than creating a
   duplicate. Safe to re-run this migration any number of times.

   Cron expression: */5 * * * *  →  every 5 minutes on the minute
   (00:00, 00:05, 00:10, ...). pg_cron's UTC schedule is fine here —
   we don't care about wall-clock alignment, just the 5-minute cadence. */
select cron.schedule(
    'delete-unverified-signups',
    '*/5 * * * *',
    $cron$select public.delete_unverified_signups();$cron$
);


-- ---- PostgREST cache refresh ----------------------------------------
/* Even though delete_unverified_signups isn't directly exposed to
   the REST API (no client should call it), the schema cache needs
   refresh so any future inspection by the dashboard sees the
   function. */
notify pgrst, 'reload schema';
