-- =====================================================================
-- Lucky Please — Action games one-shot redeploy
-- =====================================================================
-- Symptom this fixes:
--   When the snake / pacman / dodge / burger game-over overlay shows
--   "🛠 랭킹 시스템 점검 중" and the browser console reports 404s on
--   record_*_attempt / *_records / *_my_stats / *_rank_info / *_leaderboard,
--   that means the per-game tables/RPCs aren't deployed to your
--   Supabase database yet.
--
-- USAGE:
--   1. Open Supabase dashboard → SQL Editor → "+ New query"
--   2. Paste THIS ENTIRE FILE
--   3. Click Run
--   4. Reload the action-game page in the browser
--   5. The "🛠 랭킹 시스템 점검 중" message disappears, the world rank
--      ("🌍 #N · 상위 X%") shows up.
--
-- IDEMPOTENCY:
--   Every section uses `create table if not exists`, `create or replace
--   function`, `drop policy if exists` so re-running on a partially-
--   deployed DB is safe — existing rows preserved, missing pieces
--   filled in. Other tables / RPCs / data are NOT touched (this file
--   only references snake_*/pacman_*/dodge_*/burger_* objects + their
--   *_rank_info follow-up).
--
-- The final `notify pgrst, 'reload schema';` at the bottom forces
-- PostgREST to refresh its function cache so the new RPCs become
-- callable immediately (without it the cache lag can cause a few-
-- minute window where the schema is up-to-date but the API still
-- 404s).
-- =====================================================================

-- ====================================================================
-- 2026-04-22-snake-game.sql
-- ====================================================================
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

-- ====================================================================
-- 2026-04-22-pacman-game.sql
-- ====================================================================
create table if not exists public.pacman_attempts (
    id            bigserial   primary key,
    user_id       uuid        not null references auth.users(id) on delete cascade,
    score         int         not null check (score >= 0 and score <= 999999),
    dots_eaten    int         not null check (dots_eaten >= 0 and dots_eaten <= 2000),
    ghosts_eaten  int         not null check (ghosts_eaten >= 0 and ghosts_eaten <= 1000),
    duration_ms   int         not null check (duration_ms between 0 and 3600000),
    won           boolean     not null default false,
    created_at    timestamptz not null default now()
);
create index if not exists pacman_attempts_user_idx on public.pacman_attempts (user_id, created_at desc);
create index if not exists pacman_attempts_score_idx on public.pacman_attempts (score desc);

alter table public.pacman_attempts enable row level security;
drop policy if exists "pacman_attempts_select_all" on public.pacman_attempts;
create policy "pacman_attempts_select_all"
    on public.pacman_attempts for select using (true);


create table if not exists public.pacman_records (
    user_id          uuid        primary key references auth.users(id) on delete cascade,
    best_score       int         not null,
    total_games      int         not null default 0,
    total_wins       int         not null default 0,
    total_playtime_ms bigint     not null default 0,
    updated_at       timestamptz not null default now()
);
create index if not exists pacman_records_best_idx on public.pacman_records (best_score desc);

alter table public.pacman_records enable row level security;
drop policy if exists "pacman_records_select_all" on public.pacman_records;
create policy "pacman_records_select_all"
    on public.pacman_records for select using (true);


create or replace function public._pacman_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.pacman_records
           (user_id, best_score, total_games, total_wins, total_playtime_ms, updated_at)
    values (new.user_id, new.score, 1, case when new.won then 1 else 0 end, new.duration_ms, now())
    on conflict (user_id) do update
      set best_score        = greatest(public.pacman_records.best_score, new.score),
          total_games       = public.pacman_records.total_games + 1,
          total_wins        = public.pacman_records.total_wins + case when new.won then 1 else 0 end,
          total_playtime_ms = public.pacman_records.total_playtime_ms + new.duration_ms,
          updated_at        = now();
    return new;
end;
$$;
drop trigger if exists pacman_refresh_record on public.pacman_attempts;
create trigger pacman_refresh_record
    after insert on public.pacman_attempts
    for each row execute function public._pacman_refresh_record();


-- RPC: record a finished game. Client reports dots/ghosts/duration/won,
-- server derives score (dots*10 + ghosts*200 + win bonus) so client
-- cannot make up a score.
create or replace function public.record_pacman_attempt(
    p_dots_eaten int, p_ghosts_eaten int, p_duration_ms int, p_won boolean
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
    if p_dots_eaten < 0 or p_dots_eaten > 2000 then raise exception 'bad_dots'; end if;
    if p_ghosts_eaten < 0 or p_ghosts_eaten > 1000 then raise exception 'bad_ghosts'; end if;
    if p_duration_ms < 0 or p_duration_ms > 3600000 then raise exception 'bad_duration'; end if;
    /* Absurd pacing guard — each dot/ghost takes at least ~100 ms of
       gameplay. 2 seconds minimum total game so bots can't flood. */
    if p_duration_ms < 2000 then raise exception 'too_short'; end if;
    if (p_dots_eaten + p_ghosts_eaten) > 0
       and p_duration_ms < (p_dots_eaten + p_ghosts_eaten) * 90 then
        raise exception 'impossible_pace';
    end if;

    select count(*) into recent_count
      from public.pacman_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    calc_score := p_dots_eaten * 10 + p_ghosts_eaten * 200 + case when p_won then 500 else 0 end;

    select best_score into prior_best from public.pacman_records where user_id = me;

    insert into public.pacman_attempts
        (user_id, score, dots_eaten, ghosts_eaten, duration_ms, won)
    values (me, calc_score, p_dots_eaten, p_ghosts_eaten, p_duration_ms, coalesce(p_won,false));

    return jsonb_build_object(
        'ok', true,
        'score', calc_score,
        'is_personal_best', prior_best is null or calc_score > prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_pacman_attempt(int, int, int, boolean) to authenticated;


create or replace function public.pacman_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
) returns table (
    rnk          int,
    user_id      uuid,
    nickname     text,
    avatar_url   text,
    best_score   int,
    total_games  int,
    total_wins   int,
    achieved_at  timestamptz
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
                   r.best_score, r.total_games, r.total_wins, r.updated_at
            from public.pacman_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id, max(score) as best_today, min(created_at) as first_at
                from public.pacman_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            )
            select (row_number() over (order by t.best_today desc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today, coalesce(r.total_games,0), coalesce(r.total_wins,0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.pacman_records r on r.user_id = t.user_id
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
                   r.best_score, r.total_games, r.total_wins, r.updated_at
            from public.pacman_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.pacman_leaderboard(text, int) to authenticated, anon;


create or replace function public.pacman_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.pacman_records%rowtype;
        rank_world int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.pacman_records where user_id = me;
    if not found then return jsonb_build_object('has_record', false); end if;
    select 1 + count(*) into rank_world
      from public.pacman_records
     where best_score > rec.best_score;
    return jsonb_build_object(
        'has_record', true,
        'best_score', rec.best_score,
        'total_games', rec.total_games,
        'total_wins', rec.total_wins,
        'world_rank', rank_world
    );
end;
$$;
grant execute on function public.pacman_my_stats() to authenticated;

-- ====================================================================
-- 2026-04-22-burger-game.sql
-- ====================================================================
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

-- ====================================================================
-- 2026-04-25-dodge-game.sql
-- ====================================================================

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

-- ====================================================================
-- 2026-04-26-game-rank-info.sql
-- ====================================================================

-- Snake -----------------------------------------------------------------
create or replace function public.snake_rank_info()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        my_best int;
        rank_w int;
        total_w int;
        pct numeric;
begin
    if me is null then return jsonb_build_object('has_record', false); end if;
    select best_score into my_best from public.snake_records where user_id = me;
    if my_best is null then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_w
      from public.snake_records where best_score > my_best;
    select count(*) into total_w from public.snake_records;

    pct := case when total_w > 0
                then round((rank_w::numeric / total_w) * 100, 1)
                else null end;

    return jsonb_build_object(
        'has_record', true,
        'best_score', my_best,
        'world_rank', rank_w,
        'total_world_players', total_w,
        'percentile', pct
    );
end;
$$;
grant execute on function public.snake_rank_info() to authenticated;


-- Dodge -----------------------------------------------------------------
create or replace function public.dodge_rank_info()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        my_best int;
        rank_w int;
        total_w int;
        pct numeric;
begin
    if me is null then return jsonb_build_object('has_record', false); end if;
    select best_score into my_best from public.dodge_records where user_id = me;
    if my_best is null then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_w
      from public.dodge_records where best_score > my_best;
    select count(*) into total_w from public.dodge_records;

    pct := case when total_w > 0
                then round((rank_w::numeric / total_w) * 100, 1)
                else null end;

    return jsonb_build_object(
        'has_record', true,
        'best_score', my_best,
        'world_rank', rank_w,
        'total_world_players', total_w,
        'percentile', pct
    );
end;
$$;
grant execute on function public.dodge_rank_info() to authenticated;


-- Burger ----------------------------------------------------------------
create or replace function public.burger_rank_info()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        my_best int;
        rank_w int;
        total_w int;
        pct numeric;
begin
    if me is null then return jsonb_build_object('has_record', false); end if;
    select best_score into my_best from public.burger_records where user_id = me;
    if my_best is null then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_w
      from public.burger_records where best_score > my_best;
    select count(*) into total_w from public.burger_records;

    pct := case when total_w > 0
                then round((rank_w::numeric / total_w) * 100, 1)
                else null end;

    return jsonb_build_object(
        'has_record', true,
        'best_score', my_best,
        'world_rank', rank_w,
        'total_world_players', total_w,
        'percentile', pct
    );
end;
$$;
grant execute on function public.burger_rank_info() to authenticated;


-- Pacman ----------------------------------------------------------------
create or replace function public.pacman_rank_info()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        my_best int;
        rank_w int;
        total_w int;
        pct numeric;
begin
    if me is null then return jsonb_build_object('has_record', false); end if;
    select best_score into my_best from public.pacman_records where user_id = me;
    if my_best is null then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_w
      from public.pacman_records where best_score > my_best;
    select count(*) into total_w from public.pacman_records;

    pct := case when total_w > 0
                then round((rank_w::numeric / total_w) * 100, 1)
                else null end;

    return jsonb_build_object(
        'has_record', true,
        'best_score', my_best,
        'world_rank', rank_w,
        'total_world_players', total_w,
        'percentile', pct
    );
end;
$$;
grant execute on function public.pacman_rank_info() to authenticated;

-- ====================================================================
-- Final: refresh PostgREST schema cache so all new functions are
-- callable immediately.
-- ====================================================================
notify pgrst, 'reload schema';
