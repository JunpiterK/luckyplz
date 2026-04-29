-- =====================================================================
-- Migration: Quiz — per-category quota RPC
-- Date:      2026-04-29
-- Purpose:   The existing quiz_random_questions(p_categories, p_count, ...)
--            picks N rows uniformly from the union of all selected
--            categories. With a wildly uneven bank size (200 sports vs
--            40 K-pop) most picks land in the bigger category, so the
--            mix the host expects ("balanced across what I picked")
--            doesn't materialize.
--
--            New flow: client computes a per-category quota map
--            ({"kpop":3,"sports":3,"general":4}) — either by even-
--            splitting a target total, or by collecting the host's
--            explicit per-category numbers — and sends that to the
--            server. Server enforces the quota strictly per category
--            via window.row_number().
--
--            The 'myquiz' key is honoured the same way: that many
--            rows from the caller's quiz_user_questions, RLS-scoped
--            to themselves.
--
--            Old quiz_random_questions stays for backward compat —
--            no other code path uses it but we don't want to break
--            future re-exports of this RPC by name.
-- =====================================================================

create or replace function public.quiz_random_questions_quota(
    p_quotas   jsonb  default '{}'::jsonb,    -- {"kpop":3,"sports":3,"myquiz":2}
    p_language text   default 'ko'
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
    /* "myquiz" entry triggers user-content lookup; everything else is
       a curated category. We split the keys here so the curated query
       below doesn't waste a comparison against the user-content table. */
    curated_cats text[] := array(
        select k from jsonb_object_keys(p_quotas) k where k != 'myquiz'
    );
    myquiz_quota int := coalesce((p_quotas->>'myquiz')::int, 0);
    /* Hard cap so a malicious payload like {"kpop":99999} can't drag
       a huge result set out of the bank. 30 mirrors the original cap. */
    HARD_CAP constant int := 30;
begin
    if jsonb_typeof(p_quotas) is null or jsonb_typeof(p_quotas) != 'object' then
        raise exception 'bad_quotas';
    end if;

    return query
    with curated_pool as (
        select q.id, q.category, q.era, q.difficulty, q.question, q.options,
               q.correct, q.hint, q.source, q.created_at, q.language,
               row_number() over (partition by q.category order by random()) as rn
          from public.quiz_questions q
         where q.language = coalesce(p_language, 'ko')
           and q.category = any(curated_cats)
    ),
    curated_picks as (
        select cp.* from curated_pool cp
         where cp.rn <= coalesce((p_quotas->>cp.category)::int, 0)
    ),
    myquiz_pool as (
        select uq.id,
               'myquiz'::text as category,
               'modern'::text as era,
               2 as difficulty,
               uq.question, uq.options, uq.correct, uq.hint,
               null::text as source, uq.created_at, uq.language,
               row_number() over (order by random()) as rn
          from public.quiz_user_questions uq
         where myquiz_quota > 0
           and me is not null
           and uq.user_id = me
           and uq.expires_at > now()
           and uq.language = coalesce(p_language, 'ko')
    ),
    myquiz_picks as (
        select mp.id, mp.category, mp.era, mp.difficulty, mp.question, mp.options,
               mp.correct, mp.hint, mp.source, mp.created_at, mp.language
          from myquiz_pool mp
         where mp.rn <= myquiz_quota
    ),
    /* Final union with a single shuffle so questions don't appear
       grouped-by-category to the player. Cap to HARD_CAP regardless of
       what the quotas summed to. */
    everything as (
        select cp.id, cp.category, cp.era, cp.difficulty, cp.question, cp.options,
               cp.correct, cp.hint, cp.source, cp.created_at, cp.language
          from curated_picks cp
        union all
        select mp.id, mp.category, mp.era, mp.difficulty, mp.question, mp.options,
               mp.correct, mp.hint, mp.source, mp.created_at, mp.language
          from myquiz_picks mp
    )
    select e.id, e.category, e.era, e.difficulty, e.question, e.options,
           e.correct, e.hint, e.source, e.created_at, e.language
      from everything e
     order by random()
     limit HARD_CAP;
end;
$$;
grant execute on function public.quiz_random_questions_quota(jsonb, text) to authenticated, anon;
