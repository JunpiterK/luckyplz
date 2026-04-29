-- =====================================================================
-- Migration: Disposable / temporary email domain blocklist
-- Date:      2026-04-30
-- Purpose:   Block signups from throwaway-email services (Mailinator,
--            10minutemail, guerrilla-mail, etc). These accounts are the
--            primary vehicle for: (a) gaming the AdSense impressions
--            with bots, (b) creating sock-puppets to vote-manipulate
--            game leaderboards, (c) skirting per-account rate limits.
--
-- Architecture:
--   1. public.blocked_email_domains — append-only blocklist seeded
--      with ~150 of the most active disposable services. Admin can
--      INSERT new rows via SQL Editor as new services emerge.
--   2. public.is_email_domain_allowed(email) — boolean RPC the auth
--      page calls BEFORE signUp() to give immediate "이 이메일은
--      사용할 수 없어요" feedback. Idempotent + fast (single index
--      lookup).
--   3. BEFORE INSERT/UPDATE trigger on public.profiles — defense in
--      depth. If a malicious client bypasses the JS check and signs
--      up directly via the Supabase API, the trigger blocks them
--      from creating a profile (and thus from saving any game
--      record). auth.users may still get created, but without a
--      profile, they're effectively neutered.
--
-- Maintenance:
--   The blocklist evolves — new disposable services launch monthly.
--   Admin should periodically:
--     - Check public lists like https://github.com/disposable-email-domains/
--       and merge new entries via INSERT … ON CONFLICT DO NOTHING.
--     - Audit blocked attempts via the `note` column for false positives.
-- =====================================================================

create table if not exists public.blocked_email_domains (
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
