-- =====================================================================
-- Migration: Quiz locales — language column + per-language filter RPC
-- Date:      2026-04-22
-- Purpose:   Multi-country launch. Adds a `language` column to
--            quiz_questions so the same category id (kpop, general,
--            sports, …) can carry DIFFERENT questions per language.
--            Client passes its active locale to the RPC at fetch time
--            and only gets questions in that language.
--
--            Simpler than an array-of-locales: one question = one row
--            = one language. Conceptually-universal questions (water
--            = H2O) live as multiple rows, one per language, because
--            the TEXT itself is language-specific.
--
--            Existing 260+ questions are all Korean content → backfill
--            language='ko'. English seeds arrive in a follow-up
--            migration (2026-04-22-quiz-bank-en-1.sql).
-- =====================================================================

alter table public.quiz_questions
    add column if not exists language text not null default 'ko';

/* Constraint the column via CHECK so a typo ("en-gb", "zh-cn") doesn't
   silently pollute the bank. Expandable — add locale codes here when
   we launch a new language batch. */
alter table public.quiz_questions
    drop constraint if exists quiz_q_language_chk;
alter table public.quiz_questions
    add constraint quiz_q_language_chk check (language in (
        'ko','en','ja','zh','es','de','fr','pt','ru','ar','hi','th','id','vi','tr','gb'
    ));

create index if not exists quiz_q_language_category_idx on public.quiz_questions (language, category);

/* Backfill — every existing row is Korean content. This is a no-op
   for fresh installs (default value handles it). */
update public.quiz_questions set language = 'ko' where language is null or language = '';

/* Rewrite the random-selector to accept p_language. Dropping the old
   two-arg signature first because PostgREST dispatches by named
   params and we don't want a stale overload picking up calls that
   were meant to target the new version. Client code always passes
   p_language now (defaults to 'ko' if omitted). */
drop function if exists public.quiz_random_questions(text[], int);

create or replace function public.quiz_random_questions(
    p_categories text[] default null,
    p_count      int    default 10,
    p_language   text   default 'ko'
) returns setof public.quiz_questions
language sql security definer
set search_path = public
as $$
    select *
      from public.quiz_questions
     where (p_categories is null or array_length(p_categories,1) is null
            or category = any(p_categories))
       and language = coalesce(p_language, 'ko')
     order by random()
     limit greatest(1, least(p_count, 30));
$$;
grant execute on function public.quiz_random_questions(text[], int, text) to authenticated, anon;
