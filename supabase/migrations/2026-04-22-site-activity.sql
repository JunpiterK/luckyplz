-- =====================================================================
-- Migration: Site activity log (honest "how busy the site is" counters)
-- Date:      2026-04-22
-- Purpose:   Cheap activity log so the home page can honestly render
--            "⚡ 오늘 N번 · 누적 M번" — real social-proof numbers that
--            grow organically as traffic grows.
--
--            One row = one game page open (deduped to at most once per
--            5 minutes per device via localStorage on the client — the
--            server doesn't try to dedupe because rate-limiting here
--            would punish legitimate bursts and the home page is happy
--            with a slightly noisy total).
-- =====================================================================

create table if not exists public.game_plays (
    id         bigserial   primary key,
    game_id    text        not null check (length(game_id) between 1 and 32),
    user_id    uuid        references auth.users(id) on delete set null,
    created_at timestamptz not null default now()
);
create index if not exists game_plays_created_idx on public.game_plays (created_at desc);
create index if not exists game_plays_game_created_idx on public.game_plays (game_id, created_at desc);

alter table public.game_plays enable row level security;
drop policy if exists "game_plays_select_all" on public.game_plays;
create policy "game_plays_select_all"
    on public.game_plays for select using (true);


-- RPC: log one play. Anon-callable because the home activity counter
-- is a SITE-WIDE stat that would be useless if only logged-in users
-- contributed. Server-side rate limit: at most 120 logs per HOUR per
-- authenticated user (anon users rely on the client's 5-min per-device
-- dedupe — adding a per-IP cap would need the gateway to forward IP,
-- which Supabase's stock set-up doesn't by default).
create or replace function public.log_game_play(p_game_id text)
returns void
language plpgsql security definer
set search_path = public
as $$
declare me uuid := auth.uid();
        recent_count int;
begin
    if p_game_id is null or length(p_game_id) > 32 then return; end if;
    /* Accept only known game ids so a bad actor can't pollute the log
       with arbitrary strings. Kept as a literal IN list because the
       games list changes rarely and this is cheaper than a lookup. */
    if p_game_id not in ('roulette','ladder','car-racing','team','lotto',
                         'bingo','dice','snake','pacman','burger') then
        return;
    end if;
    if me is not null then
        select count(*) into recent_count
          from public.game_plays
         where user_id = me and created_at > now() - interval '1 hour';
        if recent_count >= 120 then return; end if;
    end if;
    insert into public.game_plays (game_id, user_id) values (p_game_id, me);
end;
$$;
grant execute on function public.log_game_play(text) to anon, authenticated;


-- RPC: site-wide stats for the home-page activity strip. Returns
-- today's count (Asia/Seoul day boundary, same as every other
-- "today" scope on the site) + cumulative total. Per-game breakdown
-- is included as a jsonb object so the home page CAN show a bar
-- chart later without another round-trip.
create or replace function public.site_activity_stats()
returns jsonb
language plpgsql security definer
set search_path = public
as $$
declare today_count bigint;
        total_count bigint;
        by_game     jsonb;
begin
    select count(*) into today_count
      from public.game_plays
     where (created_at at time zone 'Asia/Seoul')::date
         = (now() at time zone 'Asia/Seoul')::date;
    select count(*) into total_count from public.game_plays;
    select coalesce(jsonb_object_agg(game_id, cnt), '{}'::jsonb) into by_game
      from (
          select game_id, count(*)::bigint as cnt
            from public.game_plays
           group by game_id
      ) t;
    return jsonb_build_object(
        'today',   today_count,
        'total',   total_count,
        'by_game', by_game,
        'tz',      'Asia/Seoul'
    );
end;
$$;
grant execute on function public.site_activity_stats() to anon, authenticated;
