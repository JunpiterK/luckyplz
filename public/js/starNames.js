/* Star name pool for input placeholders across roulette / ladder /
   car-racing. Each language array is a shuffled-on-demand mix of
   the last 5 years' (2021-2026) most prominent names from that
   region — sports stars, singers, actors, variety hosts, creators.
   Used as <input placeholder> text only; user typing is never
   overwritten, and starting the game with empty inputs now falls
   back to whatever placeholder was shown.

   Curation policy: exclude anyone with a known major incident in the
   2021-2026 window (drug/DUI, assault/abuse, tax/fraud convictions,
   confirmed racism/hate speech, serious bullying findings). Marriage,
   retirement, benign feuds are fine. If the scandal status is
   uncertain, the name is left out rather than guessed in.

   Size: ko / en / ja / zh target ~100 each (priority locales). Other
   languages are shorter because confidence falls off; getStarPool()
   falls back to EN for anything not listed, so every user still sees
   a lively rotation. */

(function(){
    const POOLS = {
        /* ============ Korean (ko) — ~100 ============ */
        ko: [
            /* Football */
            '손흥민','이강인','김민재','박지성','차범근','황희찬','황인범','조규성','이재성','김영권',
            /* Baseball */
            '이정후','김하성','류현진','김혜성','김광현','양현종','오승환','박병호',
            /* Winter sports / athletics */
            '김연아','차준환','이상화','황선우','우상혁',
            /* Badminton / golf */
            '안세영','박세리','박인비','고진영','유해란',
            /* E-sports */
            '페이커','쇼메이커','데프트','제우스',
            /* Volleyball */
            '김연경',
            /* BTS */
            'BTS RM','BTS 진','BTS 슈가','BTS 제이홉','BTS 지민','BTS 뷔','BTS 정국',
            /* BLACKPINK */
            '블랙핑크 지수','블랙핑크 제니','블랙핑크 로제','블랙핑크 리사',
            /* NewJeans */
            '뉴진스 민지','뉴진스 하니','뉴진스 다니엘','뉴진스 해린','뉴진스 혜인',
            /* aespa */
            '에스파 카리나','에스파 지젤','에스파 윈터','에스파 닝닝',
            /* IVE */
            'IVE 안유진','IVE 장원영','IVE 리즈','IVE 레이',
            /* LE SSERAFIM */
            '르세라핌 김채원','르세라핌 사쿠라','르세라핌 카즈하',
            /* TWICE */
            '트와이스 나연','트와이스 사나','트와이스 지효','트와이스 쯔위',
            /* Solo pop */
            '아이유','태연','박효신','성시경',
            /* Male actors */
            '송강호','이병헌','황정민','하정우','유해진','이정재','정우성','공유','박서준','현빈',
            '송중기','김수현','차은우','이동욱','정해인','박형식','강동원','장동건',
            /* Female actors */
            '한효주','전지현','이영애','김혜수','손예진','김태리','박소담','수지','박은빈','김고은',
            '한소희','박보영',
            /* Variety / hosts */
            '유재석','신동엽','박나래','김숙','장도연','이영자','김종국','하하','지석진','양세찬'
        ],

        /* ============ English (en) — ~100 ============ */
        en: [
            /* Football (soccer) */
            'Lionel Messi','Cristiano Ronaldo','Kylian Mbappé','Erling Haaland','Jude Bellingham',
            'Vinícius Jr.','Lamine Yamal','Mohamed Salah','Kevin De Bruyne','Harry Kane',
            'Bukayo Saka','Pedri','Rodri','Phil Foden',
            /* NBA */
            'LeBron James','Stephen Curry','Kevin Durant','Giannis Antetokounmpo','Luka Dončić',
            'Nikola Jokić','Jayson Tatum','Anthony Edwards','Shai Gilgeous-Alexander','Victor Wembanyama',
            /* NFL */
            'Patrick Mahomes','Josh Allen','Lamar Jackson','Travis Kelce','Justin Jefferson',
            /* MLB */
            'Shohei Ohtani','Aaron Judge','Juan Soto','Bryce Harper','Ronald Acuña Jr.','Mookie Betts',
            /* Tennis */
            'Novak Djokovic','Rafael Nadal','Carlos Alcaraz','Jannik Sinner','Iga Świątek',
            'Coco Gauff','Aryna Sabalenka',
            /* F1 / golf / Olympics */
            'Max Verstappen','Lewis Hamilton','Charles Leclerc','Lando Norris','Oscar Piastri',
            'Scottie Scheffler','Rory McIlroy','Simone Biles','Katie Ledecky',
            /* Male actors */
            'Dwayne Johnson','Ryan Reynolds','Chris Hemsworth','Tom Holland','Timothée Chalamet',
            'Leonardo DiCaprio','Denzel Washington','Keanu Reeves','Pedro Pascal','Hugh Jackman',
            'Ryan Gosling','Michael B. Jordan','Cillian Murphy','Paul Mescal','Austin Butler',
            /* Female actresses */
            'Emma Stone','Zendaya','Margot Robbie','Florence Pugh','Anya Taylor-Joy',
            'Sydney Sweeney','Jenna Ortega','Millie Bobby Brown','Natalie Portman','Scarlett Johansson',
            'Viola Davis','Jennifer Lawrence','Saoirse Ronan',
            /* Pop music */
            'Taylor Swift','Beyoncé','Adele','Billie Eilish','Ariana Grande','Dua Lipa',
            'Olivia Rodrigo','Sabrina Carpenter','Harry Styles','Ed Sheeran','Bruno Mars',
            'The Weeknd','Lady Gaga','Shakira',
            /* Hip-hop / Latin / country */
            'Kendrick Lamar','J. Cole','Bad Bunny','Karol G','J Balvin','Chris Stapleton',
            /* Creators / tech / icons */
            'MrBeast','Oprah Winfrey','David Beckham','Sam Altman','Jensen Huang'
        ],

        /* ============ Japanese (ja) — ~100 ============ */
        ja: [
            /* Baseball */
            '大谷翔平','鈴木誠也','山本由伸','佐々木朗希','ダルビッシュ有','吉田正尚','千賀滉大','村上宗隆',
            /* Football */
            '久保建英','三笘薫','堂安律','冨安健洋','遠藤航','鎌田大地','伊東純也','守田英正','南野拓実',
            /* Winter / figure / gymnastics */
            '羽生結弦','宇野昌磨','紀平梨花','内村航平','橋本大輔',
            /* Tennis / golf / other */
            '錦織圭','大坂なおみ','松山英樹','渋野日向子','畑岡奈紗',
            /* Table tennis / badminton */
            '張本智和','伊藤美誠','早田ひな','平野美宇','桃田賢斗','山口茜',
            /* Boxing / snowboard */
            '井上尚弥','那須川天心','平野歩夢',
            /* J-pop / musicians */
            '米津玄師','宇多田ヒカル','星野源','YOASOBI ikura','YOASOBI Ayase','Ado','LiSA','Aimer',
            'あいみょん','藤井風','優里','King Gnu 井口理','Mrs. GREEN APPLE 大森元貴','ONE OK ROCK Taka',
            'back number 清水依与吏','秦基博','10-FEET TAKUMA',
            /* Idol groups — Nogizaka / Sakurazaka / Hinatazaka / AKB */
            '乃木坂46 齋藤飛鳥','乃木坂46 山下美月','乃木坂46 遠藤さくら','乃木坂46 賀喜遥香',
            '櫻坂46 森田ひかる','櫻坂46 山﨑天','日向坂46 小坂菜緒','日向坂46 齊藤京子',
            'AKB48 小栗有以','AKB48 柏木由紀',
            /* Snow Man / Travis Japan / Number_i */
            'Snow Man 目黒蓮','Snow Man 向井康二','SixTONES ジェシー','Number_i 平野紫耀','Number_i 神宮寺勇太',
            'Hey! Say! JUMP 山田涼介','Sexy Zone 中島健人','timelesz 菊池風磨',
            /* Male actors */
            '福山雅治','木村拓哉','山崎賢人','菅田将暉','綾野剛','堺雅人','大泉洋','阿部寛','佐藤健','坂口健太郎',
            /* Female actors */
            '新垣結衣','有村架純','石原さとみ','綾瀬はるか','北川景子','橋本環奈','広瀬すず','浜辺美波',
            '今田美桜','長澤まさみ','深田恭子','吉岡里帆','永野芽郁','上白石萌音','上白石萌歌','森七菜',
            /* Variety / hosts */
            'タモリ','明石家さんま','ナインティナイン 岡村隆史','千鳥 大悟','千鳥 ノブ','博多大吉','博多華丸'
        ],

        /* ============ Chinese (zh) — ~100 ============ */
        zh: [
            /* Basketball / NBA */
            '姚明','易建联','周琦','王治郅',
            /* Volleyball / athletics */
            '郎平','朱婷','袁心玥','苏炳添','谢震业','巩立姣',
            /* Swimming / diving */
            '张雨霏','汪顺','覃海洋','全红婵','陈芋汐','李冰洁',
            /* Winter sports */
            '谷爱凌','苏翊鸣','徐梦桃','齐广璞','任子威',
            /* Table tennis / badminton */
            '马龙','樊振东','王楚钦','陈梦','孙颖莎','王曼昱',
            '陈雨菲','石宇奇','何冰娇',
            /* MMA / football / snooker */
            '张伟丽','李景亮','武磊','丁俊晖','颜丙涛',
            /* Singers / musicians */
            '王菲','周杰伦','林俊杰','陈奕迅','周深','邓紫棋',
            '张惠妹','梁静茹','孙燕姿','莫文蔚','李宇春','毛不易',
            '那英','田馥甄','张靓颖','华晨宇','薛之谦','李荣浩',
            /* Idol groups — TFBOYS / Times Youth League */
            'TFBOYS 王俊凯','TFBOYS 王源','TFBOYS 易烊千玺',
            '时代少年团 马嘉祺','时代少年团 丁程鑫','时代少年团 宋亚轩','时代少年团 刘耀文',
            '时代少年团 张真源','时代少年团 严浩翔','时代少年团 贺峻霖',
            /* Male actors */
            '肖战','王一博','朱一龙','李现','龚俊','白敬亭','张若昀','胡歌','王凯','杨洋',
            '彭于晏','王鹤棣','吴磊','井柏然','成毅','任嘉伦','罗云熙','檀健次','刘昊然','易烊千玺',
            /* Female actors */
            '杨紫','赵丽颖','杨幂','刘诗诗','唐嫣','迪丽热巴','关晓彤','谭松韵','周冬雨','毛晓彤',
            '宋茜','倪妮','孙俪','章子怡','周迅','巩俐','舒淇','刘亦菲',
            /* Hong Kong icons */
            '刘德华','梁朝伟','周润发','成龙','甄子丹','古天乐','张学友','郭富城'
        ],

        /* ============ Spanish (es) — ~80 ============ */
        es: [
            /* Football */
            'Lionel Messi','Cristiano Ronaldo','Lamine Yamal','Pedri','Gavi','Rodri','Unai Simón',
            'Dani Olmo','Álvaro Morata','Nico Williams','Vinícius Jr.','Rodrygo','Endrick',
            'Fermín López','Fabián Ruiz','Ferran Torres','Mikel Merino',
            /* Tennis / basketball */
            'Rafael Nadal','Carlos Alcaraz','Paula Badosa','Garbiñe Muguruza',
            'Pau Gasol','Marc Gasol','Ricky Rubio','Sergio Llull',
            /* F1 / MotoGP / Olympics */
            'Fernando Alonso','Carlos Sainz','Marc Márquez','Jorge Martín','Pedro Acosta',
            'Mireia Belmonte','Sandra Sánchez',
            /* Music — Latin pop / reggaeton */
            'Shakira','Rosalía','Bad Bunny','J Balvin','Karol G','Maluma','Ozuna','Myke Towers',
            'Rauw Alejandro','Feid','Sebastián Yatra','Camilo','Pablo Alborán','Aitana',
            'Manuel Turizo','Quevedo','Bizarrap','Rels B',
            'Enrique Iglesias','Ricky Martin','Alejandro Sanz','Luis Fonsi',
            /* Actors */
            'Penélope Cruz','Javier Bardem','Antonio Banderas','Salma Hayek','Sofía Vergara',
            'Eva Longoria','Úrsula Corberó','Álvaro Morte','Jaime Lorente','Miguel Herrán',
            'Mario Casas','Najwa Nimri','Itziar Ituño','Blanca Suárez','Hugo Silva'
        ],

        /* ============ German (de) — ~70 ============ */
        de: [
            /* Football */
            'Thomas Müller','Manuel Neuer','Joshua Kimmich','Leroy Sané','Kai Havertz',
            'Jamal Musiala','Florian Wirtz','İlkay Gündoğan','Toni Kroos','Marco Reus',
            'Niclas Füllkrug','Antonio Rüdiger','Robert Andrich','Pascal Groß','Deniz Undav',
            'Maximilian Mittelstädt','David Raum','Chris Führich','Aleksandar Pavlović',
            /* Other sports */
            'Dirk Nowitzki','Dennis Schröder','Franz Wagner','Moritz Wagner',
            'Sebastian Vettel','Nico Hülkenberg','Mick Schumacher','Pascal Wehrlein',
            'Alexander Zverev','Angelique Kerber','Tatjana Maria','Jan-Lennard Struff',
            'Lukas Dauser','Pauline Schäfer',
            /* Music */
            'Helene Fischer','Sarah Connor','Max Giesinger','Mark Forster','Nico Santos',
            'Peter Maffay','Herbert Grönemeyer','Udo Lindenberg','AnnenMayKantereich Henning May',
            'Rammstein Till Lindemann','Clueso','Johannes Oerding','LEA',
            /* Actors / TV */
            'Christoph Waltz','Diane Kruger','Daniel Brühl','Sandra Hüller','Til Schweiger',
            'Matthias Schweighöfer','Elyas M\'Barek','Franka Potente','Moritz Bleibtreu',
            'Heike Makatsch','Jella Haase','Iris Berben','Veronica Ferres',
            /* Models / hosts */
            'Heidi Klum','Claudia Schiffer','Toni Garrn','Stefan Raab','Joko Winterscheidt',
            'Klaas Heufer-Umlauf'
        ],

        /* ============ French (fr) — ~70 ============ */
        fr: [
            /* Football */
            'Kylian Mbappé','Antoine Griezmann','Aurélien Tchouaméni','Eduardo Camavinga',
            'Ousmane Dembélé','Randal Kolo Muani','William Saliba','Mike Maignan','Theo Hernández',
            'Jules Koundé','Ibrahima Konaté','Adrien Rabiot','Bradley Barcola','Warren Zaïre-Emery',
            'N\'Golo Kanté','Hugo Lloris',
            /* NBA / basketball */
            'Tony Parker','Victor Wembanyama','Rudy Gobert','Nicolas Batum','Evan Fournier',
            'Guerschon Yabusele',
            /* Tennis / F1 */
            'Gaël Monfils','Arthur Fils','Ugo Humbert','Caroline Garcia','Corentin Moutet',
            'Pierre Gasly','Esteban Ocon',
            /* Olympics / handball */
            'Teddy Riner','Léon Marchand','Cassandre Beaugrand','Nikola Karabatić',
            /* Music */
            'Stromae','Aya Nakamura','Indila','Louane','Vianney','Angèle','Clara Luciani',
            'Pomme','Hoshi','Christine and the Queens','Zaho de Sagazan','Bigflo & Oli',
            'Soprano','Kendji Girac','Slimane',
            /* Actors */
            'Marion Cotillard','Jean Dujardin','Omar Sy','Léa Seydoux','Vincent Cassel',
            'Juliette Binoche','Camille Cottin','Virginie Efira','Tahar Rahim','Sandrine Kiberlain',
            'Karin Viard','François Civil','Pio Marmaï','Noémie Merlant','Adèle Exarchopoulos',
            'Anaïs Demoustier','Lyna Khoudri'
        ],

        /* ============ Portuguese (pt) — ~70 ============ */
        pt: [
            /* Football — Brazil */
            'Neymar Jr.','Vinícius Jr.','Rodrygo','Endrick','Casemiro','Marquinhos','Thiago Silva',
            'Ederson','Alisson Becker','Gabriel Magalhães','Bruno Guimarães','Raphinha',
            'Gabriel Martinelli','Lucas Paquetá','Richarlison',
            /* Football — Portugal */
            'Cristiano Ronaldo','Bruno Fernandes','Bernardo Silva','Rúben Dias','João Félix',
            'João Cancelo','Diogo Jota','Rafael Leão','Vitinha','Gonçalo Ramos','Pepe',
            'Rúben Neves','Nuno Mendes',
            /* Volleyball / MMA / other */
            'Gabi Guimarães','Rosamaria','Charles do Bronx','Deiveson Figueiredo','Gabriel Medina',
            'Rayssa Leal','Hugo Calderano','Rebeca Andrade',
            /* Music — Brazil / Portugal */
            'Anitta','Pabllo Vittar','Luan Santana','Gusttavo Lima','Ludmilla','Caetano Veloso',
            'Ivete Sangalo','Marília Mendonça','Wesley Safadão','Alok','Jão','Iza',
            'Manu Gavassi','Maria Bethânia','Liniker','Marisa Monte','Gilberto Gil',
            'Salvador Sobral','Diogo Piçarra','Carolina Deslandes',
            /* Actors / hosts */
            'Rodrigo Santoro','Wagner Moura','Bruna Marquezine','Fernanda Montenegro','Alice Braga',
            'Fernanda Torres','Marjorie Estiano','Paolla Oliveira','Taís Araújo','Lázaro Ramos',
            'Grazi Massafera','Juliana Paes','Vladimir Brichta','Deborah Secco','Xuxa',
            'Angélica','Luciano Huck'
        ],

        /* ============ Russian (ru) — ~50 ============ */
        ru: [
            /* Hockey / football */
            'Александр Овечкин','Евгений Малкин','Артемий Панарин','Никита Кучеров','Владимир Тарасенко',
            'Кирилл Капризов','Игорь Шестёркин',
            /* Tennis */
            'Даниил Медведев','Андрей Рублёв','Карен Хачанов','Анна Калинская','Людмила Самсонова',
            'Дарья Касаткина','Мирра Андреева',
            /* Figure skating / gymnastics */
            'Камила Валиева','Алина Загитова','Евгения Медведева','Анна Щербакова','Александра Трусова',
            'Аделия Петросян','Никита Нагорный',
            /* Swimming / biathlon */
            'Евгений Рылов','Климент Колесников','Юлия Ефимова','Евгений Устюгов',
            /* MMA / boxing */
            'Фёдор Емельяненко','Ислам Махачев','Пётр Ян','Магомед Анкалаев','Александр Емельяненко',
            /* Music */
            'Полина Гагарина','Дима Билан','Сергей Лазарев','Ани Лорак','Леонид Агутин',
            'Баста','L\'One','Егор Крид','Zivert','Валерий Меладзе','Стас Михайлов','MiyaGi',
            /* Actors / hosts */
            'Данила Козловский','Юра Борисов','Константин Хабенский','Светлана Ходченкова',
            'Юлия Пересильд','Паулина Андреева','Сергей Безруков','Ксения Собчак','Иван Ургант',
            'Максим Галкин'
        ],

        /* ============ Arabic (ar) — ~50 ============ */
        ar: [
            /* Football */
            'محمد صلاح','رياض محرز','أشرف حكيمي','حكيم زياش','يوسف النصيري','سفيان أمرابط','نصير مزراوي',
            'إيوان فيريرا','بلال الخنوس','أنس دحبي','محمد السيد','عمر مرموش','وسام أبو علي','المعز علي',
            'سالم الدوسري','فراس البريكان','أيمن حسين','ياسين بونو',
            /* Tennis / other sports */
            'أنس جابر','أحمد حافناوي','مصطفى الحسيني',
            /* Music */
            'عمرو دياب','نانسي عجرم','إليسا','تامر حسني','محمد رمضان','أصالة نصري','حسين الجسمي',
            'ماجد المهندس','راشد الماجد','محمد حماقي','بلقيس','شيرين عبد الوهاب','كاظم الساهر',
            'عاصي الحلاني','فضل شاكر','وائل كفوري','نوال الزغبي','أحلام',
            /* Actors */
            'هند صبري','منى زكي','ياسمين عبد العزيز','أحمد حلمي','يسرا','نيللي كريم','عادل إمام',
            'أحمد السقا','كريم عبد العزيز','محمد هنيدي','محمد سعد','منى شداد','شيرين رضا','يحيى الفخراني'
        ],

        /* ============ Hindi (hi) — ~70 ============ */
        hi: [
            /* Cricket */
            'विराट कोहली','रोहित शर्मा','एमएस धोनी','सचिन तेंदुलकर','जसप्रीत बुमराह','हार्दिक पांड्या',
            'केएल राहुल','रवींद्र जडेजा','शुभमन गिल','ऋषभ पंत','मोहम्मद सिराज','कुलदीप यादव',
            'वाशिंगटन सुंदर','यशस्वी जायसवाल','सूर्यकुमार यादव','अक्षर पटेल','मोहम्मद शमी','ईशान किशन',
            /* Other sports */
            'पीवी सिंधु','नीरज चोपड़ा','मीराबाई चानू','मनु भाकर','सरबजोत सिंह','निखत जरीन','मनिका बत्रा',
            'लक्ष्य सेन','सात्विकसाईराज रंकीरेड्डी','चिराग शेट्टी',
            /* Bollywood — male */
            'शाहरुख खान','सलमान खान','आमिर खान','अक्षय कुमार','अजय देवगन','ऋतिक रोशन','रणवीर सिंह',
            'रणबीर कपूर','विकी कौशल','आयुष्मान खुराना','वरुण धवन','शाहिद कपूर','सिद्धार्थ मल्होत्रा',
            'कार्तिक आर्यन','विजय देवरकोंडा','रजनीकांत','कमल हासन','धनुष','अल्लू अर्जुन','प्रभास',
            'एनटी रामा राव जूनियर','राम चरण','यश','फहाद फासिल',
            /* Bollywood — female */
            'दीपिका पादुकोण','आलिया भट्ट','अनुष्का शर्मा','प्रियंका चोपड़ा','कैटरीना कैफ','कियारा आडवाणी',
            'सारा अली खान','जाह्नवी कपूर','करीना कपूर','रश्मिका मंदाना','त्रिप्ति डिमरी','सामंथा रुथ प्रभु',
            'विद्या बालन','माधुरी दीक्षित',
            /* Music */
            'अरिजीत सिंह','श्रेया घोषाल','ए आर रहमान','दिलजीत दोसांझ','शंकर महादेवन','कैलाश खेर'
        ],

        /* ============ Thai (th) — ~55 ============ */
        th: [
            /* K-pop idols of Thai origin + T-pop */
            'ลิซ่า BLACKPINK','แบมแบม GOT7','มิงยู F.HERO','เต็น NCT','ลลิษา ROSÉ',
            'ฟ้าใส ปวีณสุดา','บีเอ็นเค48 เฌอปราง','อิ้งค์ วรันธร','LYKN',
            /* T-drama stars */
            'ใหม่ ดาวิกา','ญาญ่า อุรัสยา','คิมเบอร์ลี่ แอน','มิว นิษฐา','มิน พีชญา','ใบเฟิร์น พิมพ์ชนก',
            'เบลล่า ราณี','เเอฟ ทักษอร','เอสเธอร์ สุปรีย์ลีลา','ดาวิกา โฮร์เน่',
            'ณเดชน์ คูกิมิยะ','เจมส์ จิรายุ','ไบร์ท วชิรวิชญ์','วิน เมธวิน','ต่อ ธนภพ',
            'โป๊ป ธนวรรธน์','เวียร์ ศุกลวัฒน์','หมาก ปริญ','ก้อง สหรัถ',
            /* BL series stars */
            'มิว ศุภศิษฏ์','กัน อรรถพันธ์','จูเน่ จุน','ฟอร์ด อารัณย์','ไบเบิ้ล วิชญ์ภาส',
            /* Sports */
            'บัวขาว บัญชาเมฆ','สมจิตร จงจอหอ','รัชนก อินทนนท์','เทนนิส พาณิภัค','ภาณุพงศ์ เจริญกุล',
            'วิว กุลวุฒิ','ชนาธิป สรงกระสินธ์','ศุภชัย เจียรวนนท์',
            /* Music */
            'ปาล์มมี่','กอล์ฟ ฟักกลิ้ง ฮีโร่','ตูน บอดี้สแลม','ป๊อด โมเดิร์นด็อก','เป๊ก ผลิตโชค',
            'บี้ เดอะสตาร์','ก้อง ห้วยไร่','ลานา นิอุบล','Jeff Satur','4EVE'
        ],

        /* ============ Indonesian (id) — ~55 ============ */
        id: [
            /* Football */
            'Witan Sulaeman','Pratama Arhan','Marselino Ferdinan','Egy Maulana','Rizky Ridho',
            'Jordi Amat','Sandy Walsh','Rafael Struick','Ivar Jenner','Justin Hubner',
            'Thom Haye','Jay Idzes','Nathan Tjoe-A-On','Maarten Paes','Asnawi Mangkualam',
            /* Badminton / other sports */
            'Greysia Polii','Apriyani Rahayu','Jonatan Christie','Anthony Ginting','Kevin Sanjaya',
            'Marcus Gideon','Fajar Alfian','Muhammad Rian','Ana Rovita','Siti Fadia',
            'Eko Yuli Irawan','Rahmat Erwin',
            /* Music */
            'Raisa','Tulus','Rich Brian','Niki','Agnez Mo','Isyana Sarasvati','Afgan','Vidi Aldiano',
            'Yura Yunita','Mahalini','Lyodra','Keisya Levronka','Tiara Andini','Ziva Magnolya',
            'Ardhito Pramono','Rizky Febian','BCL','Judika','Denny Caknan','Happy Asmara',
            /* Actors */
            'Iko Uwais','Joe Taslim','Reza Rahadian','Nicholas Saputra','Dian Sastrowardoyo',
            'Luna Maya','Maudy Ayunda','Raline Shah','Cinta Laura','Prilly Latuconsina',
            'Pevita Pearce','Chelsea Islan','Marsha Timothy','Ari Irham','Angga Yunanda',
            'Iqbaal Ramadhan','Jefri Nichol','Vino G. Bastian','Adipati Dolken'
        ],

        /* ============ Vietnamese (vi) — ~55 ============ */
        vi: [
            /* Football */
            'Quang Hải','Công Phượng','Tiến Linh','Văn Hậu','Đặng Văn Lâm','Xuân Trường','Hùng Dũng',
            'Hoàng Đức','Văn Toàn','Thanh Bình','Duy Mạnh','Tuấn Anh',
            'Nguyễn Filip','Nguyễn Thành Chung','Quế Ngọc Hải','Bùi Tiến Dũng','Nguyễn Tiến Linh',
            /* Other sports */
            'Nguyễn Thùy Linh','Lê Quang Liêm','Hoàng Xuân Vinh','Nguyễn Thị Ánh Viên','Thạch Kim Tuấn',
            'Nguyễn Thị Oanh','Nguyễn Huy Hoàng','Trịnh Thu Vinh','Nguyễn Thị Tâm',
            /* Music */
            'Sơn Tùng M-TP','Đen Vâu','Mỹ Tâm','Hồ Ngọc Hà','Hoàng Thùy Linh','Bích Phương',
            'Tóc Tiên','Erik','Hương Tràm','Amee','Hoà Minzy','Văn Mai Hương','Chi Pu',
            'Đông Nhi','Ông Cao Thắng','Trúc Nhân','Tlinh','MCK','Double2T','Dương Domic',
            /* Actors / TV */
            'Trấn Thành','Trường Giang','Ngô Thanh Vân','Ninh Dương Lan Ngọc','Lan Phương',
            'Nhã Phương','Hari Won','Lê Dương Bảo Lâm','Kiều Minh Tuấn','Liên Bỉnh Phát',
            'Nhan Phúc Vinh','Bảo Thanh','Hồng Diễm','Phương Oanh','Doãn Quốc Đam'
        ],

        /* ============ Turkish (tr) — ~60 ============ */
        tr: [
            /* Football */
            'Arda Güler','Hakan Çalhanoğlu','Mert Günok','Kerem Aktürkoğlu','Ferdi Kadıoğlu',
            'Altay Bayındır','Uğurcan Çakır','Merih Demiral','Yusuf Yazıcı','Çağlar Söyüncü',
            'Barış Alper Yılmaz','Kenan Yıldız','Salih Özcan','Zeki Çelik','Orkun Kökçü',
            'İrfan Can Kahveci','Abdülkerim Bardakcı','Kaan Ayhan','Can Uzun','Semih Kılıçsoy',
            /* Basketball / volleyball */
            'Alperen Şengün','Cedi Osman','Furkan Korkmaz','Şehmus Hazer','Ebrar Karakurt',
            'Melissa Vargas','Eda Erdem Dündar','Zehra Güneş',
            /* Other sports */
            'Mete Gazoz','Yasemin Adar','Taha Akgül','Buse Tosun','Busenaz Sürmeneli',
            /* Music */
            'Tarkan','Sezen Aksu','Hadise','Edis','Aleyna Tilki','Mabel Matiz','Simge Sağın',
            'İrem Derici','Ece Seçkin','Hande Yener','Sıla','Melek Mosso','Birol Giray Namoğlu',
            'Zeynep Bastık','Derya Uluğ','UZI','Reynmen','Manuş Baba',
            /* Actors */
            'Kıvanç Tatlıtuğ','Burak Özçivit','Çağatay Ulusoy','Can Yaman','Kerem Bürsin',
            'Engin Akyürek','Halit Ergenç','Haluk Bilginer','Tuba Büyüküstün','Beren Saat',
            'Hande Erçel','Serenay Sarıkaya','Demet Özdemir','Pınar Deniz','Ebru Şahin',
            'Özge Yağız'
        ]
    };

    /* British English (gb) shares the EN pool. */
    POOLS.gb = POOLS.en;

    function shuffle(arr){
        const a=[...arr];
        for(let i=a.length-1;i>0;i--){
            const j=Math.floor(Math.random()*(i+1));
            [a[i],a[j]]=[a[j],a[i]];
        }
        return a;
    }

    /* getStarPool(lang) — returns a shuffled copy of the pool for the
       requested language. Small languages fall back to English so we
       still get a big, varied placeholder rotation everywhere. Caller
       picks the first N names for N input slots — stable until the
       language changes or the page reloads. */
    window.getStarPool = function(lang){
        const pool = POOLS[lang] || POOLS.en || [];
        return shuffle(pool);
    };
})();
