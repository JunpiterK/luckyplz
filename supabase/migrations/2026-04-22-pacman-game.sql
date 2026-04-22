-- =====================================================================
-- Migration: Pac-Man game (record-keeping skill game #3)
-- Date:      2026-04-22
-- Purpose:   Classic-inspired maze game. Player eats dots, avoids two
--            ghosts, power pellets make ghosts vulnerable for a few
--            seconds. Score = dots + ghost-eats. Die on ghost hit.
--
-- Same SECURITY DEFINER RPC pattern — see messaging_rpc_pattern.md.
-- =====================================================================

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
