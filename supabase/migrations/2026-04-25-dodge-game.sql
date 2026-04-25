-- =====================================================================
-- Migration: Dodge game (bullet-dodging airplane, skill game #3)
-- Date:      2026-04-25
-- Purpose:   Survive enemy bullets as long as possible.
--            Score = floor(duration_ms / 100) (10 pts/sec).
--            Session-based score, best per user in a summary table,
--            three-scope leaderboards.
--
-- Same SECURITY DEFINER RPC pattern as the reaction game + dm_inbox
-- (see memory/messaging_rpc_pattern.md). Every read goes through an
-- RPC so mobile WebView RLS quirks never bite.
-- =====================================================================

create table if not exists public.dodge_attempts (
    id             bigserial   primary key,
    user_id        uuid        not null references auth.users(id) on delete cascade,
    /* score = floor(duration_ms / 100) — 10 pts/sec.
       100k cap covers a theoretical 10000-second run with huge margin. */
    score          int         not null check (score >= 0 and score <= 100000),
    duration_ms    int         not null check (duration_ms between 0 and 3600000),
    created_at     timestamptz not null default now()
);

create index if not exists dodge_attempts_user_idx
    on public.dodge_attempts (user_id, created_at desc);
create index if not exists dodge_attempts_score_idx
    on public.dodge_attempts (score desc);

alter table public.dodge_attempts enable row level security;
drop policy if exists "dodge_attempts_select_all" on public.dodge_attempts;
create policy "dodge_attempts_select_all"
    on public.dodge_attempts for select using (true);


create table if not exists public.dodge_records (
    user_id           uuid        primary key references auth.users(id) on delete cascade,
    best_score        int         not null,
    total_games       int         not null default 0,
    total_playtime_ms bigint      not null default 0,
    updated_at        timestamptz not null default now()
);

create index if not exists dodge_records_best_idx on public.dodge_records (best_score desc);

alter table public.dodge_records enable row level security;
drop policy if exists "dodge_records_select_all" on public.dodge_records;
create policy "dodge_records_select_all"
    on public.dodge_records for select using (true);


-- Trigger: maintain the per-user summary after each attempt.
create or replace function public._dodge_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.dodge_records (user_id, best_score,
                                      total_games, total_playtime_ms, updated_at)
    values (new.user_id, new.score,
            1, new.duration_ms, now())
    on conflict (user_id) do update
      set best_score        = greatest(public.dodge_records.best_score, new.score),
          total_games       = public.dodge_records.total_games + 1,
          total_playtime_ms = public.dodge_records.total_playtime_ms + new.duration_ms,
          updated_at        = now();
    return new;
end;
$$;
drop trigger if exists dodge_refresh_record on public.dodge_attempts;
create trigger dodge_refresh_record
    after insert on public.dodge_attempts
    for each row execute function public._dodge_refresh_record();


-- RPC: record a finished game. Client reports duration_ms only;
-- server derives score + rate-limits (30 games per hour).
create or replace function public.record_dodge_attempt(
    p_duration_ms int
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        prior_best int;
        recent_count int;
        calc_score int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_duration_ms < 0 or p_duration_ms > 3600000 then raise exception 'bad_duration'; end if;

    select count(*) into recent_count
      from public.dodge_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    calc_score := floor(p_duration_ms / 100);

    /* Anti-cheat: 12 minutes (720s) is an extremely generous practical cap.
       score > 7200 means claimed > 720 seconds alive — reject as implausible.
       (The duration cap above already prevents > 36000, but this tightens it.) */
    if calc_score > 7200 then raise exception 'impossible_score'; end if;

    select best_score into prior_best from public.dodge_records where user_id = me;

    insert into public.dodge_attempts (user_id, score, duration_ms)
    values (me, calc_score, p_duration_ms);

    return jsonb_build_object(
        'ok', true,
        'score', calc_score,
        'is_personal_best', prior_best is null or calc_score > prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_dodge_attempt(int) to authenticated;


-- RPC: leaderboard with three scopes (world / today / friends).
-- Ordered by score DESC, tie-breaker by earlier record time.
create or replace function public.dodge_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk               int,
    user_id           uuid,
    nickname          text,
    avatar_url        text,
    best_score        int,
    total_games       int,
    achieved_at       timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;

    if p_scope = 'world' then
        return query
            select (row_number() over (order by r.best_score desc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_score, r.total_games, r.updated_at
            from public.dodge_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id, max(score) as best_today,
                       min(created_at) as first_at
                from public.dodge_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today desc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today, coalesce(r.total_games, 0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.dodge_records r on r.user_id = t.user_id
            order by t.best_today desc, t.first_at asc
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            )
            select (row_number() over (order by r.best_score desc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_score, r.total_games, r.updated_at
            from public.dodge_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.dodge_leaderboard(text, int) to authenticated, anon;


-- RPC: bundled personal stats for the game page open.
create or replace function public.dodge_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.dodge_records%rowtype;
        rank_world int;
        recents jsonb;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.dodge_records where user_id = me;
    if not found then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_world
      from public.dodge_records
     where best_score > rec.best_score;

    select jsonb_agg(x order by created_at desc) into recents
    from (
        select score, duration_ms, created_at
        from public.dodge_attempts
        where user_id = me
        order by created_at desc
        limit 10
    ) x;

    return jsonb_build_object(
        'has_record', true,
        'best_score', rec.best_score,
        'total_games', rec.total_games,
        'total_playtime_ms', rec.total_playtime_ms,
        'world_rank', rank_world,
        'recent_attempts', coalesce(recents, '[]'::jsonb)
    );
end;
$$;
grant execute on function public.dodge_my_stats() to authenticated;
