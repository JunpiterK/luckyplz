-- =====================================================================
-- Migration: Tetris game (record-keeping action game #5)
-- Date:      2026-04-30
-- Purpose:   Classic Tetris — 10x20 board, 7 standard pieces (I/O/T/S/Z/J/L),
--            SRS rotation, line clears with bonus scoring (Tetris = 4 lines
--            at once = bonus). Session score, best per user, three-scope
--            leaderboards (world / today / friends).
--
-- Same SECURITY DEFINER RPC pattern as snake / pacman / burger / dodge
-- (see memory/messaging_rpc_pattern.md). Every read goes through an
-- RPC so mobile WebView RLS quirks never bite.
--
-- Scoring (standard NES/Modern Tetris):
--   single line  =   40 × (level + 1)
--   double       =  100 × (level + 1)
--   triple       =  300 × (level + 1)
--   tetris (4)   = 1200 × (level + 1)
--   soft drop    = 1 per cell
--   hard drop    = 2 per cell
-- Score cap (10M) chosen with huge margin — even a perfect Tetris-only
-- run for 10 minutes lands well below.
-- =====================================================================

create table if not exists public.tetris_attempts (
    id             bigserial   primary key,
    user_id        uuid        not null references auth.users(id) on delete cascade,
    score          int         not null check (score >= 0 and score <= 10000000),
    lines_cleared  int         not null check (lines_cleared >= 0 and lines_cleared <= 100000),
    level_reached  int         not null check (level_reached >= 0 and level_reached <= 100),
    duration_ms    int         not null check (duration_ms between 0 and 7200000),
    created_at     timestamptz not null default now()
);

create index if not exists tetris_attempts_user_idx
    on public.tetris_attempts (user_id, created_at desc);
create index if not exists tetris_attempts_score_idx
    on public.tetris_attempts (score desc);

alter table public.tetris_attempts enable row level security;
drop policy if exists "tetris_attempts_select_all" on public.tetris_attempts;
create policy "tetris_attempts_select_all"
    on public.tetris_attempts for select using (true);


create table if not exists public.tetris_records (
    user_id           uuid        primary key references auth.users(id) on delete cascade,
    best_score        int         not null,
    best_lines        int,
    best_level        int,
    total_games       int         not null default 0,
    total_lines       bigint      not null default 0,
    total_playtime_ms bigint      not null default 0,
    updated_at        timestamptz not null default now()
);

create index if not exists tetris_records_best_idx on public.tetris_records (best_score desc);

alter table public.tetris_records enable row level security;
drop policy if exists "tetris_records_select_all" on public.tetris_records;
create policy "tetris_records_select_all"
    on public.tetris_records for select using (true);


-- Trigger: maintain the per-user summary after each attempt.
create or replace function public._tetris_refresh_record()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
    insert into public.tetris_records (user_id, best_score, best_lines, best_level,
                                       total_games, total_lines, total_playtime_ms, updated_at)
    values (new.user_id, new.score, new.lines_cleared, new.level_reached,
            1, new.lines_cleared, new.duration_ms, now())
    on conflict (user_id) do update
      set best_score        = greatest(public.tetris_records.best_score, new.score),
          best_lines        = case when new.score > public.tetris_records.best_score
                                   then new.lines_cleared
                                   else public.tetris_records.best_lines end,
          best_level        = case when new.score > public.tetris_records.best_score
                                   then new.level_reached
                                   else public.tetris_records.best_level end,
          total_games       = public.tetris_records.total_games + 1,
          total_lines       = public.tetris_records.total_lines + new.lines_cleared,
          total_playtime_ms = public.tetris_records.total_playtime_ms + new.duration_ms,
          updated_at        = now();
    return new;
end;
$$;
drop trigger if exists tetris_refresh_record on public.tetris_attempts;
create trigger tetris_refresh_record
    after insert on public.tetris_attempts
    for each row execute function public._tetris_refresh_record();


-- RPC: record a finished game. Server-side anti-cheat:
--   * lines_cleared <= 100000 (impossible-board cap)
--   * duration_ms must allow at least 200ms per line cleared
--     (a perfect Tetris-only run at level 29 still needs >200ms/line
--      for piece spawn + lock animations; lower bound is generous)
--   * 30 attempts per hour per user.
create or replace function public.record_tetris_attempt(
    p_score int, p_lines int, p_level int, p_duration_ms int
) returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        prior_best int;
        recent_count int;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    if p_score < 0 or p_score > 10000000 then raise exception 'bad_score'; end if;
    if p_lines < 0 or p_lines > 100000 then raise exception 'bad_lines'; end if;
    if p_level < 0 or p_level > 100 then raise exception 'bad_level'; end if;
    if p_duration_ms < 0 or p_duration_ms > 7200000 then raise exception 'bad_duration'; end if;
    /* Anti-cheat: minimum 200ms per cleared line. A bot claiming
       100 lines in 1 second is rejected. Real human play averages
       much higher (~2s per line in early levels). */
    if p_lines > 0 and p_duration_ms < p_lines * 200 then
        raise exception 'impossible_pace';
    end if;
    /* Anti-cheat: score must be in plausible range for the lines
       claimed. Max possible score per line = 1200 × (max_level+1) =
       1200 × 30 = 36000. Plus generous slack for soft/hard drop
       points. Cap at lines × 50000 as outer bound. */
    if p_lines > 0 and p_score > p_lines * 50000 then
        raise exception 'score_lines_mismatch';
    end if;

    select count(*) into recent_count
      from public.tetris_attempts
     where user_id = me and created_at > now() - interval '1 hour';
    if recent_count >= 30 then raise exception 'rate_limited'; end if;

    select best_score into prior_best from public.tetris_records where user_id = me;

    insert into public.tetris_attempts (user_id, score, lines_cleared, level_reached, duration_ms)
    values (me, p_score, p_lines, p_level, p_duration_ms);

    return jsonb_build_object(
        'ok', true,
        'score', p_score,
        'is_personal_best', prior_best is null or p_score > prior_best,
        'prior_best', coalesce(prior_best, 0)
    );
end;
$$;
grant execute on function public.record_tetris_attempt(int, int, int, int) to authenticated;


-- RPC: leaderboard with three scopes (world / today / friends).
create or replace function public.tetris_leaderboard(
    p_scope text default 'world',
    p_limit int   default 50
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

    if p_scope = 'world' then
        return query
            select (row_number() over (order by r.best_score desc, r.updated_at asc))::int,
                   r.user_id, p.nickname, p.avatar_url,
                   r.best_score, r.best_lines, r.best_level, r.total_games, r.updated_at
            from public.tetris_records r
            join public.profiles p on p.id = r.user_id
            order by r.best_score desc, r.updated_at asc
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
            )
            select (row_number() over (order by t.best_today desc, t.first_at asc))::int,
                   t.user_id, p.nickname, p.avatar_url,
                   t.best_today, t.lines_today, t.level_today,
                   coalesce(r.total_games, 0), t.first_at
            from today_attempts t
            join public.profiles p on p.id = t.user_id
            left join public.tetris_records r on r.user_id = t.user_id
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
                   r.best_score, r.best_lines, r.best_level, r.total_games, r.updated_at
            from public.tetris_records r
            join public.profiles p on p.id = r.user_id
            where r.user_id in (select fid from friend_ids)
            order by r.best_score desc, r.updated_at asc
            limit greatest(1, least(p_limit, 100));
    end if;
end;
$$;
grant execute on function public.tetris_leaderboard(text, int) to authenticated, anon;


-- RPC: bundled personal stats for the game page open.
create or replace function public.tetris_my_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        rec public.tetris_records%rowtype;
        rank_world int;
        recents jsonb;
begin
    if me is null then raise exception 'not_authenticated'; end if;
    select * into rec from public.tetris_records where user_id = me;
    if not found then return jsonb_build_object('has_record', false); end if;

    select 1 + count(*) into rank_world
      from public.tetris_records
     where best_score > rec.best_score;

    select jsonb_agg(x order by created_at desc) into recents
    from (
        select score, lines_cleared, level_reached, duration_ms, created_at
        from public.tetris_attempts
        where user_id = me
        order by created_at desc
        limit 10
    ) x;

    return jsonb_build_object(
        'has_record', true,
        'best_score', rec.best_score,
        'best_lines', rec.best_lines,
        'best_level', rec.best_level,
        'total_games', rec.total_games,
        'total_lines', rec.total_lines,
        'total_playtime_ms', rec.total_playtime_ms,
        'world_rank', rank_world,
        'recent_attempts', coalesce(recents, '[]'::jsonb)
    );
end;
$$;
grant execute on function public.tetris_my_stats() to authenticated;

-- Refresh PostgREST cache so new RPCs become callable immediately.
notify pgrst, 'reload schema';
