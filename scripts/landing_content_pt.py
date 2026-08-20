# -*- coding: utf-8 -*-
"""포르투갈어(브라질 기준) 도구 랜딩 콘텐츠. gen-landing-i18n.py 가 읽는다.

pt-BR 을 기준으로 쓴다 — 포르투갈어권 인터넷 사용자와 AdSense 인벤토리
양쪽 모두 브라질이 압도적이다. 어휘도 브라질 쪽을 택한다
(예: "time"(브라질) vs "equipa"(포르투갈)).
"""

CONTENT = {}

CONTENT["roulette"] = dict(
    h1="Roleta de Nomes",
    short="Digite nomes, gire e um sai sorteado.",
    title="Roleta de Nomes Online Grátis — Girar e Sortear | Lucky Please",
    description="Roleta de nomes grátis para sortear na hora. Digite as opções, gire e uma sai. Sem cadastro, funciona no celular e o resultado se compartilha com um toque.",
    keywords="roleta de nomes, roleta online gratis, sortear nomes, girar roleta, sorteador de nomes, roleta aleatoria, sorteio online, quem paga a conta",
    og_title="Roleta de Nomes Online Grátis",
    og_desc="Digite nomes, gire e deixe a roleta escolher. Grátis e sem cadastro.",
    lead="Digite qualquer lista de nomes ou opções, gire, e a roleta escolhe uma. Sem cadastro e sem instalar nada: roda aqui mesmo no navegador do celular ou do computador.",
    steps=[
        "<b>Digite as opções.</b> Nomes de pessoas, restaurantes, tarefas, prêmios: o que precisar ser sorteado.",
        "<b>Gire.</b> Toque na roleta ou no botão. Ela acelera, desacelera e para em uma fatia aleatória.",
        "<b>Leia o resultado.</b> O ponteiro marca a fatia sorteada. Pode girar quantas vezes quiser.",
        "<b>Compartilhe.</b> Um link de um toque mostra o mesmo resultado para quem não estava olhando.",
    ],
    uses=[
        ("Quem paga", "O café, o rodízio ou a conta do bar."),
        ("Decidir sem discutir", "O que comer, o que assistir, para onde ir."),
        ("Na sala de aula", "Chamar alguém ao quadro ou definir quem apresenta agora."),
        ("Sorteios", "Coloque os nomes dos participantes e sorteie ao vivo."),
        ("Ordem de jogada", "Quem começa a partida ou quem lava a louça hoje."),
        ("Desempate", "Qualquer discussão de dois — ou de dez — em um único giro."),
    ],
    sections="""    <h2>Por que uma roleta e não um número aleatório</h2>
    <p>Qualquer gerador de números aleatórios faria o mesmo trabalho em uma linha de código, e mesmo assim ninguém usa isso para decidir quem paga. O motivo não é matemático, é social: a decisão precisa ser <b>testemunhada</b>. Quando o grupo inteiro vê a mesma roleta desacelerando, o resultado deixa de pertencer a uma pessoa e passa a pertencer ao procedimento. Ninguém pode dizer "foi você que escolheu" porque todos estavam ali.</p>
    <p>Por isso a animação não é enfeite. É a parte que faz o resultado ser aceito sem discussão, e é por isso que vale girar com o celular à vista de todos, não no bolso.</p>

    <h2>Quão justo é de verdade</h2>
    <p>Cada giro usa o gerador de números aleatórios do próprio navegador. Todas as fatias têm o mesmo tamanho e a mesma probabilidade, e não importa onde cada nome está na roda. Com <i>n</i> opções, cada uma tem 1/<i>n</i> a cada giro.</p>
    <p>Um detalhe que gera muita acusação injusta: os giros são <b>independentes</b>. Ter saído uma vez não diminui sua chance no giro seguinte. Com seis pessoas, a mesma sair duas vezes seguidas tem chance de 1 em 36, então em uma noite qualquer isso vai acontecer com alguém. Se você quer que quem já saiu pare de participar, apague o nome da lista antes de girar de novo: a roleta não faz isso sozinha, de propósito.</p>
""",
    faq=[
        ("A roleta é grátis?",
         "Sim, é totalmente grátis e sem cadastro. Abra a página, digite suas opções e gire."),
        ("O giro é realmente aleatório?",
         "Sim. Cada giro usa o gerador de números aleatórios do navegador, então todas as opções têm a mesma chance de sair."),
        ("Quantos nomes posso adicionar?",
         "Quantos quiser. A roleta ajusta o tamanho de cada fatia automaticamente para que todas as entradas continuem legíveis."),
        ("Funciona no celular?",
         "Sim. Foi feita primeiro para tela de celular e escala para tablet e computador, sem instalar nada."),
        ("Posso compartilhar o resultado?",
         "Sim. Depois de girar você recebe um link de um toque, e quem abrir verá exatamente o mesmo resultado."),
        ("Preciso criar uma conta?",
         "Não. Girar não exige login. A conta serve apenas para extras opcionais, como salvar grupos ou as salas multijogador."),
    ],
)

CONTENT["team"] = dict(
    h1="Sorteio de Times",
    short="Cole uma lista e divida em times equilibrados.",
    title="Sorteio de Times Aleatório — Dividir Grupos Grátis | Lucky Please",
    description="Sorteador de times grátis. Cole a lista de participantes e ela é dividida em grupos do mesmo tamanho na hora. Sem cadastro, funciona em qualquer celular.",
    keywords="sorteio de times, dividir times, sortear grupos, gerador de times, formar times aleatorios, dividir grupos aleatorios, sorteador de equipes",
    og_title="Sorteio de Times Aleatório — Grátis",
    og_desc="Cole a lista e divida em times equilibrados na hora. Grátis e sem cadastro.",
    lead="Cole a lista de participantes, escolha quantos times você quer e a divisão sai pronta. Times do mesmo tamanho, sem que ninguém do grupo tenha encostado.",
    steps=[
        "<b>Cole a lista.</b> Um nome por linha, do jeito que já estiver no celular ou na planilha.",
        "<b>Escolha quantos times.</b> A divisão mantém os grupos do mesmo tamanho e distribui a sobra.",
        "<b>Sorteie.</b> Cada nome cai em um time aleatoriamente, à vista de todos.",
        "<b>Passe o link.</b> Quem abrir vê a mesma formação, então não circulam versões diferentes.",
    ],
    uses=[
        ("Pelada", "Futebol, vôlei, basquete na quadra do prédio."),
        ("Trabalho de escola", "Grupos de projeto sem ninguém sobrar por último."),
        ("Jogos de tabuleiro", "Dividir duplas ou lados antes de começar."),
        ("Dinâmica de empresa", "Misturar setores que nunca se falam."),
        ("Acampamento", "Barracas, escala de cozinha, times de gincana."),
        ("Torneios", "Chaveamento inicial sem ninguém reclamar do sorteio."),
    ],
    sections="""    <h2>O problema não é a divisão, é quem fez</h2>
    <p>Qualquer um sabe dividir doze nomes em três grupos. O difícil é que ninguém desconfie. No momento em que alguém do grupo faz a divisão na mão, aparecem as leituras: que os amigos caíram juntos, que o time forte ficou com os melhores. O sorteio automático elimina essa conversa inteira porque nenhum dos presentes teve chance de influenciar.</p>
    <p>Por isso vale sortear <b>na frente de todo mundo</b> e não chegar com os times prontos. O valor da ferramenta está no momento do sorteio, não na lista final.</p>

    <h2>Times iguais e o que acontece com a sobra</h2>
    <p>Quando o número de pessoas não é divisível pelo número de times, alguém joga com um a mais. A divisão espalha essa sobra em vez de amontoar: com treze pessoas em quatro times saem grupos de 4, 3, 3 e 3, nunca um de 7 e três de 2.</p>
    <p>Se você precisa de times <i>equilibrados por nível</i> e não só por tamanho, o sorteio puro não é a ferramenta certa: ele divide às cegas, que é justamente o que o torna inquestionável. O caminho usual nesse caso é sortear dois capitães na roleta e deixar que escolham alternadamente.</p>
""",
    faq=[
        ("O sorteio de times é grátis?",
         "Sim, é gratuito, sem cadastro e sem instalação. Cole a lista e sorteie."),
        ("Os times saem do mesmo tamanho?",
         "Sim. Quando o número de participantes não é divisível pelo número de times, a sobra é distribuída entre vários grupos em vez de se acumular em um só."),
        ("Posso sortear de novo?",
         "Sim, quantas vezes quiser. Cada sorteio é independente do anterior, então duas divisões seguidas não precisam se parecer."),
        ("Ele equilibra por nível dos jogadores?",
         "Não. A divisão é puramente aleatória, e é exatamente isso que impede qualquer contestação. Se você precisa equilibrar por nível, o caminho usual é sortear capitães e deixá-los escolher alternadamente."),
        ("Quantas pessoas cabem?",
         "O suficiente para uma turma inteira ou um elenco completo. Cole a lista toda e a divisão sai de uma vez."),
        ("Posso compartilhar os times?",
         "Sim. Um link de um toque mostra a mesma formação para todo mundo, então não circulam versões diferentes."),
    ],
)

CONTENT["dice"] = dict(
    h1="Rolar Dados Online",
    short="Role de um a seis dados com física de verdade.",
    title="Rolar Dados Online Grátis — Dado Virtual de 1 a 6 Dados | Lucky Please",
    description="Role dados online grátis com rolagem física de verdade. De um a seis dados, sem cadastro e sem instalar nada. Ideal para o jogo de tabuleiro que perdeu o dado.",
    keywords="rolar dados online, dado virtual, jogar dados online, dado online gratis, simulador de dados, dado 6 faces, dados 3d online, sortear numero dado",
    og_title="Rolar Dados Online Grátis — Dado Virtual",
    og_desc="Role de um a seis dados com física de verdade. Grátis, sem cadastro.",
    lead="De um a seis dados que rolam de verdade antes de parar. Para o jogo que perdeu o dado, e para qualquer coisa que se resolva mais rápido com dois números do que com uma discussão.",
    steps=[
        "<b>Escolha quantos dados.</b> De um a seis, conforme o jogo pedir.",
        "<b>Role.</b> Os dados rolam e param sozinhos, como sobre a mesa.",
        "<b>Leia o total.</b> Aparecem as faces e a soma, sem precisar somar de cabeça.",
        "<b>Role de novo.</b> Cada rolagem é independente da anterior.",
    ],
    uses=[
        ("Jogos de tabuleiro", "Banco Imobiliário, Ludo, RPG: o dado que sempre some."),
        ("Desempate", "O número mais alto ganha e acabou a discussão."),
        ("Prendas", "O mais baixo paga, convida ou cumpre a prenda."),
        ("Aula de matemática", "Probabilidade com dois dados, ao vivo e sem material."),
        ("RPG de mesa", "Rolagens rápidas quando falta o conjunto completo."),
        ("Escolher um número", "De 1 a 6 sem pensar muito."),
    ],
    sections="""    <h2>Um dado e dois dados não têm nada a ver</h2>
    <p>Com um dado só, os seis resultados são igualmente prováveis: cada face tem 1 em 6. É a forma mais limpa de sortear entre seis opções.</p>
    <p>Com dois dados muda tudo, e muita gente usa errado. São 36 combinações possíveis, mas só uma soma 2 (1+1) e só uma soma 12 (6+6), enquanto o 7 sai de seis jeitos diferentes (1+6, 2+5, 3+4 e os simétricos). Ou seja, <b>o 7 é seis vezes mais provável que o 12</b>. Se você está distribuindo prêmios pela soma de dois dados, não está distribuindo por igual, mesmo que pareça.</p>
    <p>A regra prática: para sortear entre opções de mesma chance, use <b>um</b> dado e atribua uma opção a cada face. Dois dados são para jogar, não para sortear.</p>

    <h2>Por que a rolagem demora</h2>
    <p>O número já está decidido no instante em que você toca, e mesmo assim o dado rola um segundo antes de parar. É de propósito. Um número que aparece de uma vez é lido como saída de computador e sempre fica a dúvida se alguém mexeu; um dado que rola e para é lido como algo que aconteceu. Quando o resultado decide quem paga, essa diferença é a razão de a ferramenta existir.</p>
""",
    faq=[
        ("É grátis?",
         "Sim, é gratuito, sem cadastro e sem instalação. Escolha quantos dados e role."),
        ("Quantos dados posso rolar de uma vez?",
         "De um a seis. Aparecem todas as faces e a soma total, sem precisar somar na mão."),
        ("A rolagem é realmente aleatória?",
         "Sim. Cada rolagem usa o gerador de números aleatórios do navegador, e as seis faces têm a mesma chance."),
        ("Serve para sortear entre seis opções?",
         "Sim, com um dado só, atribuindo uma opção a cada face. Com dois dados não sai por igual: o 7 aparece seis vezes mais que o 12."),
        ("Serve para RPG?",
         "Serve para rolagens de seis faces. Se a sua mesa precisa de dados com outro número de faces, esta ferramenta não cobre."),
        ("Funciona sem internet depois de aberto?",
         "A rolagem acontece no seu próprio navegador, então não depende de servidor enquanto a página continuar aberta."),
    ],
)

CONTENT["bingo"] = dict(
    h1="Bingo Online: Globo Automático",
    short="Cante números sem repetir e com o histórico na tela.",
    title="Globo de Bingo Online Grátis — Sortear Números | Lucky Please",
    description="Globo de bingo online grátis. Sorteia números sem repetir, mantém o histórico na tela e dá para ler do fundo da sala. Sem cadastro nem instalação.",
    keywords="bingo online gratis, globo de bingo, sortear numeros bingo, bingo virtual, cantar bingo online, gerador de numeros bingo, bingo para sala de aula",
    og_title="Globo de Bingo Online Grátis",
    og_desc="Sorteia números sem repetir e mantém o histórico na tela. Grátis, sem cadastro.",
    lead="Sorteia números, nunca repete um, e deixa todos os cantados à vista para quem se perdeu conseguir se achar. Substitui o globo, não as cartelas.",
    steps=[
        "<b>Coloque na maior tela que tiver.</b> Notebook no projetor ou tablet apoiado: o histórico fica visível o tempo todo.",
        "<b>Sorteie um número.</b> Ele sai de quem ainda não saiu, então repetir é impossível e não precisa conferir na mão.",
        "<b>Cante duas vezes e espere.</b> A reclamação mais comum numa partida ao vivo não é o ritmo lento, é o rápido.",
        "<b>Confira contra o histórico.</b> Quando alguém bater, confira a cartela pela lista na tela. Aquela lista é a ata.",
    ],
    uses=[
        ("Sala de aula", "Bingo de vocabulário ou de tabuada com as mãos livres."),
        ("Festa junina", "A quermesse tem cartela, mas o globo sumiu."),
        ("Confraternização", "Fim de ano e dinâmicas de integração."),
        ("Casas de repouso", "Aqui o que importa mesmo é o tamanho do número na tela."),
        ("Reunião de família", "As cartelas estão na gaveta; o globo, não."),
        ("Por videochamada", "Compartilhe a tela e todos veem a mesma bola ao mesmo tempo."),
    ],
    sections="""    <h2>Bingo de 75 e de 90 bolas: não dá para trocar</h2>
    <p>No Brasil o mais comum em festa junina e quermesse é a cartela impressa com faixa de 1 a 75 ou de 1 a 90, dependendo do jogo comprado, e vale conferir antes de começar porque muda tudo.</p>
    <p>O <b>bingo de 90 bolas</b> usa cartela de 9&times;3 com quinze números e costuma ser jogado em fases: linha, duas linhas e cartela cheia. As cartelas são vendidas em tiras de seis que juntas contêm os noventa números exatamente uma vez, e por isso com uma tira completa você marca alguma coisa em toda bola sorteada.</p>
    <p>O <b>bingo de 75 bolas</b> usa cartela de 5&times;5 com espaço livre no centro e separa os números por coluna: B de 1 a 15, I de 16 a 30, N de 31 a 45, G de 46 a 60 e O de 61 a 75. Por isso lá se canta a letra junto com o número, o que deixa o jogador olhar uma coluna só em vez da cartela inteira.</p>

    <h2>Quanto tempo uma partida leva de verdade</h2>
    <p>É a conta que mais se erra ao organizar um evento. No bingo de 90 bolas, a primeira linha costuma cair por volta da vigésima bola e a cartela cheia lá pela quinquagésima. No de 75, uma linha simples cai entre a décima quinta e a vigésima quinta, e a cartela completa precisa de quase todas as bolas.</p>
    <p>Duas consequências práticas. A primeira: <b>quanto mais gente, mais curta a partida</b>, não mais longa, porque com mais cartelas em jogo alguém fecha o padrão antes. A segunda: se você tem um horário fixo para preencher, ajuste o <i>padrão</i> e não o ritmo. Trocar cartela cheia por linha reduz a partida pela metade de forma muito mais confiável do que cantar mais rápido.</p>
""",
    faq=[
        ("O globo de bingo é grátis?",
         "Sim, é gratuito, sem cadastro e sem instalação. Abra a página e comece a cantar."),
        ("O mesmo número pode sair duas vezes?",
         "Não. Os números são sorteados sem reposição, então uma vez cantado ele sai do globo e não pode repetir na mesma partida. É isso que diferencia um globo de um gerador de números aleatórios."),
        ("Dá para ver os números já cantados?",
         "Sim. Todos os números sorteados ficam na tela, então quem se perdeu consegue se achar e você confere uma cartela vencedora contra o registro."),
        ("Funciona com cartela de papel?",
         "Sim. Ele substitui o globo e as bolas, não as cartelas. Funciona com qualquer conjunto de cartelas impressas."),
        ("Dá para usar em projetor ou compartilhando a tela?",
         "Sim. Escala do celular até um projetor, então você pode colocar na tela grande da sala ou compartilhar numa videochamada."),
        ("Quantas bolas dura uma partida normal?",
         "No bingo de 90 bolas, a primeira linha costuma cair por volta da bola vinte e a cartela cheia lá pela cinquenta. No de 75, uma linha cai entre a quinze e a vinte e cinco."),
    ],
)

CONTENT["car-racing"] = dict(
    h1="Corrida Aleatória: Sorteio com Ordem Completa",
    short="Transforme o sorteio em corrida com ordem de chegada.",
    title="Corrida Aleatória Online — Sorteio com Ordem de Chegada | Lucky Please",
    description="Um sorteio que roda como corrida e devolve a ordem completa de chegada, não só um vencedor. Grátis, sem cadastro, funciona em qualquer celular.",
    keywords="corrida aleatoria, sorteio com ordem, ordenar aleatoriamente, gerador de ordem aleatoria, sortear ordem de apresentacao, classificacao aleatoria, sortear turnos",
    og_title="Corrida Aleatória — Sorteio com Ordem de Chegada",
    og_desc="O sorteio roda como corrida e devolve a classificação completa. Grátis.",
    lead="Quase todo sorteio responde &laquo;quem?&raquo;. Este responde &laquo;em que ordem?&raquo;: cada nome corre na sua raia e no fim voc&ecirc; tem uma classifica&ccedil;&atilde;o inteira, n&atilde;o s&oacute; um vencedor.",
    steps=[
        "<b>Digite os nomes.</b> Cada um recebe uma raia. A raia não influencia o resultado.",
        "<b>Largue.</b> As posições mudam até o fim; ver as ultrapassagens é justamente o ponto.",
        "<b>Leia a classificação.</b> Do primeiro ao último. Uma corrida só resolve uma escala inteira.",
        "<b>Compartilhe.</b> Um link reproduz a mesma ordem para quem não viu.",
    ],
    uses=[
        ("Ordem de apresentação", "Uma corrida distribui todos os horários de uma vez."),
        ("Ordem de jogada", "Quem começa e quem vem depois."),
        ("Escala de tarefas", "Ordene a casa e desça pela lista a cada semana."),
        ("Draft", "Ligas de fantasy e times de pelada que precisam de ordem de escolha."),
        ("Karaokê", "Quem canta primeiro e quem vai depois do que canta bem."),
        ("A conta", "O último paga, ou o primeiro escolhe o lugar da próxima vez."),
    ],
    sections="""    <h2>Uma lista embaralhada e uma corrida dão o mesmo, mas não são recebidas igual</h2>
    <p>Estatisticamente são idênticas. A diferença está inteira em como o grupo recebe. Uma lista aparece pronta e convida à pergunta de como foi decidido. Uma corrida é assistida do início ao fim, então quando a ordem existe todo mundo já viu ela ser produzida. Ninguém pergunta como decidiu porque estava ali.</p>
    <p>Isso pesa principalmente na posição que realmente importa, que quase sempre é a última. Ser informado de que você é o último numa lista soa arbitrário. Ver-se ultrapassado na reta final soa como algo que aconteceu. Mesmo resultado, recepção bem diferente.</p>

    <h2>A matemática de uma ordem aleatória</h2>
    <p>Com <i>n</i> participantes há <i>n</i>! ordens possíveis, todas igualmente prováveis. O número cresce mais rápido do que a intuição espera: cinco nomes dão 120 ordens, oito dão 40.320 e dez passam de três milhões e meio. A partir de seis participantes, repetir exatamente a mesma classificação é praticamente impossível.</p>
    <p>Vale saber disso caso alguém acuse a corrida de ser viciada: cada participante tem 1/<i>n</i> de terminar em primeiro, 1/<i>n</i> de terminar em último e 1/<i>n</i> de qualquer posição no meio. Nem a raia, nem a ordem em que você digitou os nomes, nem o tamanho do nome influenciam. E se alguém ficar em último duas vezes seguidas, é esperado: com seis pessoas isso acontece 1 vez a cada 36, então ao longo de uma tarde vai acontecer com alguém.</p>

    <h2>Quando não usar</h2>
    <p>A corrida leva cerca de meio minuto, de propósito. Essa lentidão só compensa se o grupo estiver assistindo. Se cada um está no seu canto, ou se você só precisa de um nome para preencher um formulário, use a roleta: ela responde em dois segundos. A corrida é para quando a plateia é o ponto.</p>
""",
    faq=[
        ("É grátis?",
         "Sim, é gratuito, sem cadastro e sem instalação. Digite os nomes e largue a corrida."),
        ("A ordem de chegada é realmente aleatória?",
         "Sim. Cada participante tem a mesma chance de qualquer posição. Nem a raia, nem a ordem em que você digitou os nomes, nem o tamanho do nome influenciam o resultado."),
        ("Qual a diferença para a roleta?",
         "A roleta escolhe um vencedor em cerca de dois segundos. A corrida produz uma classificação completa, do primeiro ao último, em cerca de meio minuto. Use a roleta se precisa de um nome e a corrida se precisa de uma ordem."),
        ("Quantas pessoas podem correr de uma vez?",
         "O suficiente para um grupo ou uma turma. Cada participante tem a sua raia e a classificação final traz todos eles."),
        ("Posso compartilhar a classificação?",
         "Sim. Ao terminar você recebe um link de um toque, e quem abrir vê exatamente a mesma ordem de chegada."),
        ("Por que o mesmo sempre fica em último?",
         "É mais normal do que parece. Com seis participantes, um específico ficar em último duas vezes seguidas acontece 1 vez a cada 36, então ao longo de uma tarde vai acontecer com alguém. Cada corrida é independente da anterior."),
    ],
)

CONTENT["ladder"] = dict(
    h1="Escada Aleatória (Amidakuji)",
    short="Ghost leg / amidakuji: escolha sua linha antes de ver os caminhos.",
    title="Escada Aleatória Online — Amidakuji e Ghost Leg Grátis | Lucky Please",
    description="Escada aleatória online, também chamada de amidakuji ou ghost leg. Cada pessoa escolhe sua linha antes de os caminhos aparecerem. Grátis, sem cadastro.",
    keywords="escada aleatoria, amidakuji, ghost leg, sorteio escada, sorteio amigo secreto, distribuir tarefas aleatorio, sorteio um para um",
    og_title="Escada Aleatória Online — Amidakuji e Ghost Leg",
    og_desc="Escolha sua linha antes de os caminhos aparecerem. Grátis, sem cadastro.",
    lead="Cada pessoa fica com uma linha de cima antes de qualquer travessa aparecer. Depois os caminhos surgem e cada linha leva a um lugar diferente. No Jap&atilde;o chama-se <i>amidakuji</i>; em ingl&ecirc;s, ghost leg.",
    steps=[
        "<b>Coloque embaixo o que será distribuído.</b> Prêmios, tarefas, papéis, quem paga o quê.",
        "<b>Cada um escolhe a sua linha primeiro.</b> Esta é a parte que importa: comprometem-se antes de ver qualquer coisa.",
        "<b>Revele a escada.</b> As travessas horizontais aparecem, geradas aleatoriamente.",
        "<b>Siga o caminho para baixo.</b> A cada travessa você passa para a linha vizinha e continua descendo.",
    ],
    uses=[
        ("Distribuir tarefas", "Cada um recebe uma e nenhuma fica sem dono."),
        ("Amigo secreto", "Liga quem presenteia a quem recebe em uma passada só."),
        ("Dividir a conta de forma desigual", "Coloque valores diferentes embaixo em vez de nomes."),
        ("Papéis na sala", "Distribua temas ou funções de grupo sem discussão."),
        ("Quem paga o quê", "Um pega a conta, outro a gorjeta e o resto escapa."),
        ("Posições no time", "Atribuições que precisam ser um para um."),
    ],
    sections="""    <h2>O que a distingue de uma roleta</h2>
    <p>A escada não é mais um jeito de sortear: ela produz uma <b>correspondência um para um</b>. Cada pessoa cai em exatamente um resultado e cada resultado é levado por exatamente uma pessoa. Nenhum se duplica e nenhum sobra.</p>
    <p>Uma roleta não consegue fazer isso. Se você girar seis vezes para distribuir seis tarefas, muito provavelmente uma sairá duas vezes enquanto outra fica sem ninguém, e você teria que apagar manualmente entre um giro e outro. A escada resolve isso por construção, e por isso é a ferramenta certa quando o que está embaixo é um conjunto a distribuir e não um saco de onde tirar.</p>
    <p>O motivo matemático é elegante: cada travessa troca duas linhas vizinhas, e por mais trocas que você encadeie o resultado continua sendo uma permutação. Acrescentar travessas não quebra a propriedade um para um, só embaralha mais.</p>

    <h2>Por que escolher a linha antes</h2>
    <p>A verdadeira vantagem da escada não é matemática, é de procedimento. Os participantes escolhem a linha <i>antes</i> de os caminhos existirem. Isso significa que cada um tomou uma decisão real e que ninguém, nem quem organiza, podia saber aonde ela levava.</p>
    <p>É aí que se desarma a suspeita de armação que qualquer sorteio carrega. Com uma roleta, o desconfiado precisa confiar na ferramenta. Com uma escada ele só precisa confiar que as travessas não estavam à vista quando escolheu, e isso ele confere com os próprios olhos. Por isso o formato é usado há séculos no Japão e na Coreia justamente para as decisões mais delicadas.</p>
""",
    faq=[
        ("O que é uma escada aleatória?",
         "É uma ferramenta de distribuição aleatória, conhecida como amidakuji no Japão e ghost leg em inglês. Cada pessoa escolhe uma linha no topo antes de as travessas horizontais aparecerem e depois segue o caminho até o resultado onde chega."),
        ("É grátis?",
         "Sim, é gratuita, sem cadastro e sem instalação. Coloque os resultados embaixo, deixe cada um pegar a sua linha e revele a escada."),
        ("Qual a diferença para a roleta?",
         "A escada produz uma correspondência um para um: cada pessoa recebe exatamente um resultado e cada resultado é atribuído uma única vez. A roleta pode repetir o mesmo resultado em giros seguidos e deixar outro sem dono."),
        ("O resultado é realmente aleatório?",
         "Sim. As travessas são geradas aleatoriamente e não aparecem até que todos tenham escolhido a linha de partida, então nenhuma posição inicial é melhor que outra."),
        ("Por que escolher a linha antes de revelar a escada?",
         "Essa ordem é o que torna o sorteio convincente. Cada participante decide num momento em que ninguém, nem quem organiza, pode saber aonde aquela linha leva, o que elimina a suspeita de que a distribuição estivesse combinada."),
        ("Serve para amigo secreto?",
         "Sim, é um dos usos mais comuns, porque garante que cada pessoa presenteie uma só e receba de uma só."),
    ],
)
