-- =====================================================================
-- Migration: Quiz — "MyQuiz" user-submitted questions with 7-day TTL
-- Date:      2026-04-29
-- Purpose:   Logged-in users can author their own quiz questions and
--            include them in a quiz session via a new "myquiz" category.
--            Server-side persistence is capped at 7 days from creation
--            — after that, rows are filtered out of every fetch and the
--            cleanup function deletes them physically.
--
-- Design choices:
--   - SEPARATE table from public.quiz_questions, not a CHECK extension.
--     Rationale: user content is per-author (RLS), TTL'd, and capped per
--     user — properties that don't fit the curated bank's "global,
--     permanent, public" model. Mixing them would force user content
--     into the global RLS-public policy.
--   - Per-user cap: 200 active questions. Stops a single account from
--     filling the table; comfortably above any reasonable personal
--     question set (Kahoot equivalent ~10–50 per game).
--   - The existing quiz_random_questions RPC is extended to UNION-IN
--     the caller's own myquiz rows when 'myquiz' is in the category
--     filter. Mixed selection (e.g. kpop + myquiz) returns a unified
--     shuffle — same UX as any other category combo.
--   - Cleanup runs application-side via cleanup_expired_user_quizzes()
--     called whenever a user opens the MyQuiz manager. No pg_cron
--     dependency (Supabase pg_cron is paid-tier only).
-- =====================================================================

create table if not exists public.quiz_user_questions (
    id          bigserial   primary key,
    user_id     uuid        not null references auth.users(id) on delete cascade,
    question    text        not null check (length(question) between 4 and 400),
    options     jsonb       not null,                       -- exactly 4 strings
    correct     int         not null check (correct between 0 and 3),
    hint        text,                                       -- optional
    /* Per-user content language (defaults to author's UI locale).
       Lets a Korean user mark their question 'ko' so it shows up only
       when the running game is in Korean — matches the curated bank's
       per-language filtering. */
    language    text        not null default 'ko'
                            check (language in ('ko','en','ja','zh','es','de','fr','pt','ru','ar','hi','th','id','vi','tr','gb')),
    created_at  timestamptz not null default now(),
    expires_at  timestamptz not null default (now() + interval '7 days'),
    constraint quiz_user_options_shape check (
        jsonb_typeof(options) = 'array' and jsonb_array_length(options) = 4
    )
);
create index if not exists quiz_uq_user_idx    on public.quiz_user_questions (user_id, created_at desc);
create index if not exists quiz_uq_expires_idx on public.quiz_user_questions (expires_at);
create index if not exists quiz_uq_language_idx on public.quiz_user_questions (language);

-- RLS: every row is owned by exactly one user; reads/inserts/deletes
-- are scoped to that owner. The host doesn't get to see other people's
-- myquiz content even inside a multiplayer room.
alter table public.quiz_user_questions enable row level security;

drop policy if exists "quiz_uq_select_own" on public.quiz_user_questions;
create policy "quiz_uq_select_own"
    on public.quiz_user_questions for select
    using (auth.uid() = user_id);

drop policy if exists "quiz_uq_insert_own" on public.quiz_user_questions;
create policy "quiz_uq_insert_own"
    on public.quiz_user_questions for insert
    with check (auth.uid() = user_id);

drop policy if exists "quiz_uq_delete_own" on public.quiz_user_questions;
create policy "quiz_uq_delete_own"
    on public.quiz_user_questions for delete
    using (auth.uid() = user_id);

-- Caller is also the implied authenticator. Anonymous (no auth.uid()) gets nothing.
grant select, insert, delete on public.quiz_user_questions to authenticated;
grant usage, select on sequence public.quiz_user_questions_id_seq to authenticated;


-- =====================================================================
-- RPC: insert a user question
-- =====================================================================
create or replace function public.quiz_user_insert_question(
    p_question text,
    p_options  jsonb,
    p_correct  int,
    p_hint     text default null,
    p_language text default 'ko'
) returns bigint
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    new_id bigint;
    user_count int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if length(p_question) < 4 or length(p_question) > 400 then raise exception 'bad_question'; end if;
    if jsonb_typeof(p_options) != 'array' or jsonb_array_length(p_options) != 4 then
        raise exception 'bad_options';
    end if;
    if p_correct < 0 or p_correct > 3 then raise exception 'bad_correct'; end if;
    if p_language not in ('ko','en','ja','zh','es','de','fr','pt','ru','ar','hi','th','id','vi','tr','gb') then
        raise exception 'bad_language';
    end if;

    /* Per-user cap so a compromised account can't fill the table. */
    select count(*) into user_count
      from public.quiz_user_questions
     where user_id = me and expires_at > now();
    if user_count >= 200 then raise exception 'too_many_questions'; end if;

    insert into public.quiz_user_questions (user_id, question, options, correct, hint, language)
    values (me, p_question, p_options, p_correct, nullif(p_hint, ''), p_language)
    returning id into new_id;

    return new_id;
end;
$$;
grant execute on function public.quiz_user_insert_question(text, jsonb, int, text, text) to authenticated;


-- =====================================================================
-- RPC: list current user's questions (for management UI)
-- Returns rows sorted newest-first, only non-expired entries.
-- =====================================================================
create or replace function public.quiz_user_list_questions()
returns table (
    id          bigint,
    question    text,
    options     jsonb,
    correct     int,
    hint        text,
    language    text,
    created_at  timestamptz,
    expires_at  timestamptz
)
language sql security definer
set search_path = public
as $$
    select id, question, options, correct, hint, language, created_at, expires_at
      from public.quiz_user_questions
     where user_id = auth.uid()
       and expires_at > now()
     order by created_at desc;
$$;
grant execute on function public.quiz_user_list_questions() to authenticated;


-- =====================================================================
-- RPC: delete one of the caller's questions by id
-- Returns true if a row was actually removed (so the UI can show a
-- toast on race / stale id).
-- =====================================================================
create or replace function public.quiz_user_delete_question(p_id bigint)
returns boolean
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    deleted int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    delete from public.quiz_user_questions
     where id = p_id and user_id = me;
    get diagnostics deleted = row_count;
    return deleted > 0;
end;
$$;
grant execute on function public.quiz_user_delete_question(bigint) to authenticated;


-- =====================================================================
-- Cleanup: physically remove expired rows. Anyone authenticated can
-- run it (it only deletes already-invisible rows so no abuse vector).
-- The frontend calls this lazily when a user opens the MyQuiz manager.
-- =====================================================================
create or replace function public.cleanup_expired_user_quizzes()
returns int
language plpgsql security definer
set search_path = public
as $$
declare deleted_count int;
begin
    delete from public.quiz_user_questions where expires_at < now();
    get diagnostics deleted_count = row_count;
    return deleted_count;
end;
$$;
grant execute on function public.cleanup_expired_user_quizzes() to authenticated;


-- =====================================================================
-- Extend quiz_random_questions to fold in MyQuiz when 'myquiz' is in
-- the selected categories. Returns a unified shuffled set of curated
-- + user-owned questions.
--
-- Return type changes from `setof public.quiz_questions` to an
-- explicit table(...) shape because user-owned rows don't satisfy
-- the curated table's category CHECK ('myquiz' isn't in the whitelist
-- and we don't want it to be — see migration header rationale).
-- The client already reads named columns, so the shape change is
-- transparent.
-- =====================================================================
drop function if exists public.quiz_random_questions(text[], int, text);

create or replace function public.quiz_random_questions(
    p_categories text[] default null,
    p_count      int    default 10,
    p_language   text   default 'ko'
) returns table (
    id          bigint,
    category    text,
    era         text,
    difficulty  int,
    question    text,
    options     jsonb,
    correct     int,
    hint        text,
    source      text,
    created_at  timestamptz,
    language    text
)
language plpgsql security definer
set search_path = public
as $$
declare
    me uuid := auth.uid();
    cats text[] := coalesce(p_categories, ARRAY[]::text[]);
    has_myquiz boolean := 'myquiz' = any(cats);
    /* Are there ANY non-myquiz categories selected? If categories is
       empty/null we treat it as "all curated" per the original
       behavior. */
    fetch_curated boolean := (
        p_categories is null
        or array_length(p_categories,1) is null
        or exists (select 1 from unnest(cats) c where c != 'myquiz')
    );
    /* Curated category list with myquiz stripped — used to filter the
       curated query. */
    curated_cats text[] := array(
        select c from unnest(cats) c where c != 'myquiz'
    );
begin
    return query
    (
        select q.id, q.category, q.era, q.difficulty, q.question, q.options,
               q.correct, q.hint, q.source, q.created_at, q.language
          from public.quiz_questions q
         where fetch_curated
           and q.language = coalesce(p_language, 'ko')
           and (
                /* No filter (legacy "all categories") */
                array_length(curated_cats,1) is null
                /* Or category in the requested list */
                or q.category = any(curated_cats)
           )
        union all
        select uq.id,
               'myquiz'::text as category,
               'modern'::text as era,
               2 as difficulty,
               uq.question,
               uq.options,
               uq.correct,
               uq.hint,
               null::text as source,
               uq.created_at,
               uq.language
          from public.quiz_user_questions uq
         where has_myquiz
           and me is not null
           and uq.user_id = me
           and uq.expires_at > now()
           and uq.language = coalesce(p_language, 'ko')
    )
    order by random()
    limit greatest(1, least(p_count, 30));
end;
$$;
grant execute on function public.quiz_random_questions(text[], int, text) to authenticated, anon;
