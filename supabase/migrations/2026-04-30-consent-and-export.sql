-- =====================================================================
-- Migration: KISA marketing consent split + GDPR-style data export
-- Date:      2026-04-30
-- Purpose:   Two compliance items rolled together:
--
--   (A) Korean 정통망법 50조 — marketing emails require SEPARATE consent
--       from terms-of-service / privacy-policy agreement. Cannot be
--       bundled into a single "I agree to everything" checkbox. We
--       record terms_agreed_at, privacy_agreed_at, and
--       marketing_agreed_at as distinct timestamps so an audit (or
--       KISA inspection) can prove which the user explicitly agreed
--       to and when.
--
--   (B) GDPR Art. 15 + 20 (right of access + portability) — user can
--       request a machine-readable copy of all their personal data.
--       Korean 개인정보보호법 follows the same shape. Implemented as
--       export_my_data() RPC returning JSONB with profile, game
--       records, nickname history, friendships, etc. The /me/ page
--       wires a "내 데이터 다운로드" button that calls this and saves
--       the response as a .json file.
--
-- Schema additions:
--   profiles.terms_agreed_at      timestamptz NULL — when ToS was accepted
--   profiles.privacy_agreed_at    timestamptz NULL — when privacy policy accepted
--   profiles.marketing_agreed_at  timestamptz NULL — set when user opts in,
--                                  CLEARED to NULL when they opt out (so the
--                                  "is currently consenting?" check is just
--                                  IS NOT NULL).
--
-- RPCs:
--   set_consent(p_terms, p_privacy, p_marketing) — toggle all three at once.
--     boolean true → set timestamp to now() (or preserve existing for terms/
--     privacy which are append-only after first agreement).
--     boolean false → clears the timestamp (only affects marketing —
--     terms/privacy can't be unagreed without account deletion).
--   export_my_data() — returns JSONB blob covering every table that
--     references the calling user_id. Uses information_schema to skip
--     tables that don't exist on this Supabase instance (e.g. user
--     hasn't deployed all action-game migrations yet) so the export
--     works on partial deployments without errors.
-- =====================================================================

-- ---- Schema changes -------------------------------------------------
alter table public.profiles
    add column if not exists terms_agreed_at      timestamptz,
    add column if not exists privacy_agreed_at    timestamptz,
    add column if not exists marketing_agreed_at  timestamptz;

create index if not exists profiles_marketing_agreed_idx
    on public.profiles (marketing_agreed_at)
    where marketing_agreed_at is not null;

comment on column public.profiles.terms_agreed_at      is '이용약관 동의 시점 (필수)';
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
