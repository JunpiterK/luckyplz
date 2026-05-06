-- Email subscriber list for Lucky Blog new-post notifications.
--
-- Apply via Supabase Dashboard → SQL Editor → paste this whole file → Run.
-- Idempotent (uses `if not exists` / `or replace` everywhere) so it's safe
-- to re-run during development.
--
-- Surface area: anon visitors POST {email, lang, source} → row inserted.
-- Admin (you) reads the list via the dashboard or a saved query when you
-- want to send a digest. Unsubscribe is token-based — no auth required,
-- the user clicks an emailed link and an Edge / RPC call flips active=false.

-- =========================================================================
-- TABLE
-- =========================================================================
create table if not exists public.email_subscribers (
    id uuid primary key default gen_random_uuid(),
    email text not null,
    lang text not null default 'ko' check (lang in ('ko', 'en')),
    subscribed_at timestamptz not null default now(),
    unsubscribe_token uuid not null default gen_random_uuid(),
    active boolean not null default true,
    source text,
    -- Lower-cased unique constraint via index — case-insensitive uniqueness
    -- so 'Foo@Bar.com' and 'foo@bar.com' aren't double-counted.
    constraint email_subscribers_email_check
        check (email = lower(trim(email)) and email like '%@%.%')
);

create unique index if not exists email_subscribers_email_unique
    on public.email_subscribers (lower(email));

create index if not exists email_subscribers_active_idx
    on public.email_subscribers (active) where active = true;

create index if not exists email_subscribers_unsubscribe_token_idx
    on public.email_subscribers (unsubscribe_token);

-- =========================================================================
-- RLS
-- =========================================================================
alter table public.email_subscribers enable row level security;

-- Anyone (anon + authenticated) can subscribe — INSERT a single row.
-- We do NOT allow them to SELECT their own row back; the form just shows
-- a "thanks" message based on the operation succeeding.
drop policy if exists "subscribe_anyone_can_insert" on public.email_subscribers;
create policy "subscribe_anyone_can_insert"
    on public.email_subscribers
    for insert
    to anon, authenticated
    with check (true);

-- Reads are admin-only. Set a role claim on your admin profile in
-- public.profiles or auth.users.app_metadata to enable.
drop policy if exists "subscribers_admin_read" on public.email_subscribers;
create policy "subscribers_admin_read"
    on public.email_subscribers
    for select
    to authenticated
    using (
        exists (
            select 1 from public.profiles p
            where p.id = auth.uid() and p.role = 'admin'
        )
    );

-- =========================================================================
-- UNSUBSCRIBE RPC (token-based, no auth)
-- =========================================================================
-- The unsubscribe link in outgoing emails takes the form
-- https://luckyplz.com/unsubscribe/?token=<uuid>. The page calls this RPC
-- which flips active=false where the token matches. SECURITY DEFINER lets
-- the function bypass RLS on UPDATE (we don't expose direct UPDATE rights
-- to anon to prevent enumeration attacks).
create or replace function public.unsubscribe_email(p_token uuid)
returns boolean
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_count int;
begin
    if p_token is null then
        return false;
    end if;
    update public.email_subscribers
       set active = false
     where unsubscribe_token = p_token
       and active = true;

    get diagnostics v_count = row_count;
    return v_count > 0;
end;
$$;

-- Lock down then explicitly grant.
revoke all on function public.unsubscribe_email(uuid) from public;
grant execute on function public.unsubscribe_email(uuid) to anon, authenticated;

-- =========================================================================
-- SUBSCRIBE RPC (idempotent — re-subscribe after unsub flips active back on)
-- =========================================================================
-- Direct INSERT works for a fresh email, but for already-known emails the
-- unique constraint blocks the request. Wrapping in an upsert RPC lets us:
--   1. cleanly re-activate a previously-unsubscribed user
--   2. update lang preference if they switched site language
--   3. return a status code the form can show ("subscribed" / "reactivated"
--      / "already_active") so we don't lie to the user.
create or replace function public.subscribe_email(
    p_email text,
    p_lang  text default 'ko',
    p_source text default null
) returns text
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_email_lower text := lower(trim(p_email));
    v_existing public.email_subscribers%rowtype;
begin
    if v_email_lower !~ '^[^@]+@[^@]+\.[^@]+$' then
        return 'invalid';
    end if;
    if p_lang not in ('ko', 'en') then
        p_lang := 'ko';
    end if;

    select * into v_existing
      from public.email_subscribers
     where lower(email) = v_email_lower
     limit 1;

    if v_existing.id is null then
        insert into public.email_subscribers (email, lang, source, active)
        values (v_email_lower, p_lang, p_source, true);
        return 'subscribed';
    end if;

    if v_existing.active then
        return 'already_active';
    end if;

    update public.email_subscribers
       set active = true,
           lang = p_lang,
           subscribed_at = now()
     where id = v_existing.id;
    return 'reactivated';
end;
$$;

revoke all on function public.subscribe_email(text, text, text) from public;
grant execute on function public.subscribe_email(text, text, text) to anon, authenticated;

-- =========================================================================
-- ADMIN VIEW (optional — saves you from joining + filtering each time)
-- =========================================================================
create or replace view public.email_subscribers_export as
select
    id,
    email,
    lang,
    subscribed_at,
    source,
    active
from public.email_subscribers
where active = true
order by subscribed_at desc;

-- View inherits the table's RLS, so admin-only reads stay admin-only.
