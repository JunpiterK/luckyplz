-- =====================================================================
-- Migration: Leaderboard RPC clean rebuild (bullet-proof against rnk ambig)
-- Date:      2026-05-02
-- Purpose:   직전 두 fix migration 적용 후에도 "오늘" scope 호출 시
--            'rnk is ambiguous' 에러가 계속 뜨는 케이스 대응.
--
-- 진단 가설: PostgreSQL plpgsql 함수에서 RETURNS TABLE 의 output
--            파라미터 (rnk, user_id 등) 가 함수 body 안 모든 select
--            scope 에서 column candidate 으로 visible. CTE 안 row_number()
--            결과를 'as rnk' 로 alias 하면 inner select 의 rnk 가
--            output 파라미터 rnk 와 충돌 → ambiguous.
--
-- 해결: CTE 안 column 이름을 _rank_pos 처럼 underscore prefix + 명확히
--       다른 이름으로 지정 → output 파라미터 와 충돌 불가능.
--       바깥 select 에서 _rank_pos AS rnk 로 다시 매핑.
--       모든 6 RPC 동일 패턴.
--
-- 추가: 모든 가능한 old signature 명시적 DROP (text,int / text,int,int).
--       PostgreSQL function overloading 으로 잔존 broken 버전 routing
--       방지.
-- =====================================================================

-- ---- 1. Drop ALL old signatures first (any number of args) ----
drop function if exists public.snake_leaderboard(text, int);
drop function if exists public.snake_leaderboard(text, int, int);
drop function if exists public.burger_leaderboard(text, int);
drop function if exists public.burger_leaderboard(text, int, int);
drop function if exists public.pacman_leaderboard(text, int);
drop function if exists public.pacman_leaderboard(text, int, int);
drop function if exists public.dodge_leaderboard(text, int);
drop function if exists public.dodge_leaderboard(text, int, int);
drop function if exists public.tetris_leaderboard(text, int);
drop function if exists public.tetris_leaderboard(text, int, int);
drop function if exists public.tetris_sprint_leaderboard(text, int);
drop function if exists public.tetris_sprint_leaderboard(text, int, int);


-- =====================================================================
-- 1. SNAKE
-- =====================================================================
create function public.snake_leaderboard(
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
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._foods, sub._games, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.best_foods_eaten as _foods,
                       r.total_games as _games, r.updated_at as _when
                from public.snake_records r
                join public.profiles p on p.id = r.user_id
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._foods, sub._games, sub._when
            from (
                select (row_number() over (order by t._best_today desc, t._first_at asc))::int as _rank_pos,
                       t._uid as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score, t._foods_today as _foods,
                       coalesce(r.total_games, 0) as _games, t._first_at as _when
                from (
                    select user_id as _uid,
                           max(score) as _best_today,
                           max(foods_eaten) as _foods_today,
                           min(created_at) as _first_at
                    from public.snake_attempts
                    where (created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by user_id
                ) t
                join public.profiles p on p.id = t._uid
                left join public.snake_records r on r.user_id = t._uid
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._foods, sub._games, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.best_foods_eaten as _foods,
                       r.total_games as _games, r.updated_at as _when
                from public.snake_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (
                    select case when user_a = me then user_b else user_a end
                    from public.friendships
                    where (user_a = me or user_b = me) and status = 'accepted'
                    union
                    select me
                )
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.snake_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 2. BURGER
-- =====================================================================
create function public.burger_leaderboard(
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
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._level, sub._games, sub._burgers, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.best_level as _level,
                       r.total_games as _games, r.total_burgers as _burgers,
                       r.updated_at as _when
                from public.burger_records r
                join public.profiles p on p.id = r.user_id
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._level, sub._games, sub._burgers, sub._when
            from (
                select (row_number() over (order by t._best_today desc, t._first_at asc))::int as _rank_pos,
                       t._uid as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score, t._level_today as _level,
                       coalesce(r.total_games, 0) as _games,
                       t._burgers_today::int as _burgers,
                       t._first_at as _when
                from (
                    select user_id as _uid,
                           max(score) as _best_today,
                           max(level_reached) as _level_today,
                           sum(burgers_served) as _burgers_today,
                           min(created_at) as _first_at
                    from public.burger_attempts
                    where (created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by user_id
                ) t
                join public.profiles p on p.id = t._uid
                left join public.burger_records r on r.user_id = t._uid
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._level, sub._games, sub._burgers, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.best_level as _level,
                       r.total_games as _games, r.total_burgers as _burgers,
                       r.updated_at as _when
                from public.burger_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (
                    select case when user_a = me then user_b else user_a end
                    from public.friendships
                    where (user_a = me or user_b = me) and status = 'accepted'
                    union
                    select me
                )
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.burger_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 3. PACMAN
-- =====================================================================
create function public.pacman_leaderboard(
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
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._games, sub._wins, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.total_games as _games,
                       r.total_wins as _wins, r.updated_at as _when
                from public.pacman_records r
                join public.profiles p on p.id = r.user_id
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._games, sub._wins, sub._when
            from (
                select (row_number() over (order by t._best_today desc, t._first_at asc))::int as _rank_pos,
                       t._uid as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score,
                       coalesce(r.total_games, 0) as _games,
                       t._wins_today::int as _wins,
                       t._first_at as _when
                from (
                    select user_id as _uid,
                           max(score) as _best_today,
                           sum(case when won then 1 else 0 end) as _wins_today,
                           min(created_at) as _first_at
                    from public.pacman_attempts
                    where (created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by user_id
                ) t
                join public.profiles p on p.id = t._uid
                left join public.pacman_records r on r.user_id = t._uid
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._games, sub._wins, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.total_games as _games,
                       r.total_wins as _wins, r.updated_at as _when
                from public.pacman_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (
                    select case when user_a = me then user_b else user_a end
                    from public.friendships
                    where (user_a = me or user_b = me) and status = 'accepted'
                    union
                    select me
                )
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.pacman_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 4. DODGE
-- =====================================================================
create function public.dodge_leaderboard(
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
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._games, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.total_games as _games,
                       r.updated_at as _when
                from public.dodge_records r
                join public.profiles p on p.id = r.user_id
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._games, sub._when
            from (
                select (row_number() over (order by t._best_today desc, t._first_at asc))::int as _rank_pos,
                       t._uid as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score,
                       coalesce(r.total_games, 0) as _games,
                       t._first_at as _when
                from (
                    select user_id as _uid,
                           max(score) as _best_today,
                           min(created_at) as _first_at
                    from public.dodge_attempts
                    where (created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by user_id
                ) t
                join public.profiles p on p.id = t._uid
                left join public.dodge_records r on r.user_id = t._uid
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._games, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.total_games as _games,
                       r.updated_at as _when
                from public.dodge_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (
                    select case when user_a = me then user_b else user_a end
                    from public.friendships
                    where (user_a = me or user_b = me) and status = 'accepted'
                    union
                    select me
                )
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.dodge_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 5. TETRIS (Marathon)
-- =====================================================================
create function public.tetris_leaderboard(
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
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._lines, sub._level, sub._games, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.best_lines as _lines,
                       r.best_level as _level, r.total_games as _games,
                       r.updated_at as _when
                from public.tetris_records r
                join public.profiles p on p.id = r.user_id
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._lines, sub._level, sub._games, sub._when
            from (
                select (row_number() over (order by t._best_today desc, t._first_at asc))::int as _rank_pos,
                       t._uid as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score, t._lines_today as _lines,
                       t._level_today as _level,
                       coalesce(r.total_games, 0) as _games, t._first_at as _when
                from (
                    select user_id as _uid,
                           max(score) as _best_today,
                           max(lines_cleared) as _lines_today,
                           max(level_reached) as _level_today,
                           min(created_at) as _first_at
                    from public.tetris_attempts
                    where (created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by user_id
                ) t
                join public.profiles p on p.id = t._uid
                left join public.tetris_records r on r.user_id = t._uid
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._score, sub._lines, sub._level, sub._games, sub._when
            from (
                select (row_number() over (order by r.best_score desc, r.updated_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_score as _score, r.best_lines as _lines,
                       r.best_level as _level, r.total_games as _games,
                       r.updated_at as _when
                from public.tetris_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (
                    select case when user_a = me then user_b else user_a end
                    from public.friendships
                    where (user_a = me or user_b = me) and status = 'accepted'
                    union
                    select me
                )
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.tetris_leaderboard(text, int, int) to authenticated, anon;


-- =====================================================================
-- 6. TETRIS SPRINT (time-based, lower better)
-- =====================================================================
create function public.tetris_sprint_leaderboard(
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
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._dur, sub._completes, sub._when
            from (
                select (row_number() over (order by r.best_duration_ms asc,
                                                    r.achieved_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_duration_ms as _dur,
                       r.total_completes as _completes,
                       r.achieved_at as _when
                from public.tetris_sprint_records r
                join public.profiles p on p.id = r.user_id
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    elsif p_scope = 'today' then
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._dur, sub._completes, sub._when
            from (
                select (row_number() over (order by t._best_today asc,
                                                    t._first_at asc))::int as _rank_pos,
                       t._uid as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _dur,
                       coalesce(r.total_completes, 0) as _completes,
                       t._first_at as _when
                from (
                    select user_id as _uid,
                           min(duration_ms) as _best_today,
                           min(created_at) as _first_at
                    from public.tetris_sprint_attempts
                    where (created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by user_id
                ) t
                join public.profiles p on p.id = t._uid
                left join public.tetris_sprint_records r on r.user_id = t._uid
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    else /* friends */
        return query
            select sub._rank_pos, sub._uid, sub._nick, sub._avatar,
                   sub._dur, sub._completes, sub._when
            from (
                select (row_number() over (order by r.best_duration_ms asc,
                                                    r.achieved_at asc))::int as _rank_pos,
                       r.user_id as _uid, p.nickname as _nick, p.avatar_url as _avatar,
                       r.best_duration_ms as _dur,
                       r.total_completes as _completes,
                       r.achieved_at as _when
                from public.tetris_sprint_records r
                join public.profiles p on p.id = r.user_id
                where r.user_id in (
                    select case when user_a = me then user_b else user_a end
                    from public.friendships
                    where (user_a = me or user_b = me) and status = 'accepted'
                    union
                    select me
                )
            ) sub
            where sub._rank_pos >= p_start_rank
            order by sub._rank_pos
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.tetris_sprint_leaderboard(text, int, int) to authenticated, anon;


-- PostgREST schema cache reload — 새 함수 즉시 callable.
notify pgrst, 'reload schema';
