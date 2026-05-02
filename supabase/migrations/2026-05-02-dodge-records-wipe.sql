-- =====================================================================
-- Migration: Dodge (Space-Z) records wipe — one-time
-- Date:      2026-05-02
-- Purpose:   점수제도 → 시간(time) 기반으로 채점 방식이 바뀐 적이 있어,
--            기존 dodge_attempts / dodge_records 의 score 값이
--            새 채점법(score = floor(duration_ms / 100), 즉 centi-second)
--            과 일관성 없음. 한 번 깨끗하게 비우고 새로 누적되도록.
--
-- 주의:      이 마이그레이션은 1회성. 실행 후 모든 유저의 dodge 기록
--            (이전 attempts + best score 요약) 이 삭제됨. 다른 게임의
--            기록 (tetris, snake, pacman, burger, reaction 등) 은
--            영향 없음.
--
-- 실행 후:   유저들이 다시 플레이하면 자동으로 새 기록이 누적됨.
--            redeploy 없이 SQL 한 번만 실행하면 됨 (테이블 스키마는
--            그대로, 데이터만 비움).
-- =====================================================================

-- attempts 모두 삭제 (개별 시도 기록)
truncate table public.dodge_attempts restart identity;

-- 베스트 기록 요약 모두 삭제
truncate table public.dodge_records;
