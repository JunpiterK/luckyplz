-- =====================================================================
-- Lucky Please — Auth Security one-shot redeploy
-- =====================================================================
-- Bundles the three auth-security migrations (#2 nickname cooldown,
-- #3 disposable email blocklist, #4 consent + GDPR export) into a
-- single paste-and-run script for the Supabase SQL Editor.
--
-- USAGE:
--   1. Open Supabase dashboard → SQL Editor → "+ New query"
--   2. Paste THIS ENTIRE FILE
--   3. Click Run (Ctrl+Enter)
--   4. Done. The final `notify pgrst, 'reload schema';` refreshes
--      PostgREST so the new RPCs become callable immediately.
--
-- IDEMPOTENCY:
--   Every section uses `create table if not exists`, `create or
--   replace function`, `drop policy if exists`, `add column if not
--   exists`, `on conflict do nothing` so re-running is safe — existing
--   rows / consents / nickname history are preserved, missing pieces
--   filled in.
--
-- WHAT THIS DOES (in order):
--   1. nickname_changes table + 30-day cooldown trigger + RPCs
--      (anti-impersonation, anti-squatting)
--   2. blocked_email_domains table seeded with ~150 disposable
--      services + is_email_domain_allowed() RPC + profiles trigger
--      (anti-bot signup, sock-puppet defense)
--   3. profiles consent columns + set_consent() + export_my_data()
--      RPCs (KISA marketing-consent split + GDPR data portability)
--
-- WHAT THIS DOES NOT DO:
--   - Cloudflare Turnstile activation. That requires:
--     (a) Cloudflare dashboard → Turnstile → Add a site
--     (b) Paste SITE KEY into public/js/supabase-config.js
--     (c) Paste SECRET KEY into Supabase dashboard → Auth →
--         Captcha protection
--     See CLAUDE.md "Bot protection" for the full procedure.
--
-- AFTER RUNNING:
--   - New signups will see the 3-checkbox consent block + (if you
--     enabled Turnstile separately) a managed-difficulty challenge.
--   - Existing users: nickname is unchanged but a 30-day cooldown
--     starts from any future change. Marketing consent = NULL until
--     they toggle it on /me/. They can download their data right
--     away via the new "내 데이터 다운로드" button on /me/.
-- =====================================================================

-- ====================================================================
-- 2026-04-30-nickname-cooldown.sql
-- ====================================================================
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

-- ====================================================================
-- 2026-04-30-disposable-email-blocklist.sql
-- ====================================================================
    domain   text primary key,           -- lowercase, no @, no leading dot
    added_at timestamptz not null default now(),
    note     text                         -- optional why-blocked annotation
);

alter table public.blocked_email_domains enable row level security;

/* Public read so the is_email_domain_allowed RPC works for anon. The
   list itself isn't sensitive — anyone can guess that 10minutemail.com
   is on it. */
drop policy if exists "blocked_email_domains_select_all" on public.blocked_email_domains;
create policy "blocked_email_domains_select_all"
    on public.blocked_email_domains for select using (true);

/* Only super_admin can mutate. Regular users / authenticated have NO
   write access — blocklist is curated. */
drop policy if exists "blocked_email_domains_admin_write" on public.blocked_email_domains;
create policy "blocked_email_domains_admin_write"
    on public.blocked_email_domains for all
    using (
        exists (select 1 from public.profiles
                where id = auth.uid() and role = 'super_admin')
    )
    with check (
        exists (select 1 from public.profiles
                where id = auth.uid() and role = 'super_admin')
    );

-- ---- Seed list (~150 most-active disposable services as of 2026-04) ---
insert into public.blocked_email_domains (domain) values
    ('10minutemail.com'),('10minutemail.net'),('10minutemail.org'),
    ('20minutemail.com'),('30minutemail.com'),
    ('discard.email'),('discardmail.com'),('discardmail.de'),
    ('dispostable.com'),
    ('emailondeck.com'),('email-fake.com'),('email-temp.com'),('emailtemp.com'),
    ('fake-mail.fr'),('fake-mail.net'),('fakeinbox.com'),('fakemailgenerator.com'),
    ('fakemail.fr'),
    ('getairmail.com'),('getnada.com'),('grr.la'),
    ('guerrillamail.biz'),('guerrillamail.com'),('guerrillamail.de'),
    ('guerrillamail.info'),('guerrillamail.net'),('guerrillamail.org'),
    ('guerrillamailblock.com'),
    ('h.mintemail.com'),('harakirimail.com'),('hidemail.de'),
    ('inboxalias.com'),('inboxbear.com'),('incognitomail.com'),
    ('jetable.com'),('jetable.fr.nf'),('jetable.net'),('jetable.org'),
    ('koszmail.pl'),('kurzepost.de'),
    ('linshiyou.cn'),('lortemail.dk'),
    ('maildrop.cc'),('mailcatch.com'),('mailexpire.com'),
    ('mailfa.tk'),('mailforspam.com'),('mailimate.com'),
    ('mailin8r.com'),('mailinator.com'),('mailinator.net'),('mailinator.org'),
    ('mailinator2.com'),('mailmetrash.com'),('mailmoat.com'),
    ('mailnesia.com'),('mailnull.com'),
    ('mailshell.com'),('mailtemp.info'),('mailtothis.com'),
    ('mailtrash.net'),('mailzilla.com'),('mailzilla.org'),
    ('mbx.cc'),('mintemail.com'),('moakt.com'),
    ('mt2009.com'),('mt2014.com'),('mt2015.com'),('mt2016.com'),
    ('mytrashmail.com'),
    ('nada.ltd'),('nepwk.com'),('nervmich.net'),('nervtmich.net'),
    ('no-spam.ws'),('noclickemail.com'),('nogmailspam.info'),
    ('nomail2me.com'),('notmailinator.com'),
    ('onewaymail.com'),('online.ms'),('owlpic.com'),
    ('pancakemail.com'),('pjjkp.com'),('plexolan.de'),
    ('pokemail.net'),('poofy.org'),('pookmail.com'),
    ('proxymail.eu'),('prtnx.com'),
    ('quickinbox.com'),
    ('rcpt.at'),('rejectmail.com'),('reliable-mail.com'),('rmqkr.net'),
    ('rppkn.com'),('rtrtr.com'),
    ('s0ny.net'),('safe-mail.net'),('safersignup.de'),('safetymail.info'),
    ('safetypost.de'),('sandelf.de'),
    ('schafmail.de'),('schrott-email.de'),('secretemail.de'),
    ('sendspamhere.com'),('sharklasers.com'),('shieldedmail.com'),
    ('shiftmail.com'),('shitmail.me'),('shmeriously.com'),
    ('sinnlos-mail.de'),('slaskpost.se'),('smashmail.de'),
    ('snkmail.com'),('sofort-mail.de'),
    ('spam4.me'),('spamavert.com'),('spambog.com'),('spambog.de'),('spambog.ru'),
    ('spambox.us'),('spamcero.com'),('spamcorptastic.com'),
    ('spamday.com'),('spamfree24.com'),('spamfree24.de'),
    ('spamfree24.eu'),('spamfree24.info'),('spamfree24.net'),('spamfree24.org'),
    ('spamgourmet.com'),('spamgourmet.net'),('spamgourmet.org'),
    ('spamherelots.com'),('spamhereplease.com'),('spamify.com'),
    ('spaml.com'),('spaml.de'),('spammotel.com'),('spamobox.com'),
    ('superrito.com'),('suremail.info'),
    ('talkinator.com'),('tempail.com'),('temp-mail.com'),('temp-mail.net'),
    ('temp-mail.org'),('temp-mail.ru'),('tempemail.biz'),('tempemail.com'),
    ('tempemail.net'),('tempinbox.co.uk'),('tempinbox.com'),
    ('tempmail.eu'),('tempmail.it'),('tempmaildemand.com'),
    ('tempmailer.com'),('tempmailer.de'),('tempomail.fr'),
    ('temporamail.com'),('temporarily.de'),('temporaryemail.net'),
    ('temporaryforwarding.com'),('temporaryinbox.com'),
    ('throwawayemailaddresses.com'),('throwam.com'),('throwawaymail.com'),
    ('thanksnospam.info'),
    ('trash-mail.at'),('trash-mail.com'),('trash-mail.de'),
    ('trashmail.at'),('trashmail.com'),('trashmail.de'),('trashmail.me'),
    ('trashmail.net'),('trashmail.org'),('trashmail.ws'),
    ('trashmailer.com'),('trashymail.com'),('trashymail.net'),
    ('twinmail.de'),
    ('uggsrock.com'),
    ('venompen.com'),('vidchart.com'),('viditag.com'),
    ('wegwerfemail.com'),('wegwerfemail.de'),('wegwerfmail.de'),
    ('wegwerfmail.info'),('wegwerfmail.net'),('wegwerfmail.org'),
    ('whyspam.me'),
    ('xagloo.com'),('xemaps.com'),('xents.com'),('xoxy.net'),
    ('yep.it'),('yopmail.com'),('yopmail.fr'),('yopmail.net'),
    ('zippymail.info'),('zoaxe.com'),('zomg.info')
on conflict (domain) do nothing;


-- ---- RPC: client check before signUp() -------------------------------
create or replace function public.is_email_domain_allowed(p_email text)
returns boolean
language plpgsql security definer
set search_path = public
as $$
declare d text;
begin
    if p_email is null or position('@' in p_email) = 0 then
        return false;
    end if;
    d := lower(trim(split_part(p_email, '@', 2)));
    if d = '' then return false; end if;
    /* If domain is on the blocklist → not allowed. */
    if exists (select 1 from public.blocked_email_domains
               where blocked_email_domains.domain = d) then
        return false;
    end if;
    return true;
end;
$$;
grant execute on function public.is_email_domain_allowed(text) to authenticated, anon;


-- ---- BEFORE INSERT/UPDATE trigger on profiles (defense in depth) -----
/* If a malicious client bypasses the JS RPC check and creates an
   auth.users row directly via the Supabase API, this trigger still
   blocks them from creating a profile — and without a profile, they
   can't write game records, send messages, or use any social feature.
   Effectively neutralises the disposable account.

   The trigger only enforces on profile email — it doesn't look at
   auth.users.email (which we can't trigger on without owner perms).
   But profile email is the canonical email for our app's purposes,
   so this is the right enforcement point. */
create or replace function public._profile_check_email_domain()
returns trigger
language plpgsql security definer
set search_path = public
as $$
declare d text;
begin
    if new.email is null or new.email = '' then return new; end if;
    if position('@' in new.email) = 0 then return new; end if;
    d := lower(trim(split_part(new.email, '@', 2)));
    if d = '' then return new; end if;
    if exists (select 1 from public.blocked_email_domains
               where blocked_email_domains.domain = d) then
        raise exception 'email_domain_blocked: %', d;
    end if;
    return new;
end;
$$;

drop trigger if exists profile_check_email_domain on public.profiles;
create trigger profile_check_email_domain
    before insert or update on public.profiles
    for each row execute function public._profile_check_email_domain();


-- Force PostgREST to refresh its schema cache so is_email_domain_allowed
-- becomes callable immediately.
notify pgrst, 'reload schema';

-- ====================================================================
-- 2026-04-30-consent-and-export.sql
-- ====================================================================
comment on column public.profiles.privacy_agreed_at    is '개인정보처리방침 동의 시점 (필수)';
comment on column public.profiles.marketing_agreed_at  is '마케팅·이벤트 정보 수신 동의 시점 (선택, NULL=미동의/철회)';


-- ---- RPC: set_consent ------------------------------------------------
/* Called from the signup-completion / profile-edit flow to record or
   update the user's three consent flags. Terms + privacy are sticky
   once true (you can't withdraw without deleting the account); marketing
   is freely toggleable. The function only touches the calling user's
   own row — no admin override path. */
create or replace function public.set_consent(
    p_terms     boolean,
    p_privacy   boolean,
    p_marketing boolean
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if me is null then raise exception 'not_authenticated'; end if;

    update public.profiles set
        /* Terms + privacy are append-only after first true. Setting
           them false here is a no-op (stays NULL or stays the existing
           timestamp). The only way to clear them is to delete the
           account, which is the legally-correct semantics. */
        terms_agreed_at = case
            when p_terms and terms_agreed_at is null then now()
            else terms_agreed_at end,
        privacy_agreed_at = case
            when p_privacy and privacy_agreed_at is null then now()
            else privacy_agreed_at end,
        /* Marketing toggles freely. true → now(), false → NULL (clear).
           A subsequent true → fresh timestamp (per KISA, each new
           consent should be re-dated). */
        marketing_agreed_at = case
            when p_marketing then now()
            else null end
    where id = me;

    return jsonb_build_object(
        'ok', true,
        'terms_agreed_at',     (select terms_agreed_at     from public.profiles where id = me),
        'privacy_agreed_at',   (select privacy_agreed_at   from public.profiles where id = me),
        'marketing_agreed_at', (select marketing_agreed_at from public.profiles where id = me)
    );
end;
$$;
grant execute on function public.set_consent(boolean, boolean, boolean) to authenticated;


-- ---- RPC: export_my_data --------------------------------------------
/* GDPR Art. 20 (data portability) — returns a JSONB blob with every
   table the calling user owns. Caller can save this to disk as a
   .json file. Other-user content (e.g. messages SENT TO this user by
   someone else) is intentionally excluded — that's the other party's
   data, not yours.

   Robustness: each per-table query is wrapped in EXISTS check via
   information_schema so a Supabase project that hasn't deployed all
   game migrations still gets a working export covering whatever IS
   deployed. Tables we don't own (auth.users, etc.) are out of scope. */
create or replace function public.export_my_data()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    result jsonb;
    -- Per-table buckets, default empty so missing tables yield [] not error.
    profile_row     jsonb := null;
    snake_attempts  jsonb := '[]'::jsonb;
    snake_records   jsonb := null;
    pacman_attempts jsonb := '[]'::jsonb;
    pacman_records  jsonb := null;
    burger_attempts jsonb := '[]'::jsonb;
    burger_records  jsonb := null;
    dodge_attempts  jsonb := '[]'::jsonb;
    dodge_records   jsonb := null;
    quiz_attempts   jsonb := '[]'::jsonb;
    quiz_questions  jsonb := '[]'::jsonb;
    nickname_hist   jsonb := '[]'::jsonb;
    friendships_rows jsonb := '[]'::jsonb;
    has_table       boolean;
begin
    if me is null then raise exception 'not_authenticated'; end if;

    -- Profile (always exists for any signed-in user)
    select to_jsonb(p) into profile_row from public.profiles p where p.id = me;

    -- Snake
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='snake_attempts')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at), ''[]''::jsonb)
                   from public.snake_attempts s where s.user_id = $1'
            using me into snake_attempts;
        execute 'select to_jsonb(s) from public.snake_records s where s.user_id = $1'
            using me into snake_records;
    end if;

    -- Pacman
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='pacman_attempts')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at), ''[]''::jsonb)
                   from public.pacman_attempts s where s.user_id = $1'
            using me into pacman_attempts;
        execute 'select to_jsonb(s) from public.pacman_records s where s.user_id = $1'
            using me into pacman_records;
    end if;

    -- Burger
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='burger_attempts')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at), ''[]''::jsonb)
                   from public.burger_attempts s where s.user_id = $1'
            using me into burger_attempts;
        execute 'select to_jsonb(s) from public.burger_records s where s.user_id = $1'
            using me into burger_records;
    end if;

    -- Dodge / Space-Z
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='dodge_attempts')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at), ''[]''::jsonb)
                   from public.dodge_attempts s where s.user_id = $1'
            using me into dodge_attempts;
        execute 'select to_jsonb(s) from public.dodge_records s where s.user_id = $1'
            using me into dodge_records;
    end if;

    -- Quiz
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='quiz_attempts')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at), ''[]''::jsonb)
                   from public.quiz_attempts s where s.user_id = $1'
            using me into quiz_attempts;
    end if;
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='quiz_user_questions')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.created_at), ''[]''::jsonb)
                   from public.quiz_user_questions s where s.user_id = $1'
            using me into quiz_questions;
    end if;

    -- Nickname history (from #2 cooldown migration)
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='nickname_changes')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s) order by s.changed_at), ''[]''::jsonb)
                   from public.nickname_changes s where s.user_id = $1'
            using me into nickname_hist;
    end if;

    -- Friendships
    select exists (select 1 from information_schema.tables
                   where table_schema='public' and table_name='friendships')
      into has_table;
    if has_table then
        execute 'select coalesce(jsonb_agg(to_jsonb(s)), ''[]''::jsonb)
                   from public.friendships s where s.user_a = $1 or s.user_b = $1'
            using me into friendships_rows;
    end if;

    result := jsonb_build_object(
        'export_version', '1.0',
        'exported_at',    now(),
        'user_id',        me,
        'profile',        profile_row,
        'snake_attempts', snake_attempts,
        'snake_records',  snake_records,
        'pacman_attempts', pacman_attempts,
        'pacman_records', pacman_records,
        'burger_attempts', burger_attempts,
        'burger_records', burger_records,
        'dodge_attempts', dodge_attempts,
        'dodge_records',  dodge_records,
        'quiz_attempts',  quiz_attempts,
        'quiz_user_questions', quiz_questions,
        'nickname_changes', nickname_hist,
        'friendships',    friendships_rows
    );
    return result;
end;
$$;
grant execute on function public.export_my_data() to authenticated;

-- Refresh PostgREST cache so new RPCs are immediately callable.
notify pgrst, 'reload schema';

-- ====================================================================
-- Final: refresh PostgREST schema cache so all new RPCs are callable
-- ====================================================================
notify pgrst, 'reload schema';
