-- =====================================================================
-- Migration: Quiz bank — English starter pack (~50 questions)
-- Date:      2026-04-22
-- Purpose:   Seed an initial English-language question set so Live
--            Quiz has something to serve on the 🇺🇸/🇬🇧 region.
--            Covers the same 8 categories as Korean: kpop (global-
--            recognizable acts only), variety (Hollywood + streaming),
--            sports (global), general, retro (80s/90s US), history
--            (world history framed for English speakers), world,
--            latest.
--
--            Depends on 2026-04-22-quiz-locales.sql having run first
--            (needs the `language` column). Uses `on conflict do
--            nothing` so re-running is safe.
-- =====================================================================

insert into public.quiz_questions (category, era, difficulty, question, options, correct, language) values

-- ====================== K-POP (globally known acts) ======================
('kpop','modern',2,'Which K-pop group performed "Gangnam Style"?',                       '["PSY (solo)","Big Bang","BTS","Super Junior"]'::jsonb,0,'en'),
('kpop','modern',2,'What is BTS''s fandom name?',                                          '["ARMY","BLINK","ONCE","ELF"]'::jsonb,0,'en'),
('kpop','modern',3,'Which K-pop group released "How You Like That" in 2020?',             '["BLACKPINK","TWICE","ITZY","Red Velvet"]'::jsonb,0,'en'),
('kpop','modern',3,'BTS''s leader is?',                                                    '["Jin","RM","J-Hope","Suga"]'::jsonb,1,'en'),
('kpop','current',3,'Which group released "Super Shy" in 2023?',                          '["NewJeans","IVE","aespa","LE SSERAFIM"]'::jsonb,0,'en'),
('kpop','current',3,'aespa''s member Karina''s real name is?',                             '["Yoo Jimin","Kim Minjeong","Ning Yizhuo","Giselle Aubrey"]'::jsonb,0,'en'),
('kpop','current',4,'Which company manages NewJeans (ADOR)?',                             '["SM","JYP","YG","HYBE"]'::jsonb,3,'en'),
('kpop','modern',3,'TWICE debuted in which year?',                                        '["2013","2014","2015","2016"]'::jsonb,2,'en'),

-- ====================== VARIETY / FILM / TV ======================
('variety','modern',2,'Which streaming service released "Stranger Things"?',              '["Netflix","Disney+","HBO Max","Prime Video"]'::jsonb,0,'en'),
('variety','modern',3,'Who directed "Inception" (2010)?',                                 '["Christopher Nolan","Steven Spielberg","Ridley Scott","Denis Villeneuve"]'::jsonb,0,'en'),
('variety','modern',3,'Which film won Best Picture at the 2020 Oscars?',                  '["Parasite","1917","Joker","Once Upon a Time in Hollywood"]'::jsonb,0,'en'),
('variety','modern',3,'Who plays Tony Stark / Iron Man in the MCU?',                      '["Chris Evans","Robert Downey Jr.","Chris Hemsworth","Mark Ruffalo"]'::jsonb,1,'en'),
('variety','current',3,'"The Last of Us" TV series airs on which network?',              '["HBO","Netflix","Disney+","Apple TV+"]'::jsonb,0,'en'),
('variety','current',3,'"House of the Dragon" is a prequel to which show?',               '["The Witcher","Game of Thrones","The Walking Dead","Westworld"]'::jsonb,1,'en'),
('variety','modern',4,'Which Pixar film features a chef rat named Remy?',                 '["WALL-E","Ratatouille","Up","Coco"]'::jsonb,1,'en'),
('variety','current',3,'Which film was the highest-grossing of 2023 worldwide?',          '["Barbie","Oppenheimer","The Super Mario Bros. Movie","Avatar 2"]'::jsonb,0,'en'),

-- ====================== SPORTS ======================
('sports','classic',2,'Lionel Messi is from which country?',                              '["Argentina","Brazil","Spain","Portugal"]'::jsonb,0,'en'),
('sports','modern',2,'LeBron James plays in which sport?',                                '["Football","Basketball","Baseball","Soccer"]'::jsonb,1,'en'),
('sports','modern',3,'Which team did Cristiano Ronaldo win the UEFA Champions League with 5 times?',  '["Real Madrid","Manchester United","Juventus","Sporting"]'::jsonb,0,'en'),
('sports','classic',3,'Michael Jordan wore which jersey number for the Chicago Bulls?',   '["23","33","45","24"]'::jsonb,0,'en'),
('sports','modern',3,'Who won the 2022 FIFA World Cup?',                                  '["France","Argentina","Brazil","Germany"]'::jsonb,1,'en'),
('sports','classic',3,'How many players are on a soccer team (on the field)?',            '["9","10","11","12"]'::jsonb,2,'en'),
('sports','current',3,'Which country hosted the 2024 Summer Olympics?',                   '["Japan","France","Brazil","USA"]'::jsonb,1,'en'),

-- ====================== GENERAL ======================
('general','classic',1,'What is the chemical formula of water?',                          '["H2O","CO2","NaCl","O2"]'::jsonb,0,'en'),
('general','classic',2,'Which planet is known as the "Red Planet"?',                      '["Venus","Mars","Jupiter","Saturn"]'::jsonb,1,'en'),
('general','classic',2,'How many continents are there?',                                  '["5","6","7","8"]'::jsonb,2,'en'),
('general','classic',2,'The Great Wall is located in which country?',                     '["Japan","China","India","Mongolia"]'::jsonb,1,'en'),
('general','classic',3,'What is the largest organ in the human body?',                    '["Liver","Skin","Brain","Lungs"]'::jsonb,1,'en'),
('general','classic',3,'How many bones are in the adult human body?',                     '["186","206","226","246"]'::jsonb,1,'en'),
('general','classic',2,'Who painted the Mona Lisa?',                                      '["Michelangelo","Leonardo da Vinci","Raphael","Van Gogh"]'::jsonb,1,'en'),
('general','classic',3,'The speed of light is approximately?',                            '["150,000 km/s","300,000 km/s","3,000 km/s","30,000 km/s"]'::jsonb,1,'en'),
('general','classic',3,'Which element has the chemical symbol "Au"?',                     '["Silver","Gold","Aluminum","Argon"]'::jsonb,1,'en'),
('general','modern',3,'Who developed the theory of relativity?',                          '["Isaac Newton","Albert Einstein","Stephen Hawking","Galileo"]'::jsonb,1,'en'),
('general','modern',3,'Who founded Microsoft?',                                           '["Steve Jobs","Bill Gates","Mark Zuckerberg","Larry Page"]'::jsonb,1,'en'),

-- ====================== RETRO (80s/90s) ======================
('retro','classic',3,'"Thriller" (1982) is by which artist?',                             '["Prince","Michael Jackson","Madonna","David Bowie"]'::jsonb,1,'en'),
('retro','classic',3,'Which band released "Bohemian Rhapsody"?',                          '["The Beatles","Queen","Led Zeppelin","Pink Floyd"]'::jsonb,1,'en'),
('retro','classic',3,'In which decade did the original Star Wars trilogy release?',       '["1970s","1980s","1990s","Both 70s and 80s"]'::jsonb,3,'en'),
('retro','classic',3,'"Friends" first aired in which year?',                              '["1992","1994","1996","1998"]'::jsonb,1,'en'),
('retro','classic',3,'Who played Neo in "The Matrix" (1999)?',                            '["Tom Cruise","Keanu Reeves","Brad Pitt","Will Smith"]'::jsonb,1,'en'),

-- ====================== HISTORY (world/general) ======================
('history','classic',2,'Who was the first President of the United States?',               '["Thomas Jefferson","George Washington","Abraham Lincoln","John Adams"]'::jsonb,1,'en'),
('history','classic',3,'In which year did World War II end?',                             '["1943","1944","1945","1946"]'::jsonb,2,'en'),
('history','classic',3,'Who wrote the Communist Manifesto?',                              '["Lenin","Stalin","Marx and Engels","Trotsky"]'::jsonb,2,'en'),
('history','classic',3,'The Roman Empire fell in approximately which year?',              '["376 AD","476 AD","576 AD","676 AD"]'::jsonb,1,'en'),
('history','classic',3,'Who was the ruler of France during its 1789 revolution?',         '["Napoleon Bonaparte","Louis XVI","Charles X","Louis XIV"]'::jsonb,1,'en'),

-- ====================== WORLD ======================
('world','classic',1,'What is the capital of France?',                                    '["Berlin","Paris","Rome","Madrid"]'::jsonb,1,'en'),
('world','classic',2,'Mount Everest is in which mountain range?',                         '["Andes","Himalayas","Alps","Rockies"]'::jsonb,1,'en'),
('world','classic',2,'Which ocean is the largest?',                                       '["Atlantic","Pacific","Indian","Arctic"]'::jsonb,1,'en'),
('world','classic',3,'The pyramids of Giza are in which country?',                        '["Mexico","Egypt","Greece","Turkey"]'::jsonb,1,'en'),
('world','modern',3,'Which country has the most time zones?',                             '["USA","Russia","France","China"]'::jsonb,2,'en'),
('world','classic',3,'The Amazon River is primarily located in which country?',           '["Peru","Brazil","Colombia","Venezuela"]'::jsonb,1,'en'),

-- ====================== LATEST ======================
('latest','current',3,'Which company released ChatGPT?',                                  '["Google","OpenAI","Meta","Anthropic"]'::jsonb,1,'en'),
('latest','current',3,'What is the name of Apple''s AI platform announced in 2024?',      '["Apple AI","Apple Intelligence","Siri GPT","iBrain"]'::jsonb,1,'en'),
('latest','current',3,'Which social network did Elon Musk buy in 2022?',                  '["Facebook","Snapchat","Twitter","TikTok"]'::jsonb,2,'en'),
('latest','current',3,'Which company made the AI video model "Sora"?',                    '["DeepMind","OpenAI","Runway","Meta"]'::jsonb,1,'en'),
('latest','current',4,'Who won the 2024 Nobel Prize in Literature?',                      '["Haruki Murakami","Han Kang","Margaret Atwood","Salman Rushdie"]'::jsonb,1,'en'),
('latest','current',3,'Who won the 2024 US Presidential election?',                       '["Kamala Harris","Donald Trump","Joe Biden","Ron DeSantis"]'::jsonb,1,'en')

on conflict do nothing;
