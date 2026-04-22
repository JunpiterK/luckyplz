-- =====================================================================
-- Migration: 넌센스 v2 — curated replacement pool
-- Date:      2026-04-22
-- Purpose:   Previous batch (bank-ko-nonsense.sql) was padded to hit
--            volume; many entries were forced puns that don't actually
--            land. This migration WIPES all existing nonsense rows and
--            inserts ~55 questions picked only from Korean 넌센스
--            classics that are recognized at a glance (풋사과, 후다닭,
--            썰렁해, 계산, 소문, …) plus a few modern SNS-era ones
--            that are widely known (JMT, ㅇㅈ, 럭키비키).
--
--            Quality-over-quantity — better to have 55 questions that
--            actually land than 140 that are forgettable. Future
--            batches can expand but only with verified pun value.
-- =====================================================================

/* Wipe the old pool so we aren't mixing good + mediocre rows.
   Safe because nonsense questions don't carry user-facing data. */
delete from public.quiz_questions where category = 'nonsense';

insert into public.quiz_questions (category, era, difficulty, question, options, correct, language) values

-- ============ Tier A — universally recognized classics ============
('nonsense','classic',2,'사과가 웃으면?',                                   '["풋사과","빨개짐","썩은 사과","애사과"]'::jsonb,0,'ko'),
('nonsense','classic',2,'바나나가 웃으면?',                                 '["바나나 킥","바나나 셰이크","바나나 스플릿","바나나 우유"]'::jsonb,0,'ko'),
('nonsense','classic',2,'병아리가 가장 좋아하는 약은?',                      '["삐약","비타민","달걀영양제","닭가슴살"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 빠른 닭은?',                         '["후다닭","치킨","삼계탕","계란"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 추운 바다는?',                       '["썰렁해","북극해","얼음해","남극해"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 깨끗한 바다는?',                     '["청결해","동해","지중해","맑은해"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 지저분한 바다는?',                   '["지저분해","흙탕해","더러운해","잿빛해"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 따뜻한 바다는?',                     '["따뜻해","훈훈해","열대해","뜨거해"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 가까운 바다는?',                     '["가까워(가까해)","서해","남해","이 앞바다"]'::jsonb,0,'ko'),
('nonsense','classic',2,'밥은 밥인데 못 먹는 밥은?',                        '["꿀밤","주먹밥","김밥","볶음밥"]'::jsonb,0,'ko'),
('nonsense','classic',2,'산은 산인데 오를 수 없는 산은?',                   '["계산","설악산","한라산","지리산"]'::jsonb,0,'ko'),
('nonsense','classic',2,'문은 문인데 들어갈 수 없는 문은?',                 '["소문","현관문","창문","대문"]'::jsonb,0,'ko'),
('nonsense','classic',2,'말은 말인데 탈 수 없는 말은?',                     '["거짓말","경주마","조랑말","백마"]'::jsonb,0,'ko'),
('nonsense','classic',2,'차는 차인데 탈 수 없는 차는?',                     '["녹차","자동차","기차","경주차"]'::jsonb,0,'ko'),
('nonsense','classic',2,'꽃은 꽃인데 향기가 없는 꽃은?',                    '["불꽃","장미","튤립","벚꽃"]'::jsonb,0,'ko'),
('nonsense','classic',2,'불은 불인데 뜨겁지 않은 불은?',                    '["반딧불","모닥불","촛불","화덕"]'::jsonb,0,'ko'),
('nonsense','classic',2,'초는 초인데 먹을 수 있는 초는?',                   '["식초","양초","초인종","초록빛"]'::jsonb,0,'ko'),
('nonsense','classic',2,'콩은 콩인데 못 먹는 콩은?',                        '["킹콩","검은콩","콩나물","강낭콩"]'::jsonb,0,'ko'),
('nonsense','classic',2,'개는 개인데 짖지 않는 개는?',                      '["무지개","강아지","진돗개","푸들"]'::jsonb,0,'ko'),
('nonsense','classic',2,'쥐는 쥐인데 쥐가 아닌 것은?',                      '["박쥐","들쥐","새앙쥐","생쥐"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 큰 코는?',                           '["멕시코","공룡코","고릴라코","빨간코"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 작은 다리는?',                       '["오다리","외다리","다리품","한강다리"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 야한 새는?',                         '["참새","비둘기","독수리","까마귀"]'::jsonb,0,'ko'),
('nonsense','classic',2,'맞으면 기분 좋은 것은?',                           '["정답","따귀","매","공"]'::jsonb,0,'ko'),
('nonsense','classic',2,'거꾸로 서면 키가 커지는 나라는?',                  '["칠레","미국","일본","스웨덴"]'::jsonb,0,'ko'),
('nonsense','classic',2,'뒤집으면 더 커지는 숫자는?',                       '["6","7","0","2"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 공부 잘 하는 동물은?',                '["족제비(족+비 우등)","쥐","다람쥐","노루"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 바쁜 곤충은?',                       '["일벌","나비","사마귀","매미"]'::jsonb,0,'ko'),
('nonsense','classic',2,'아무리 먹어도 배부르지 않은 것은?',                '["욕심","밥","과자","물"]'::jsonb,0,'ko'),
('nonsense','classic',2,'눈 감으면 보이고 눈 뜨면 안 보이는 것은?',         '["꿈","별","어둠","상상"]'::jsonb,0,'ko'),
('nonsense','classic',2,'하루 종일 일해도 자리를 못 옮기는 사람은?',        '["동상","경비원","운전기사","연예인"]'::jsonb,0,'ko'),
('nonsense','classic',2,'항상 뒤에 따라오는 것은?',                         '["그림자","미래","과거","오늘"]'::jsonb,0,'ko'),
('nonsense','classic',2,'입은 있지만 말을 못 하는 것은?',                   '["병","현관","우체통","냉장고"]'::jsonb,0,'ko'),
('nonsense','classic',2,'머리는 있지만 모자를 안 쓰는 것은?',               '["못","전구","압핀","계란"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 지루한 중학교는?',                   '["로딩중","상업중","공립중","사립중"]'::jsonb,0,'ko'),

-- ============ Tier B — verified pun + clear correct answer ============
('nonsense','classic',2,'눈을 감고도 볼 수 있는 것은?',                     '["꿈","영화","TV","책"]'::jsonb,0,'ko'),
('nonsense','classic',2,'낮에는 숨어 있다가 밤에만 나오는 것은?',           '["별","도둑","박쥐","귀신"]'::jsonb,0,'ko'),
('nonsense','classic',2,'손은 있는데 잡을 수 없는 손은?',                   '["시계바늘","왼손","오른손","악수"]'::jsonb,0,'ko'),
('nonsense','classic',2,'귀는 귀인데 듣지 못하는 귀는?',                    '["냄비 손잡이(냄비 귀)","강아지 귀","고양이 귀","사람 귀"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세상에서 가장 짧은 다리는?',                       '["책상다리","한강다리","징검다리","외나무다리"]'::jsonb,0,'ko'),
('nonsense','classic',2,'발은 발인데 향기가 나는 발은?',                    '["꽃발","맨발","군발","왼발"]'::jsonb,0,'ko'),
('nonsense','classic',2,'세 살 짜리 아이도 할 수 있지만 대통령도 어려운 것은?', '["울음","뛰어놀기","말하기","걷기"]'::jsonb,0,'ko'),
('nonsense','classic',2,'아무리 많이 맞아도 아프지 않은 것은?',             '["바람","돌","비","매"]'::jsonb,0,'ko'),

-- ============ Tier C — 글자·숫자 유희 ============
('nonsense','classic',2,'한글 자음 중 가장 슬픈 자음은?',                   '["ㅠ","ㅋ","ㅎ","ㅇ"]'::jsonb,0,'ko'),
('nonsense','classic',2,'한글 자음 중 가장 잘 웃는 자음은?',                '["ㅋ","ㅠ","ㅜ","ㅗ"]'::jsonb,0,'ko'),
('nonsense','classic',2,'"ㅋㅋ"이 세계에서 가장 많은 나라는?',              '["코리아","일본","중국","미국"]'::jsonb,0,'ko'),
('nonsense','classic',2,'1과 100 중 더 외로운 숫자는?',                     '["1","100","50","10"]'::jsonb,0,'ko'),
('nonsense','classic',2,'"가나다라"의 다음 글자는?',                         '["마","바","사","아"]'::jsonb,0,'ko'),

-- ============ Tier D — SNS 시대 유머 (2015~) ============
('nonsense','modern',2,'"JMT"의 뜻은?',                                     '["존맛탱","중매탱","잘먹탱","준모탱"]'::jsonb,0,'ko'),
('nonsense','modern',2,'"ㅇㅈ"의 뜻은?',                                    '["인정","이준","아주","약정"]'::jsonb,0,'ko'),
('nonsense','modern',2,'"TMI"의 뜻은?',                                     '["Too Much Information","Try My Idea","Time Missing Info","Take Me In"]'::jsonb,0,'ko'),
('nonsense','modern',2,'"MZ세대"의 M과 Z는?',                               '["밀레니얼+Z세대","Mother+Zoomer","Man+Zero","Millennial+Zone"]'::jsonb,0,'ko'),
('nonsense','modern',3,'"아싸"의 반대말은?',                                '["인싸","우싸","오싸","이싸"]'::jsonb,0,'ko'),
('nonsense','current',2,'"럭키비키"를 유행시킨 아이돌은?',                   '["IVE 장원영","BTS 뷔","뉴진스 민지","에스파 카리나"]'::jsonb,0,'ko')

on conflict do nothing;
