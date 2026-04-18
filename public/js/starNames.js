/* Star name pool for input placeholders across roulette / ladder /
   car-racing. Each language array is a shuffled-on-demand mix of
   currently popular sports figures, actors, and pop stars from that
   region. Used as <input placeholder> text only — user typing is
   never overwritten.

   Design: ko + en are heavy (200+ each, the two priority locales per
   user preference). ja + zh are ~100 each. All other languages fall
   back to EN via getStarPool(), keeping the file lean while still
   localizing the two markets that matter most. */

(function(){
    const POOLS = {
        /* ============ Korean (ko) — 200+ ============ */
        ko: [
            /* Football */
            '손흥민','이강인','김민재','박지성','차범근','황희찬','황인범','조규성','김진수','이재성',
            '김영권','기성용','이청용','구자철','홍명보','박주영','이동국','이영표','설기현','안정환',
            /* Baseball */
            '박찬호','류현진','추신수','이정후','김하성','오타니 쇼헤이','김광현','양현종','오승환','이대호',
            '박병호','강정호','나성범','이승엽','양의지','김현수','최정','구자욱','박해민','손아섭',
            /* Figure skating / winter */
            '김연아','차준환','유영','이해인','임은수','이상화','박승희','심석희','안현수','임효준',
            /* Golf / tennis / other */
            '박세리','박인비','고진영','전인지','김효주','유소연','최나연','신지애',
            /* E-sports */
            '페이커','데프트','쇼메이커','캐니언','울프','뱅','룰러','케리아',
            /* BTS */
            'BTS RM','BTS 진','BTS 슈가','BTS 제이홉','BTS 지민','BTS 뷔','BTS 정국',
            /* BLACKPINK */
            '블랙핑크 지수','블랙핑크 제니','블랙핑크 로제','블랙핑크 리사',
            /* TWICE */
            '트와이스 나연','트와이스 정연','트와이스 모모','트와이스 사나','트와이스 지효',
            '트와이스 미나','트와이스 다현','트와이스 채영','트와이스 쯔위',
            /* NewJeans */
            '뉴진스 민지','뉴진스 하니','뉴진스 다니엘','뉴진스 해린','뉴진스 혜인',
            /* aespa */
            '에스파 카리나','에스파 지젤','에스파 윈터','에스파 닝닝',
            /* LE SSERAFIM */
            '르세라핌 김채원','르세라핌 사쿠라','르세라핌 허윤진','르세라핌 카즈하','르세라핌 홍은채',
            /* IVE */
            'IVE 안유진','IVE 가을','IVE 장원영','IVE 리즈','IVE 이서','IVE 레이',
            /* (G)I-DLE / ITZY / etc */
            '아이들 미연','아이들 민니','아이들 소연','아이들 우기','아이들 슈화',
            'ITZY 예지','ITZY 리아','ITZY 류진','ITZY 채령','ITZY 유나',
            /* Solo pop */
            '아이유','태연','선미','청하','화사','제시','현아','보아','백지영','이효리',
            /* Boy groups */
            '세븐틴 우지','세븐틴 도겸','세븐틴 호시','엑소 카이','엑소 백현','엑소 디오','엑소 세훈','엑소 찬열',
            'NCT 마크','NCT 재현','NCT 태용','NCT 도영','NCT 태일',
            '스트레이키즈 방찬','스트레이키즈 리노','스트레이키즈 현진','스트레이키즈 필릭스',
            '투모로우바이투게더 수빈','투모로우바이투게더 연준','투모로우바이투게더 범규',
            '빅뱅 지디','빅뱅 탑','빅뱅 대성','빅뱅 태양','2PM 닉쿤','2PM 택연','2PM 우영','2PM 준호',
            /* Movie actors (male) */
            '송강호','이병헌','최민식','설경구','황정민','하정우','유해진','류승룡','마동석','이정재',
            '정우성','공유','김우빈','이민호','박보검','박서준','현빈','송중기','김수현','차은우',
            '이동욱','이준기','유아인','이제훈','정해인','박형식','남주혁','강동원','원빈','장동건',
            '조인성','이선균','류준열','이성민','오정세','주지훈','김남길','유지태','조진웅',
            /* Movie actresses (female) */
            '한효주','전지현','이영애','김혜수','손예진','김태리','박소담','배두나','수지','윤아',
            '박은빈','김고은','한소희','김다미','박민영','김새론','임수정','이나영','한지민','공효진',
            '전도연','고아성','천우희','정유미','김옥빈','박보영','유인나','이민정','정려원','이지아',
            /* Variety / hosts */
            '유재석','강호동','신동엽','김구라','박명수','정형돈','이수근','양세형','노홍철',
            '박나래','김숙','장도연','송은이','이경규','이영자','김종국','하하','지석진','양세찬',
            /* Directors / writers */
            '봉준호','박찬욱','이창동','홍상수','나홍진','김한민',
            /* Classical / crossover */
            '조성진','임윤찬','손열음','정명훈','서희',
            /* Creators / youtubers */
            '주호민','쯔양','도티','양띵','보겸','풍월량','우왁굳',
            /* Misc idols (extra depth) */
            '레드벨벳 아이린','레드벨벳 슬기','레드벨벳 웬디','레드벨벳 조이','레드벨벳 예리',
            '마마무 솔라','마마무 문별','마마무 휘인','마마무 화사',
            '오마이걸 효정','오마이걸 미미','오마이걸 지호','오마이걸 유아',
            '에이핑크 박초롱','에이핑크 윤보미','에이핑크 정은지','에이핑크 손나은',
            '걸스데이 혜리','걸스데이 민아','소녀시대 태연','소녀시대 윤아','소녀시대 서현',
            '소녀시대 티파니','소녀시대 유리','소녀시대 수영','소녀시대 제시카','소녀시대 효연'
        ],

        /* ============ English (en) — 200+ ============ */
        en: [
            /* Football (soccer) */
            'Lionel Messi','Cristiano Ronaldo','Kylian Mbappé','Erling Haaland','Neymar Jr.',
            'Vinícius Jr.','Jude Bellingham','Mohamed Salah','Kevin De Bruyne','Harry Kane',
            'Robert Lewandowski','Luka Modrić','Karim Benzema','Virgil van Dijk','Alisson Becker',
            'Bukayo Saka','Trent Alexander-Arnold','Lamine Yamal','Pedri','Gavi',
            'Phil Foden','Declan Rice','Rodri','Jamal Musiala','Florian Wirtz',
            /* NBA */
            'LeBron James','Stephen Curry','Kevin Durant','Giannis Antetokounmpo','Luka Dončić',
            'Nikola Jokić','Jayson Tatum','Jimmy Butler','Ja Morant','Anthony Edwards',
            'Devin Booker','Joel Embiid','Damian Lillard','Kawhi Leonard','Shai Gilgeous-Alexander',
            'Zion Williamson','Donovan Mitchell','Paolo Banchero','Victor Wembanyama','Chet Holmgren',
            /* NFL / MLB */
            'Patrick Mahomes','Josh Allen','Tom Brady','Aaron Rodgers','Lamar Jackson',
            'Christian McCaffrey','Travis Kelce','Justin Jefferson','Ja\'Marr Chase','Tyreek Hill',
            'Shohei Ohtani','Aaron Judge','Mike Trout','Bryce Harper','Juan Soto','Ronald Acuña Jr.',
            'Freddie Freeman','Mookie Betts','Vladimir Guerrero Jr.',
            /* Tennis / golf / F1 */
            'Serena Williams','Novak Djokovic','Rafael Nadal','Carlos Alcaraz','Iga Świątek',
            'Coco Gauff','Aryna Sabalenka','Jannik Sinner','Daniil Medvedev','Roger Federer',
            'Tiger Woods','Rory McIlroy','Scottie Scheffler','Brooks Koepka','Jon Rahm',
            'Max Verstappen','Lewis Hamilton','Charles Leclerc','Lando Norris','Sergio Pérez','Fernando Alonso',
            /* Olympics / UFC / boxing */
            'Usain Bolt','Simone Biles','Michael Phelps','Katie Ledecky','Caeleb Dressel',
            'Conor McGregor','Khabib Nurmagomedov','Jon Jones','Israel Adesanya','Islam Makhachev',
            'Canelo Álvarez','Tyson Fury','Anthony Joshua','Naomi Osaka','Allyson Felix',
            /* Actors (male) */
            'Dwayne Johnson','Ryan Reynolds','Chris Hemsworth','Chris Evans','Tom Holland',
            'Timothée Chalamet','Tom Hanks','Leonardo DiCaprio','Brad Pitt','Denzel Washington',
            'Will Smith','Robert Downey Jr.','Keanu Reeves','Jackie Chan','Jason Momoa',
            'Henry Cavill','Pedro Pascal','Benedict Cumberbatch','Idris Elba','Matt Damon',
            'Ben Affleck','Matthew McConaughey','Jake Gyllenhaal','Ryan Gosling','Zac Efron',
            'Chris Pratt','Mark Ruffalo','Paul Rudd','Robert Pattinson','Cillian Murphy',
            'Michael B. Jordan','Anthony Mackie','Andrew Garfield','Tom Hiddleston','Hugh Jackman',
            /* Actresses (female) */
            'Scarlett Johansson','Emma Stone','Jennifer Lawrence','Zendaya','Margot Robbie',
            'Florence Pugh','Anya Taylor-Joy','Sydney Sweeney','Jenna Ortega','Millie Bobby Brown',
            'Lily Collins','Emma Watson','Natalie Portman','Jennifer Aniston','Nicole Kidman',
            'Angelina Jolie','Gal Gadot','Viola Davis','Cate Blanchett','Meryl Streep',
            'Reese Witherspoon','Sandra Bullock','Kristen Stewart','Dakota Johnson','Blake Lively',
            'Charlize Theron','Mila Kunis','Anne Hathaway','Julia Roberts','Halle Berry',
            /* Pop music */
            'Taylor Swift','Beyoncé','Rihanna','Adele','Billie Eilish','Ariana Grande',
            'Dua Lipa','Lady Gaga','Olivia Rodrigo','Sabrina Carpenter','Miley Cyrus',
            'Katy Perry','Selena Gomez','Demi Lovato','Shakira','Pink',
            'Ed Sheeran','Justin Bieber','Harry Styles','Shawn Mendes','Zayn Malik',
            'Bruno Mars','John Legend','Post Malone','The Weeknd','Nick Jonas',
            /* Hip-hop / R&B / Country / Rock */
            'Drake','Kendrick Lamar','J. Cole','Travis Scott','Eminem',
            'Jay-Z','Snoop Dogg','Bad Bunny','J Balvin','Karol G',
            'Chris Brown','Usher','Frank Ocean','H.E.R.','Jhené Aiko',
            'Luke Combs','Morgan Wallen','Kacey Musgraves','Dolly Parton',
            'Chris Martin','Dan Reynolds','Dave Grohl','Billie Joe Armstrong',
            /* Models / influencers */
            'Kim Kardashian','Kylie Jenner','Gigi Hadid','Bella Hadid','Hailey Bieber',
            'Kendall Jenner','Cara Delevingne','Emily Ratajkowski','Kaia Gerber','Heidi Klum',
            'Naomi Campbell','Tyra Banks',
            /* Tech / business */
            'Elon Musk','Jeff Bezos','Mark Zuckerberg','Bill Gates','Tim Cook','Sam Altman','Jensen Huang',
            /* YouTubers / creators */
            'MrBeast','Emma Chamberlain','Markiplier','Dream'
        ],

        /* ============ Japanese (ja) — ~110 ============ */
        ja: [
            /* Baseball / sports */
            '大谷翔平','鈴木誠也','山本由伸','佐々木朗希','ダルビッシュ有',
            '田中将大','吉田正尚','千賀滉大','イチロー','松井秀喜',
            '羽生結弦','宇野昌磨','紀平梨花','浅田真央','高橋大輔',
            '内村航平','橋本大輔','白井健三',
            '錦織圭','大坂なおみ','伊達公子',
            '久保建英','三笘薫','堂安律','冨安健洋','遠藤航','鎌田大地','伊東純也','守田英正',
            '本田圭佑','香川真司','長友佑都','長谷部誠','中田英寿',
            '松山英樹','渋野日向子','畑岡奈紗',
            '張本智和','伊藤美誠','早田ひな','平野美宇','水谷隼',
            '桃田賢斗','山口茜',
            /* J-pop / musicians */
            '米津玄師','宇多田ヒカル','椎名林檎','星野源','YOASOBI ikura','YOASOBI Ayase',
            'Ado','LiSA','Aimer','あいみょん','藤井風','優里','back number 清水依与吏',
            'Mrs. GREEN APPLE 大森元貴','King Gnu 井口理','ONE OK ROCK Taka',
            /* Johnny\'s / idols */
            '嵐 大野智','嵐 櫻井翔','嵐 相葉雅紀','嵐 二宮和也','嵐 松本潤',
            'KinKi Kids 堂本光一','KinKi Kids 堂本剛','V6 岡田准一',
            '山田涼介','中島健人','菊池風磨','平野紫耀',
            /* Girl groups */
            'AKB48 指原莉乃','AKB48 柏木由紀','AKB48 小栗有以',
            '乃木坂46 齋藤飛鳥','乃木坂46 白石麻衣','乃木坂46 遠藤さくら','乃木坂46 山下美月',
            '欅坂46 平手友梨奈','櫻坂46 森田ひかる','日向坂46 小坂菜緒',
            /* Actors / actresses */
            '福山雅治','桑田佳祐','木村拓哉','松本潤','山崎賢人','菅田将暉','綾野剛','松山ケンイチ',
            '堺雅人','長谷川博己','大泉洋','阿部寛','岡田准一','織田裕二',
            '新垣結衣','有村架純','石原さとみ','綾瀬はるか','北川景子','橋本環奈','広瀬すず',
            '浜辺美波','今田美桜','吉岡里帆','長澤まさみ','深田恭子','篠原涼子','米倉涼子',
            '佐藤健','坂口健太郎','千葉雄大','山田孝之','窪田正孝',
            /* Variety */
            'タモリ','明石家さんま','ダウンタウン 浜田雅功','ダウンタウン 松本人志',
            'とんねるず 石橋貴明','ナインティナイン 岡村隆史','宮迫博之'
        ],

        /* ============ Chinese (zh) — ~100 ============ */
        zh: [
            /* Sports */
            '姚明','林書豪','王治郅','易建聯',
            '郎平','朱婷','惠若琪',
            '刘翔','苏炳添','谢震业',
            '孙杨','傅园慧','张雨霏','汪顺','覃海洋',
            '谷爱凌','苏翊鸣','徐梦桃',
            '马龙','樊振东','陈梦','孙颖莎','王曼昱','许昕','刘诗雯','丁宁',
            '林丹','谌龙','陈雨菲','石宇奇',
            '张伟丽','李景亮','张挺',
            '武磊','郑智','吴曦',
            '丁俊晖','颜丙涛',
            '全红婵','陈芋汐','施廷懋',
            /* Music / singers */
            '王菲','周杰伦','蔡依林','王力宏','林俊杰','张惠妹','陈奕迅',
            '邓紫棋','张韶涵','萧敬腾','林志玲','莫文蔚','梁静茹','孙燕姿',
            '李宇春','周笔畅','张靓颖','华晨宇','毛不易','周深',
            '阿信','玛莎','石头','冠佑','怪兽',
            /* Idol groups */
            'TFBOYS 王俊凯','TFBOYS 王源','TFBOYS 易烊千玺',
            '时代少年团 马嘉祺','时代少年团 丁程鑫',
            /* Actors / actresses */
            '肖战','王一博','朱一龙','李现','龚俊','白敬亭','张若昀','胡歌','王凯',
            '杨洋','陈伟霆','彭于晏','井柏然','邓伦','吴磊','王鹤棣',
            '杨紫','赵丽颖','杨幂','刘诗诗','唐嫣','迪丽热巴','关晓彤','谭松韵',
            '周迅','巩俐','舒淇','姚晨','刘亦菲','章子怡','范冰冰',
            '刘德华','梁朝伟','张学友','郭富城','黎明',
            '周润发','成龙','李连杰','甄子丹','古天乐','张家辉',
            '黄晓明','吴彦祖','吴京','张晋'
        ],

        /* ============ Spanish (es) — light pool, en fallback covers rest ============ */
        es: [
            'Lionel Messi','Cristiano Ronaldo','Sergio Ramos','Andrés Iniesta','Xavi Hernández',
            'Vinícius Jr.','Rodrygo','Lamine Yamal','Pedri','Gavi','Rodri','Unai Simón',
            'Rafael Nadal','Carlos Alcaraz','Paula Badosa','Garbiñe Muguruza',
            'Pau Gasol','Marc Gasol','Ricky Rubio',
            'Fernando Alonso','Carlos Sainz',
            'Shakira','Rosalía','Bad Bunny','J Balvin','Karol G','Maluma','Daddy Yankee','Anuel AA',
            'Enrique Iglesias','Ricky Martin','Luis Miguel','Alejandro Sanz','Pablo Alborán',
            'Penélope Cruz','Javier Bardem','Antonio Banderas','Salma Hayek','Sofía Vergara',
            'Eva Longoria','Úrsula Corberó','Álvaro Morte','Jaime Lorente','Miguel Herrán'
        ],

        /* ============ German (de) — light ============ */
        de: [
            'Thomas Müller','Manuel Neuer','Joshua Kimmich','Leroy Sané','Kai Havertz',
            'Jamal Musiala','Florian Wirtz','İlkay Gündoğan','Toni Kroos','Marco Reus',
            'Dirk Nowitzki','Max Verstappen','Sebastian Vettel','Nico Rosberg','Mick Schumacher',
            'Angelique Kerber','Alexander Zverev','Boris Becker',
            'Rammstein Till Lindemann','Herbert Grönemeyer','Helene Fischer','Sarah Connor','Max Giesinger',
            'Christoph Waltz','Diane Kruger','Til Schweiger','Daniel Brühl','Sandra Hüller',
            'Heidi Klum','Claudia Schiffer','Toni Garrn'
        ],

        /* ============ French (fr) — light ============ */
        fr: [
            'Kylian Mbappé','Antoine Griezmann','Paul Pogba','Karim Benzema','Hugo Lloris',
            'Ousmane Dembélé','Aurélien Tchouaméni','Eduardo Camavinga','Zinedine Zidane',
            'Tony Parker','Victor Wembanyama','Rudy Gobert','Evan Fournier',
            'Gaël Monfils','Richard Gasquet','Pierre Gasly','Esteban Ocon',
            'Stromae','Indila','Aya Nakamura','M. Pokora','Maître Gims','Zaz',
            'Marion Cotillard','Jean Dujardin','Omar Sy','Léa Seydoux','Vincent Cassel',
            'Juliette Binoche','Audrey Tautou','Sophie Marceau','Gaspard Ulliel'
        ],

        /* ============ Portuguese (pt) — light ============ */
        pt: [
            'Cristiano Ronaldo','Bruno Fernandes','Bernardo Silva','Rúben Dias','João Félix',
            'Neymar Jr.','Vinícius Jr.','Rodrygo','Casemiro','Marquinhos','Thiago Silva',
            'Anitta','Pabllo Vittar','Luan Santana','Gusttavo Lima','Ludmilla','Caetano Veloso',
            'Rodrigo Santoro','Wagner Moura','Bruna Marquezine','Fernanda Montenegro','Alice Braga'
        ],

        /* ============ Russian (ru) — light ============ */
        ru: [
            'Александр Овечкин','Евгений Малкин','Артемий Панарин','Никита Кучеров',
            'Мария Шарапова','Даниил Медведев','Андрей Рублёв','Карен Хачанов',
            'Камила Валиева','Евгения Медведева','Алина Загитова',
            'Фёдор Емельяненко','Хабиб Нурмагомедов','Ислам Махачев',
            'Егор Крид','Моргенштерн','Баста','Полина Гагарина','Дима Билан'
        ],

        /* ============ Arabic (ar) — light ============ */
        ar: [
            'محمد صلاح','رياض محرز','سعد الشاعر','حكيم زياش','أشرف حكيمي','كريم بنزيما',
            'عمرو دياب','نانسي عجرم','إليسا','تامر حسني','محمد رمضان','أصالة نصري',
            'هند صبري','منى زكي','ياسمين عبد العزيز','أحمد حلمي'
        ],

        /* ============ Hindi (hi) — light ============ */
        hi: [
            'विराट कोहली','रोहित शर्मा','एमएस धोनी','सचिन तेंदुलकर','जसप्रीत बुमराह',
            'हार्दिक पांड्या','केएल राहुल','रवींद्र जडेजा','पीवी सिंधु','नीरज चोपड़ा',
            'शाहरुख खान','सलमान खान','आमिर खान','अक्षय कुमार','अजय देवगन','ऋतिक रोशन',
            'रणवीर सिंह','रणबीर कपूर','विकी कौशल','आयुष्मान खुराना',
            'दीपिका पादुकोण','आलिया भट्ट','कैटरीना कैफ','अनुष्का शर्मा','प्रियंका चोपड़ा',
            'कियारा आडवाणी','सारा अली खान','जाह्नवी कपूर','करीना कपूर','माधुरी दीक्षित',
            'अरिजीत सिंह','श्रेया घोषाल','ए आर रहमान','बादशाह','हनी सिंह'
        ],

        /* ============ Thai (th) — light ============ */
        th: [
            'ลิซ่า BLACKPINK','แบมแบม GOT7','นิชคุณ 2PM','มิวกี้ พัดซิต',
            'ใหม่ ดาวิกา','ญาญ่า อุรัสยา','คิมเบอร์ลี่ แอน','มิว นิษฐา','มิน พีชญา',
            'ณเดชน์ คูกิมิยะ','เจมส์ จิรายุ','ไบร์ท วชิรวิชญ์','วิน เมธวิน','ต่อ ธนภพ',
            'บัวขาว บัญชาเมฆ','สมจิตร จงจอหอ','รัชนก อินทนนท์','ราชนก อินทนนท์'
        ],

        /* ============ Indonesian (id) — light ============ */
        id: [
            'Raisa','Tulus','Rich Brian','Niki','Agnez Mo','Isyana Sarasvati','Afgan',
            'Iko Uwais','Joe Taslim','Reza Rahadian','Dian Sastrowardoyo','Luna Maya',
            'Maudy Ayunda','Raline Shah','Cinta Laura',
            'Witan Sulaeman','Pratama Arhan','Marselino Ferdinan','Egy Maulana','Rizky Ridho',
            'Greysia Polii','Apriyani Rahayu','Jonatan Christie','Anthony Ginting'
        ],

        /* ============ Vietnamese (vi) — light ============ */
        vi: [
            'Quang Hải','Công Phượng','Tiến Linh','Văn Hậu','Văn Lâm','Xuân Trường','Hùng Dũng',
            'Nguyễn Thùy Linh','Lê Quang Liêm','Hoàng Xuân Vinh',
            'Sơn Tùng M-TP','Jack','K-ICM','Đen Vâu','Hương Tràm','Mỹ Tâm','Hồ Ngọc Hà',
            'Trấn Thành','Trường Giang','Ngô Thanh Vân','Chi Pu','Ninh Dương Lan Ngọc'
        ],

        /* ============ Turkish (tr) — light ============ */
        tr: [
            'Arda Güler','Hakan Çalhanoğlu','Mert Günok','Kerem Aktürkoğlu','Burak Yılmaz',
            'Cenk Tosun','Merih Demiral','Yusuf Yazıcı',
            'Tarkan','Sezen Aksu','Murat Boz','Hadise','Demet Akalın','Ebru Gündeş',
            'Kıvanç Tatlıtuğ','Burak Özçivit','Çağatay Ulusoy','Can Yaman',
            'Tuba Büyüküstün','Beren Saat','Hande Erçel','Serenay Sarıkaya'
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
