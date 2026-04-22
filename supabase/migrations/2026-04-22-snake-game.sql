-- =====================================================================
-- Migration: Snake game (record-keeping skill game #2)
-- Date:      2026-04-22
-- Purpose:   Classic Snake — arrow / swipe controls, eat food to grow,
--            die on wall or self collision. Session-based score, best
--            per user in a summary table, three-scope leaderboards.
--
-- Same SECURITY DEFINER RPC pattern as the reaction game + dm_inbox
-- (see memory/messaging_rpc_pattern.md). Every read goes through an
-- RPC so mobile WebView RLS quirks never bite.
-- =====================================================================

create table if not exists public.snake_attempts (
    id             bigserial   primary key,
    user_id        uuid        not null references auth.users(id) on delete cascade,
    /* score = foods_eaten * 10 — deterministic + server-verifiable.
       100k cap lets even a perfect 20x20 clear (400 * 10 = 4000) fit
       with a huge margin in case a bigger board is added later. */
    score          int         not null check (score >= 0 and score <= 100000),
    foods_eaten    int         not null check (foods_eaten >= 0 and foods_eaten <= 10000),
    duration_ms    int         not null check (duration_ms between 0 and 3600000),
    created_at     timestamptz not null default now()
);

create index if not exists snake_attempts_user_idx
    on public.snake_attempts (user_id, created_at desc);
create index if not exists snake_attempts_score_idx
    on public.snake_attempts (score desc);

alter table public.snake_attempts enable row level security;
drop policy if exists "snake_attempts_select_all" on public.snake_attempts;
create policy "snake_attempts_select_all"
    on public.snake_attempts for select using (true);


create table if not exists public.snake_records (
    user_id           uuid        primary key references auth.users(id) on delete cascade,
    best_score        int         not null,
    best_foods_eaten  int,
    total_games       int         not null default 0,
    total_playtime_ms bigint      not null default 0,
    updated_at        timestamptz not null default now()
);

create index if not exists snake_records_best_idx on public.snake_records (best_score desc);

alter table public.snake_records enable row level security;
drop policy if exists "snake_records_select_all" on public.snake_records;
create policy "snake_records_select_all"
    on public.snake_records for select using (true);


-- Trigger: maintain the per-user summary after each attempt.
create or replace function public._snake_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.snake_records (user_id, best_score, best_foods_eaten,
                                       total_games, total_playtime_ms, updated_at)
    values (new.user_id, new.score, new.foods_eaten,
            1, new.duration_ms, now())
    on conflict (user_id) do update
      set best_score        = greatest(public.snake_records.best_score, new.score),
          best_foods_eaten  = case when new.score > public.snake_records.best_score
                                   then new.foods_eaten
                                   else public.snake_records.best_foods_eaten end,
          total_games       = public.snake_records.total_games + 1,
          total_playtime_ms = public.snake_records.total_playtime_ms + new.duration_ms,
          updated_at        = now();
    return new;
end;
$$;
drop trigger if exists snake_refresh_record on public.snake_attempts;
create trigger snake_refresh_record
    after insert on public.snake_attempts
    for each row execute function public._snake_refresh_record();


-- RPC: record a finished game. Client reports foods_eaten + duration;
-- server derives score + rate-limits (30 games per hour).
create or replace function public.record_snake_attempt(
    p_foods_eaten int, p_duration_ms int
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
    if p_foods_eaten < 0 or p_foods_eaten > 10000 then raise exception 'bad_foods_eaten'; end if;
    if p_duration_ms < 0 or p_duration_ms > 3600000 then raise exception 'bad_duration'; end if;
    /* Each food requires at least ~200 ms of ticks to reach (the
       fastest level is 80 ms/tick × a few ticks min), so reject
       obvious bots that claim 100 foods in 1 second. Generous bound
       so legitimate fast players aren't rejected. */
    if p_foods_eaten > 0 and p_duration_ms < p_foods_eaten * 80 then
        raise exception 'impossible_pace';
    end if;

    select count(*) into recent_count
      from public.snake_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    calc_score := p_foods_eaten * 10;

    select best_score into prior_best from public.snake_records where user_id = me;

    insert into public.snake_attempts (user_id, score, foods_eaten, duration_ms)
    values (me, calc_score, p_foods_eaten, p_duration_ms);

    return jsonb_build_object(
        'ok', true,
        'score', calc_score,
        'is_personal_best', prior_best is null or calc_score > prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_snake_attempt(int, int) to authenticated;


-- RPC: leaderboard with three scopes (world / today / friends).
-- Ordered by score DESC, tie-breaker by earlier record time
-- (achieving higher score earlier = more impressive).
create or replace function public.snake_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk               int,
    user_id           uuid,
    nickname          text,
    avatar_url        text,
    best_score        int,
    best_foods_eaten  int,
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
                   r.best_score, r.best_foods_eaten, r.total_games, r.updated_at
            from public.snake_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id, max(score) as best_today, max(foods_eaten) as foods_today,
                       min(created_at) as first_at
                from public.snake_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today desc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today, t.foods_today, coalesce(r.total_games, 0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.snake_records r on r.user_id = t.user_id
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
                   r.best_score, r.best_foods_eaten, r.total_games, r.updated_at
            from public.snake_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.snake_leaderboard(text, int) to authenticated, anon;


-- RPC: bundled personal stats for the game page open.
create or replace function public.snake_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.snake_records%rowtype;
        rank_world int;
        recents jsonb;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.snake_records where user_id = me;
    if not found then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_world
      from public.snake_records
     where best_score > rec.best_score;

    select jsonb_agg(x order by created_at desc) into recents
    from (
        select score, foods_eaten, duration_ms, created_at
        from public.snake_attempts
        where user_id = me
        order by created_at desc
        limit 10
    ) x;

    return jsonb_build_object(
        'has_record', true,
        'best_score', rec.best_score,
        'best_foods_eaten', rec.best_foods_eaten,
        'total_games', rec.total_games,
        'total_playtime_ms', rec.total_playtime_ms,
        'world_rank', rank_world,
        'recent_attempts', coalesce(recents, '[]'::jsonb)
    );
end;
$$;
grant execute on function public.snake_my_stats() to authenticated;
