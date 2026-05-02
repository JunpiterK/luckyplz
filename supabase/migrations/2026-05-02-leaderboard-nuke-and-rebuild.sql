-- =====================================================================
-- Migration: Leaderboard NUKE & REBUILD (final aggressive fix)
-- Date:      2026-05-02
-- Purpose:   직전 3개 fix migration 후에도 today scope 에러 지속
--            → DO block 으로 *모든* signature 동적 제거 후 새로 작성.
--
-- 진단 가능 시나리오:
--   (a) 직전 migration 이 실제로 적용 안 됐음 (사용자 dashboard 에서
--       SQL 실행 시 syntax/permission 등으로 silent 실패 가능)
--   (b) 알 수 없는 다른 signature variant 가 db 에 잔존
--   (c) PostgREST schema cache 가 reload notify 받았는데도 stale
--
-- 이 migration 은 (a),(b) 에 모두 대응:
--   1. DO block 으로 pg_proc 조회 → public schema 의 *_leaderboard 함수
--      모두 동적 DROP (signature 무관). 잔존 broken 버전 100% 제거.
--   2. 6 RPC 새로 작성 — subquery + underscore-prefix column.
--   3. 끝에 SELECT 로 결과 확인 (어떤 함수가 deployed 됐는지).
--
-- ⚠️ 사용자: 이 migration 만 실행하면 됨 (이전 fix migration 들 안 돌
--   려도 됨). self-contained.
-- =====================================================================

-- ---- Step 1: pg_proc 조회해서 *_leaderboard 모든 signature DROP ----
do $$
declare
    r record;
begin
    for r in
        select n.nspname as schema_name,
               p.proname as func_name,
               pg_get_function_identity_arguments(p.oid) as args
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public'
          and p.proname in (
              'snake_leaderboard',
              'burger_leaderboard',
              'pacman_leaderboard',
              'dodge_leaderboard',
              'tetris_leaderboard',
              'tetris_sprint_leaderboard'
          )
    loop
        execute format('drop function if exists public.%I(%s)',
                       r.func_name, r.args);
        raise notice 'Dropped: public.%(%)', r.func_name, r.args;
    end loop;
end $$;


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
#variable_conflict use_column
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
                       t._uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score, t._foods_today as _foods,
                       coalesce(r.total_games, 0) as _games, t._first_at as _when
                from (
                    select a.user_id as _uid,
                           max(a.score) as _best_today,
                           max(a.foods_eaten) as _foods_today,
                           min(a.created_at) as _first_at
                    from public.snake_attempts a
                    where (a.created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by a.user_id
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
                    select case when f.user_a = me then f.user_b else f.user_a end
                    from public.friendships f
                    where (f.user_a = me or f.user_b = me) and f.status = 'accepted'
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
#variable_conflict use_column
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
                       t._uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score, t._level_today as _level,
                       coalesce(r.total_games, 0) as _games,
                       t._burgers_today::int as _burgers,
                       t._first_at as _when
                from (
                    select a.user_id as _uid,
                           max(a.score) as _best_today,
                           max(a.level_reached) as _level_today,
                           sum(a.burgers_served) as _burgers_today,
                           min(a.created_at) as _first_at
                    from public.burger_attempts a
                    where (a.created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by a.user_id
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
                    select case when f.user_a = me then f.user_b else f.user_a end
                    from public.friendships f
                    where (f.user_a = me or f.user_b = me) and f.status = 'accepted'
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
#variable_conflict use_column
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
                       t._uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score,
                       coalesce(r.total_games, 0) as _games,
                       t._wins_today::int as _wins,
                       t._first_at as _when
                from (
                    select a.user_id as _uid,
                           max(a.score) as _best_today,
                           sum(case when a.won then 1 else 0 end) as _wins_today,
                           min(a.created_at) as _first_at
                    from public.pacman_attempts a
                    where (a.created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by a.user_id
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
                    select case when f.user_a = me then f.user_b else f.user_a end
                    from public.friendships f
                    where (f.user_a = me or f.user_b = me) and f.status = 'accepted'
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
#variable_conflict use_column
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
                       t._uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score,
                       coalesce(r.total_games, 0) as _games,
                       t._first_at as _when
                from (
                    select a.user_id as _uid,
                           max(a.score) as _best_today,
                           min(a.created_at) as _first_at
                    from public.dodge_attempts a
                    where (a.created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by a.user_id
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
                    select case when f.user_a = me then f.user_b else f.user_a end
                    from public.friendships f
                    where (f.user_a = me or f.user_b = me) and f.status = 'accepted'
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
#variable_conflict use_column
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
                       t._uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _score, t._lines_today as _lines,
                       t._level_today as _level,
                       coalesce(r.total_games, 0) as _games, t._first_at as _when
                from (
                    select a.user_id as _uid,
                           max(a.score) as _best_today,
                           max(a.lines_cleared) as _lines_today,
                           max(a.level_reached) as _level_today,
                           min(a.created_at) as _first_at
                    from public.tetris_attempts a
                    where (a.created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by a.user_id
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
                    select case when f.user_a = me then f.user_b else f.user_a end
                    from public.friendships f
                    where (f.user_a = me or f.user_b = me) and f.status = 'accepted'
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
#variable_conflict use_column
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
                       t._uid, p.nickname as _nick, p.avatar_url as _avatar,
                       t._best_today as _dur,
                       coalesce(r.total_completes, 0) as _completes,
                       t._first_at as _when
                from (
                    select a.user_id as _uid,
                           min(a.duration_ms) as _best_today,
                           min(a.created_at) as _first_at
                    from public.tetris_sprint_attempts a
                    where (a.created_at at time zone 'Asia/Seoul')::date
                        = (now() at time zone 'Asia/Seoul')::date
                    group by a.user_id
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
                    select case when f.user_a = me then f.user_b else f.user_a end
                    from public.friendships f
                    where (f.user_a = me or f.user_b = me) and f.status = 'accepted'
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


-- ---- Step 3: Verification — 어떤 함수가 deployed 됐는지 확인 ----
-- Supabase SQL Editor 가 마지막 SELECT 결과를 보여줌 → 6 함수가 모두
-- (text,int,int) signature 로만 등록됐는지 확인 가능.
select n.nspname as schema,
       p.proname as func,
       pg_get_function_identity_arguments(p.oid) as args
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in (
      'snake_leaderboard', 'burger_leaderboard', 'pacman_leaderboard',
      'dodge_leaderboard', 'tetris_leaderboard', 'tetris_sprint_leaderboard'
  )
order by p.proname, args;


-- PostgREST schema cache reload — 새 signature 즉시 callable.
notify pgrst, 'reload schema';
