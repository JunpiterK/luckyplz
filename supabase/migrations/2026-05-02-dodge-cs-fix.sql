-- =====================================================================
-- Migration: Dodge (Space-Z) score 단위 cs 로 통일 + 재 wipe
-- Date:      2026-05-02
-- =====================================================================
-- 진짜 버그 발견:
--   서버 RPC record_dodge_attempt 가 score = floor(p_duration_ms/100)
--   = deci-seconds (1ds = 100ms) 단위로 저장.
--   하지만 클라이언트 formatTime(score) 는 score 를 centi-seconds
--   (1cs = 10ms) 로 가정하고 표시 (mm:ss:cs).
--   → 10초 게임 → 서버 score=100 → 클라이언트 표시 "0:01:00" (1초)
--   → 사용자가 본 실제 시간과 leaderboard 표시 안 맞음.
--
-- 해결: 서버 score 를 cs 단위로 통일 (ms/10). 클라이언트 코드는 그대로.
--   · 10초 게임 → server stores 1000 → formatTime(1000) → "0:10:00" ✓
--   · 720초 hard cap = 72000 cs (이전 7200ds 과 동일 의미)
--   · score column constraint 도 확장 (10000초 = 1,000,000 cs 까지 허용)
--
-- 재 wipe 포함: 이전 commit 의 wipe 후 일부 ds 값으로 저장된 기록이
-- 있을 수 있어 다시 비움. 새 RPC 적용 후 깨끗한 상태로 시작.
-- =====================================================================

-- 1. 기록 다시 wipe (이전 ds 값들이 cs interpretation 과 안 맞음)
truncate table public.dodge_attempts restart identity;
truncate table public.dodge_records;

-- 2. score column 의 max constraint 확장 (cs 로 변경 시 값 10x 커짐)
alter table public.dodge_attempts drop constraint if exists dodge_attempts_score_check;
alter table public.dodge_attempts add constraint dodge_attempts_score_check
    check (score >= 0 and score <= 1000000);

-- 3. record_dodge_attempt RPC 업데이트 — score 를 cs (ms/10) 로 저장
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

    -- ★ score 단위 = centi-seconds (1cs = 10ms)
    --   기존 ds (ms/100) → 새 cs (ms/10). 클라이언트 formatTime 와 일치.
    calc_score := floor(p_duration_ms / 10);

    -- 720초 hard cap (anti-cheat) = 72000 cs
    if calc_score > 72000 then raise exception 'impossible_score'; end if;

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

-- 4. PostgREST 스키마 캐시 reload (새 RPC 즉시 callable)
notify pgrst, 'reload schema';
