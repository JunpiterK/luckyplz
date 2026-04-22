-- =====================================================================
-- Migration: Burger Chef (record-keeping skill game replacing Reaction)
-- Date:      2026-04-22
-- Purpose:   Tap-5-plates timed-order stacking game. Sample burger on
--            the left; 5 ingredient plates on the bottom; player taps
--            them in the same order as the sample inside a shrinking
--            time budget. Wrong tap = -2 s + combo reset. Complete the
--            burger = level up, longer sample, tighter clock.
--
--            Score is derived SERVER-SIDE from ingredients_caught,
--            burgers_completed and level_reached (so a tampered client
--            can't submit an arbitrary number). Anti-cheat: minimum
--            pacing (each correct tap takes real time), plus the usual
--            30-per-hour rate limit. Same SECURITY DEFINER pattern as
--            Pac-Man / Snake.
-- =====================================================================

create table if not exists public.burger_attempts (
    id                  bigserial   primary key,
    user_id             uuid        not null references auth.users(id) on delete cascade,
    score               int         not null check (score >= 0 and score <= 9999999),
    burgers_completed   int         not null check (burgers_completed >= 0 and burgers_completed <= 1000),
    ingredients_caught  int         not null check (ingredients_caught >= 0 and ingredients_caught <= 10000),
    level_reached       int         not null check (level_reached >= 1 and level_reached <= 100),
    duration_ms         int         not null check (duration_ms between 0 and 3600000),
    created_at          timestamptz not null default now()
);
create index if not exists burger_attempts_user_idx  on public.burger_attempts (user_id, created_at desc);
create index if not exists burger_attempts_score_idx on public.burger_attempts (score desc);

alter table public.burger_attempts enable row level security;
drop policy if exists "burger_attempts_select_all" on public.burger_attempts;
create policy "burger_attempts_select_all"
    on public.burger_attempts for select using (true);


create table if not exists public.burger_records (
    user_id           uuid        primary key references auth.users(id) on delete cascade,
    best_score        int         not null,
    best_level        int         not null default 1,
    total_games       int         not null default 0,
    total_burgers     int         not null default 0,
    total_playtime_ms bigint      not null default 0,
    updated_at        timestamptz not null default now()
);
create index if not exists burger_records_best_idx on public.burger_records (best_score desc);

alter table public.burger_records enable row level security;
drop policy if exists "burger_records_select_all" on public.burger_records;
create policy "burger_records_select_all"
    on public.burger_records for select using (true);


create or replace function public._burger_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.burger_records
           (user_id, best_score, best_level, total_games, total_burgers, total_playtime_ms, updated_at)
    values (new.user_id, new.score, new.level_reached, 1, new.burgers_completed, new.duration_ms, now())
    on conflict (user_id) do update
      set best_score        = greatest(public.burger_records.best_score, new.score),
          best_level        = greatest(public.burger_records.best_level, new.level_reached),
          total_games       = public.burger_records.total_games + 1,
          total_burgers     = public.burger_records.total_burgers + new.burgers_completed,
          total_playtime_ms = public.burger_records.total_playtime_ms + new.duration_ms,
          updated_at        = now();
    return new;
end;
$$;
drop trigger if exists burger_refresh_record on public.burger_attempts;
create trigger burger_refresh_record
    after insert on public.burger_attempts
    for each row execute function public._burger_refresh_record();


-- RPC: record a finished game. Client reports ingredients/burgers/
-- level/duration; server derives score using a fixed formula so the
-- client can't make up points. Score = ingredients*10 + burgers*50 +
-- level_reached*100 (level bonus rewards surviving to higher stages,
-- not just tapping a lot at level 1).
create or replace function public.record_burger_attempt(
    p_burgers_completed  int,
    p_ingredients_caught int,
    p_level_reached      int,
    p_duration_ms        int
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
    if p_burgers_completed < 0 or p_burgers_completed > 1000 then raise exception 'bad_burgers'; end if;
    if p_ingredients_caught < 0 or p_ingredients_caught > 10000 then raise exception 'bad_ingredients'; end if;
    if p_level_reached < 1 or p_level_reached > 100 then raise exception 'bad_level'; end if;
    if p_duration_ms < 0 or p_duration_ms > 3600000 then raise exception 'bad_duration'; end if;
    /* Pacing guard — each tap takes at least ~300 ms of real time
       (perceive + react + thumb travel). Reject games that claim to
       have tapped more correct ingredients than that pacing would
       allow. Also 2s minimum total so scripted refresh-loops can't
       flood records. */
    if p_duration_ms < 2000 then raise exception 'too_short'; end if;
    if p_ingredients_caught > 0 and p_duration_ms < p_ingredients_caught * 300 then
        raise exception 'impossible_pace';
    end if;

    select count(*) into recent_count
      from public.burger_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    calc_score := p_ingredients_caught * 10
                + p_burgers_completed * 50
                + p_level_reached * 100;

    select best_score into prior_best from public.burger_records where user_id = me;

    insert into public.burger_attempts
        (user_id, score, burgers_completed, ingredients_caught, level_reached, duration_ms)
    values (me, calc_score, p_burgers_completed, p_ingredients_caught, p_level_reached, p_duration_ms);

    return jsonb_build_object(
        'ok', true,
        'score', calc_score,
        'is_personal_best', prior_best is null or calc_score > prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_burger_attempt(int, int, int, int) to authenticated;


create or replace function public.burger_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk           int,
    user_id       uuid,
    nickname      text,
    avatar_url    text,
    best_score    int,
    best_level    int,
    total_games   int,
    total_burgers int,
    achieved_at   timestamptz
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
                   r.best_score, r.best_level, r.total_games, r.total_burgers, r.updated_at
            from public.burger_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id, max(score) as best_today,
                       max(level_reached) as best_lvl_today,
                       min(created_at) as first_at
                from public.burger_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today desc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today, t.best_lvl_today,
                   coalesce(r.total_games,0), coalesce(r.total_burgers,0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.burger_records r on r.user_id = t.user_id
            order by t.best_today desc, t.first_at asc
            limit greatest(1, least(p_limit, 100));
    else
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
                   r.best_score, r.best_level, r.total_games, r.total_burgers, r.updated_at
            from public.burger_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.burger_leaderboard(text, int) to authenticated, anon;


create or replace function public.burger_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.burger_records%rowtype;
        rank_world int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.burger_records where user_id = me;
    if not found then return jsonb_build_object('has_record', false); end if;
    select 1 + count(*) into rank_world
      from public.burger_records
     where best_score > rec.best_score;
    return jsonb_build_object(
        'has_record',    true,
        'best_score',    rec.best_score,
        'best_level',    rec.best_level,
        'total_games',   rec.total_games,
        'total_burgers', rec.total_burgers,
        'world_rank',    rank_world
    );
end;
$$;
grant execute on function public.burger_my_stats() to authenticated;
