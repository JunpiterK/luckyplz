-- =====================================================================
-- Migration: Unified ranking — p_start_rank pagination for all action games
-- Date:      2026-05-02
-- Purpose:   클라이언트의 통합 랭크 윈도우가 "특정 순위부터 +29위까지"
--            점프할 수 있도록 모든 leaderboard RPC 에 p_start_rank
--            파라미터 추가. 기존 호출 (p_start_rank 미지정) 은 default 1
--            로 동작 → 후방 호환.
--
-- 적용 RPC (6개 액션 게임):
--   * snake_leaderboard
--   * burger_leaderboard
--   * pacman_leaderboard
--   * dodge_leaderboard
--   * tetris_leaderboard
--   * tetris_sprint_leaderboard
--
-- 패턴: row_number() over (...) 를 CTE 안으로 옮기고 where rnk >= p_start_rank
--       limit 적용. 같은 정렬, 같은 return shape 유지.
-- =====================================================================

-- =====================================================================
-- 1. SNAKE
-- =====================================================================
create or replace function public.snake_leaderboard(
    p_scope      text default 'world',
    p_limit      int  default 50,
    p_start_rank int  default 1
) returns table (
    rnk             int,
    user_id         uuid,
    nickname        text,
    avatar_url      text,
    best_score      int,
    best_foods_eaten int,
    total_games     int,
    achieved_at     timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;
    if p_start_rank < 1 then p_start_rank := 1; end if;

    if p_scope = 'world' then
        return query
            with ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.best_foods_eaten, r.total_games, r.updated_at as achieved_at
                from public.snake_records r
                join public.profiles p on p.id = r.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       max(score) as best_today,
                       max(foods_eaten) as foods_today,
                       min(created_at) as first_at
                from public.snake_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            ),
            ranked as (
                select (row_number() over (order by t.best_today desc, t.first_at asc))::int as rnk,
                       t.user_id, p.nickname, p.avatar_url,
                       t.best_today as best_score, t.foods_today as best_foods_eaten,
                       coalesce(r.total_games, 0) as total_games, t.first_at as achieved_at
                from today_attempts t
                join public.profiles p on p.id = t.user_id
                left join public.snake_records r on r.user_id = t.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            ),
            ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.best_foods_eaten, r.total_games, r.updated_at as achieved_at
                from public.snake_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (select fid from friend_ids)
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.snake_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 2. BURGER
-- =====================================================================
create or replace function public.burger_leaderboard(
    p_scope      text default 'world',
    p_limit      int  default 50,
    p_start_rank int  default 1
) returns table (
    rnk            int,
    user_id        uuid,
    nickname       text,
    avatar_url     text,
    best_score     int,
    best_level     int,
    total_games    int,
    total_burgers  int,
    achieved_at    timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;
    if p_start_rank < 1 then p_start_rank := 1; end if;

    if p_scope = 'world' then
        return query
            with ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.best_level, r.total_games, r.total_burgers,
                       r.updated_at as achieved_at
                from public.burger_records r
                join public.profiles p on p.id = r.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       max(score) as best_today,
                       max(level_reached) as level_today,
                       sum(burgers_served) as burgers_today,
                       min(created_at) as first_at
                from public.burger_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            ),
            ranked as (
                select (row_number() over (order by t.best_today desc, t.first_at asc))::int as rnk,
                       t.user_id, p.nickname, p.avatar_url,
                       t.best_today as best_score, t.level_today as best_level,
                       coalesce(r.total_games, 0) as total_games,
                       t.burgers_today::int as total_burgers,
                       t.first_at as achieved_at
                from today_attempts t
                join public.profiles p on p.id = t.user_id
                left join public.burger_records r on r.user_id = t.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            ),
            ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.best_level, r.total_games, r.total_burgers,
                       r.updated_at as achieved_at
                from public.burger_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (select fid from friend_ids)
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.burger_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 3. PACMAN
-- =====================================================================
create or replace function public.pacman_leaderboard(
    p_scope      text default 'world',
    p_limit      int  default 50,
    p_start_rank int  default 1
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
    if p_start_rank < 1 then p_start_rank := 1; end if;

    if p_scope = 'world' then
        return query
            with ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.total_games, r.total_wins,
                       r.updated_at as achieved_at
                from public.pacman_records r
                join public.profiles p on p.id = r.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       max(score) as best_today,
                       sum(case when won then 1 else 0 end) as wins_today,
                       min(created_at) as first_at
                from public.pacman_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            ),
            ranked as (
                select (row_number() over (order by t.best_today desc, t.first_at asc))::int as rnk,
                       t.user_id, p.nickname, p.avatar_url,
                       t.best_today as best_score,
                       coalesce(r.total_games, 0) as total_games,
                       t.wins_today::int as total_wins,
                       t.first_at as achieved_at
                from today_attempts t
                join public.profiles p on p.id = t.user_id
                left join public.pacman_records r on r.user_id = t.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            ),
            ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.total_games, r.total_wins,
                       r.updated_at as achieved_at
                from public.pacman_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (select fid from friend_ids)
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.pacman_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 4. DODGE
-- =====================================================================
create or replace function public.dodge_leaderboard(
    p_scope      text default 'world',
    p_limit      int  default 50,
    p_start_rank int  default 1
) returns table (
    rnk          int,
    user_id      uuid,
    nickname     text,
    avatar_url   text,
    best_score   int,
    total_games  int,
    achieved_at  timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;
    if p_start_rank < 1 then p_start_rank := 1; end if;

    if p_scope = 'world' then
        return query
            with ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.total_games, r.updated_at as achieved_at
                from public.dodge_records r
                join public.profiles p on p.id = r.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       max(score) as best_today,
                       min(created_at) as first_at
                from public.dodge_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            ),
            ranked as (
                select (row_number() over (order by t.best_today desc, t.first_at asc))::int as rnk,
                       t.user_id, p.nickname, p.avatar_url,
                       t.best_today as best_score,
                       coalesce(r.total_games, 0) as total_games, t.first_at as achieved_at
                from today_attempts t
                join public.profiles p on p.id = t.user_id
                left join public.dodge_records r on r.user_id = t.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            ),
            ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.total_games, r.updated_at as achieved_at
                from public.dodge_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (select fid from friend_ids)
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.dodge_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 5. TETRIS (Marathon)
-- =====================================================================
create or replace function public.tetris_leaderboard(
    p_scope      text default 'world',
    p_limit      int  default 50,
    p_start_rank int  default 1
) returns table (
    rnk           int,
    user_id       uuid,
    nickname      text,
    avatar_url    text,
    best_score    int,
    best_lines    int,
    best_level    int,
    total_games   int,
    achieved_at   timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;
    if p_start_rank < 1 then p_start_rank := 1; end if;

    if p_scope = 'world' then
        return query
            with ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.best_lines, r.best_level, r.total_games,
                       r.updated_at as achieved_at
                from public.tetris_records r
                join public.profiles p on p.id = r.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       max(score) as best_today,
                       max(lines_cleared) as lines_today,
                       max(level_reached) as level_today,
                       min(created_at) as first_at
                from public.tetris_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            ),
            ranked as (
                select (row_number() over (order by t.best_today desc, t.first_at asc))::int as rnk,
                       t.user_id, p.nickname, p.avatar_url,
                       t.best_today as best_score, t.lines_today as best_lines,
                       t.level_today as best_level,
                       coalesce(r.total_games, 0) as total_games, t.first_at as achieved_at
                from today_attempts t
                join public.profiles p on p.id = t.user_id
                left join public.tetris_records r on r.user_id = t.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            ),
            ranked as (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_score, r.best_lines, r.best_level, r.total_games,
                       r.updated_at as achieved_at
                from public.tetris_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (select fid from friend_ids)
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.tetris_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 6. TETRIS SPRINT (time-based, lower better)
-- =====================================================================
create or replace function public.tetris_sprint_leaderboard(
    p_scope      text default 'world',
    p_limit      int  default 50,
    p_start_rank int  default 1
) returns table (
    rnk              int,
    user_id          uuid,
    nickname         text,
    avatar_url       text,
    best_duration_ms int,
    total_completes  int,
    achieved_at      timestamptz
)
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
begin
    if p_scope not in ('world','today','friends') then raise exception 'bad_scope'; end if;
    if p_scope = 'friends' and me is null then raise exception 'not_authenticated'; end if;
    if p_start_rank < 1 then p_start_rank := 1; end if;

    if p_scope = 'world' then
        return query
            with ranked as (
                select (row_number() over (order by r.best_duration_ms asc,
                                                    r.achieved_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_duration_ms, r.total_completes, r.achieved_at
                from public.tetris_sprint_records r
                join public.profiles p on p.id = r.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            with today_attempts as (
                select user_id,
                       min(duration_ms) as best_today,
                       min(created_at) as first_at
                from public.tetris_sprint_attempts
                where (created_at at time zone 'Asia/Seoul')::date
                    = (now() at time zone 'Asia/Seoul')::date
                group by user_id
            ),
            ranked as (
                select (row_number() over (order by t.best_today asc,
                                                    t.first_at asc))::int as rnk,
                       t.user_id, p.nickname, p.avatar_url,
                       t.best_today as best_duration_ms,
                       coalesce(r.total_completes, 0) as total_completes,
                       t.first_at as achieved_at
                from today_attempts t
                join public.profiles p on p.id = t.user_id
                left join public.tetris_sprint_records r on r.user_id = t.user_id
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            with friend_ids as (
                select case when user_a = me then user_b else user_a end as fid
                from public.friendships
                where (user_a = me or user_b = me) and status = 'accepted'
                union
                select me
            ),
            ranked as (
                select (row_number() over (order by r.best_duration_ms asc,
                                                    r.achieved_at asc))::int as rnk,
                       r.user_id, p.nickname, p.avatar_url,
                       r.best_duration_ms, r.total_completes, r.achieved_at
                from public.tetris_sprint_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (select fid from friend_ids)
            )
            select * from ranked
            where rnk >= p_start_rank
            order by rnk
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.tetris_sprint_leaderboard(text, int, int) to authenticated, anon;


-- PostgREST schema cache reload — 새 signature 즉시 callable.
notify pgrst, 'reload schema';
