-- =====================================================================
-- Migration: rank_info RPCs for action games (world rank + percentile)
-- Date:      2026-04-26
-- Purpose:   Expose a small RPC per action game that returns the
--            caller's world rank, total world players, and percentile
--            (top X%). Called from the game-over overlay so the player
--            sees their global standing immediately after every match.
--
-- Why a new RPC instead of extending each *_my_stats(): keeps the
-- existing my_stats schema untouched (other UI panels rely on it),
-- and the rank panel needs only 3 fields, so a tiny dedicated RPC is
-- cheaper to call (single round-trip during the post-game RPC chain).
--
-- Same SECURITY DEFINER pattern as the rest of the game RPCs — see
-- memory/messaging_rpc_pattern.md for why every read goes through an
-- RPC (mobile WebView RLS quirks).
-- =====================================================================

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
