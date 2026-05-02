-- =====================================================================
-- Migration: Drop old 2-arg leaderboard RPC signatures
-- Date:      2026-05-02
-- Purpose:   2026-05-02-leaderboard-pagination-fix.sql 적용 후에도
--            "오늘" scope 호출 시 ambiguous rnk 에러가 계속 뜨는 이슈.
--
-- 진짜 원인: PostgreSQL 의 function overloading.
--            CREATE OR REPLACE FUNCTION tetris_leaderboard(text, int, int)
--            는 *새로운 signature* 함수를 추가만 함. 기존 (text, int)
--            2-arg 버전은 그대로 남아있음. PostgREST 가 호출 시 2 args
--            를 보내면 OLD 깨진 버전을 routing → 에러.
--
--            World scope 도 새 윈도우 (3-arg 호출) 에선 fix 가
--            적용되지만 게임별 bottom sheet (2-arg 호출) 에선 여전히
--            old 깨진 버전 사용 중. 사용자가 새 rank 윈도우 today 만
--            테스트했을 때 "오늘" 만 깨져 보였던 이유.
--
-- 해결: 6 RPC 의 old 2-arg signature 명시적 DROP.
--       남은 3-arg 버전이 default p_start_rank=1 를 갖고 있어 모든
--       호출 (2 args / 3 args) 을 unified 처리.
-- =====================================================================

drop function if exists public.snake_leaderboard(text, int);
drop function if exists public.burger_leaderboard(text, int);
drop function if exists public.pacman_leaderboard(text, int);
drop function if exists public.dodge_leaderboard(text, int);
drop function if exists public.tetris_leaderboard(text, int);
drop function if exists public.tetris_sprint_leaderboard(text, int);

-- PostgREST schema cache reload — 사라진 signature 가 캐시에서 제거.
notify pgrst, 'reload schema';
