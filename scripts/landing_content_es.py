# -*- coding: utf-8 -*-
"""스페인어 도구 랜딩 콘텐츠. gen-landing-i18n.py 가 읽는다.

키 순서 = 페이지 하단 상호 링크 순서. 메인 6종 순서와 맞춘다.
`sections` 는 그 도구에서만 얻는 내용(정보 이득)을 담는 자유 HTML.
"""

CONTENT = {}

CONTENT["roulette"] = dict(
    h1="Ruleta de Nombres",
    short="Escribe nombres, gira y sale uno al azar.",
    title="Ruleta de Nombres Online Gratis — Girar y Elegir al Azar | Lucky Please",
    description="Ruleta de nombres gratis para elegir al azar. Escribe las opciones, gira y sale una. Sin registro, funciona en el móvil y se comparte con un toque.",
    keywords="ruleta de nombres, ruleta aleatoria, girar la ruleta, ruleta online gratis, sorteo de nombres, elegir al azar, ruleta para decidir, sorteador de nombres, quien paga",
    og_title="Ruleta de Nombres Online Gratis",
    og_desc="Escribe nombres, gira y deja que la ruleta elija. Gratis y sin registro.",
    lead="Escribe cualquier lista de nombres u opciones, gira, y la ruleta elige una. Sin registro y sin instalar nada: funciona aquí mismo en el navegador del móvil o del ordenador.",
    steps=[
        "<b>Escribe las opciones.</b> Nombres de personas, restaurantes, tareas, premios: lo que sea que haya que repartir.",
        "<b>Gira.</b> Toca la ruleta o el botón. Acelera, frena y se detiene en un sector al azar.",
        "<b>Lee el resultado.</b> La aguja marca el sector ganador. Puedes volver a girar las veces que quieras.",
        "<b>Compártelo.</b> Un enlace de un toque enseña el mismo resultado a quien no estaba mirando.",
    ],
    uses=[
        ("Quién paga", "La ronda de café, la cena o la cuenta del bar."),
        ("Decidir sin discutir", "Qué comer, qué ver, a dónde ir."),
        ("En clase", "Sacar a alguien a la pizarra o elegir al siguiente en exponer."),
        ("Sorteos", "Mete los nombres de los participantes y saca un ganador en directo."),
        ("Turnos", "Quién empieza la partida o quién friega hoy."),
        ("Desempates", "Cualquier discusión de dos, o de diez, en un solo giro."),
    ],
    sections="""    <h2>Por qué una ruleta y no un número al azar</h2>
    <p>Cualquier generador de números aleatorios haría el mismo trabajo en una línea de código, y sin embargo nadie lo usa para decidir quién paga. El motivo no es matemático sino social: la decisión necesita ser <b>presenciada</b>. Cuando todo el grupo mira cómo la misma ruleta va frenando, el resultado deja de pertenecer a una persona y pasa a pertenecer al procedimiento. Nadie puede decir "lo has elegido tú" porque todos estaban delante.</p>
    <p>De ahí que la animación no sea un adorno. Es la parte que hace que el resultado se acepte sin discusión, y por eso conviene girar con el móvil a la vista de todos y no en el bolsillo.</p>

    <h2>Cómo de justo es en realidad</h2>
    <p>Cada giro usa el generador de números aleatorios del propio navegador. Todos los sectores tienen el mismo tamaño y la misma probabilidad, y da igual dónde esté cada nombre en la rueda. Con <i>n</i> opciones, cada una tiene 1/<i>n</i> en cada giro.</p>
    <p>Un detalle que provoca muchas acusaciones injustas: los giros son <b>independientes</b>. Salir una vez no reduce tu probabilidad en el siguiente giro. Con seis personas, que a la misma le toque dos veces seguidas tiene una probabilidad de 1 entre 36, así que en una noche cualquiera le pasará a alguien. Si quieres que quien ya salió deje de participar, bórralo de la lista antes de volver a girar: la ruleta no lo hace sola a propósito.</p>
""",
    faq=[
        ("¿La ruleta es gratis?",
         "Sí, es totalmente gratis y sin registro. Abre la página, escribe tus opciones y gira."),
        ("¿El giro es realmente aleatorio?",
         "Sí. Cada giro usa el generador de números aleatorios del navegador, así que todas las opciones tienen la misma probabilidad de salir."),
        ("¿Cuántos nombres puedo añadir?",
         "Los que quieras. La ruleta ajusta el tamaño de cada sector automáticamente para que todas las entradas se sigan leyendo."),
        ("¿Funciona en el móvil?",
         "Sí. Está diseñada primero para pantalla de móvil y escala a tableta y ordenador, sin instalar nada."),
        ("¿Puedo compartir el resultado?",
         "Sí. Después de girar obtienes un enlace de un toque y quien lo abra verá exactamente el mismo resultado."),
        ("¿Hace falta crear una cuenta?",
         "No. Girar no requiere iniciar sesión. La cuenta solo sirve para extras opcionales como guardar grupos o las salas multijugador."),
    ],
)

CONTENT["team"] = dict(
    h1="Sorteo de Equipos",
    short="Pega una lista y divídela en equipos equilibrados.",
    title="Sorteo de Equipos Aleatorio — Generador de Equipos Gratis | Lucky Please",
    description="Generador de equipos aleatorio y gratuito. Pega la lista de participantes y se divide en grupos equilibrados al instante. Sin registro, funciona en cualquier móvil.",
    keywords="sorteo de equipos, generador de equipos, dividir en equipos, hacer equipos aleatorios, sortear grupos, formar grupos al azar, repartir equipos, generador de grupos",
    og_title="Sorteo de Equipos Aleatorio — Generador Gratis",
    og_desc="Pega la lista y se divide en equipos equilibrados al instante. Gratis y sin registro.",
    lead="Pega la lista de participantes, elige cuántos equipos quieres y el reparto se hace solo. Equipos del mismo tamaño, sin que nadie del grupo haya tocado nada.",
    steps=[
        "<b>Pega la lista.</b> Un nombre por línea, tal cual lo tengas en el móvil o en una hoja.",
        "<b>Elige cuántos equipos.</b> El reparto mantiene los grupos del mismo tamaño y coloca el resto donde toque.",
        "<b>Sortea.</b> Cada nombre cae en un equipo al azar, a la vista de todos.",
        "<b>Reparte el enlace.</b> Quien lo abra ve la misma composición, así que no hay versiones distintas circulando.",
    ],
    uses=[
        ("Partidos", "Fútbol sala, pádel, baloncesto en el parque."),
        ("Trabajos de clase", "Grupos de proyecto sin que nadie se quede el último."),
        ("Juegos de mesa", "Repartir parejas o bandos antes de empezar."),
        ("Dinámicas de empresa", "Mezclar departamentos que nunca se hablan."),
        ("Campamentos", "Cabañas, turnos de cocina, equipos de gymkhana."),
        ("Torneos", "Cuadros iniciales sin que nadie proteste por el sorteo."),
    ],
    sections="""    <h2>El problema no es el reparto, es quién lo hizo</h2>
    <p>Cualquiera sabe dividir doce nombres en tres grupos. Lo que cuesta es que nadie sospeche. En cuanto una persona del grupo hace el reparto a mano, aparecen las lecturas: que si los amigos han caído juntos, que si el equipo fuerte se ha quedado con los mejores. El sorteo automático elimina esa conversación entera porque ninguno de los presentes tuvo la oportunidad de influir.</p>
    <p>Por eso conviene sortear <b>delante de todos</b> y no llegar con los equipos ya hechos. El valor de la herramienta está en el momento del reparto, no en la lista final.</p>

    <h2>Equipos iguales y qué pasa con el resto</h2>
    <p>Cuando el número de personas no es divisible entre el número de equipos, alguien tiene que jugar con uno más. El reparto distribuye ese sobrante en lugar de amontonarlo: con trece personas en cuatro equipos salen grupos de 4, 3, 3 y 3, nunca uno de 7 y tres de 2.</p>
    <p>Si necesitas equipos <i>equilibrados por nivel</i> y no solo por tamaño, el sorteo puro no es la herramienta adecuada: divide a ciegas, que es justo lo que lo hace incuestionable. Lo habitual en ese caso es sortear dos capitanes con la ruleta y que ellos elijan por turnos.</p>
""",
    faq=[
        ("¿Es gratis el sorteo de equipos?",
         "Sí, es gratuito, sin registro y sin instalación. Pega la lista y sortea."),
        ("¿Los equipos salen del mismo tamaño?",
         "Sí. Cuando el número de participantes no es divisible entre el de equipos, el sobrante se reparte entre varios grupos en lugar de acumularse en uno solo."),
        ("¿Puedo repetir el sorteo?",
         "Sí, las veces que quieras. Cada sorteo es independiente del anterior, así que dos repartos seguidos no tienen por qué parecerse."),
        ("¿Equilibra por nivel de los jugadores?",
         "No. El reparto es puramente aleatorio, que es precisamente lo que hace que nadie pueda cuestionarlo. Si necesitas equilibrar por nivel, lo habitual es sortear capitanes y que elijan por turnos."),
        ("¿Cuántas personas admite?",
         "Suficientes para una clase o una plantilla completa. Pega la lista entera y el reparto se hace de una vez."),
        ("¿Puedo compartir los equipos?",
         "Sí. Un enlace de un toque muestra la misma composición a todo el mundo, así que no circulan versiones distintas."),
    ],
)

CONTENT["dice"] = dict(
    h1="Tirar Dados Online",
    short="Lanza de uno a seis dados con tirada física.",
    title="Tirar Dados Online Gratis — Dado Virtual de 1 a 6 Dados | Lucky Please",
    description="Tira dados online gratis con una tirada física real. De uno a seis dados, sin registro y sin instalar nada. Ideal para juegos de mesa a los que se les perdió el dado.",
    keywords="tirar dados online, dado virtual, lanzar dados, dado online gratis, tirar dado 6 caras, dados 3d online, simulador de dados, dado aleatorio",
    og_title="Tirar Dados Online Gratis — Dado Virtual",
    og_desc="Lanza de uno a seis dados con tirada física. Gratis, sin registro.",
    lead="De uno a seis dados que ruedan de verdad antes de parar. Para la partida a la que se le perdió el dado, y para cualquier cosa que se resuelva antes con dos números que con una discusión.",
    steps=[
        "<b>Elige cuántos dados.</b> De uno a seis, según lo que pida la partida.",
        "<b>Lanza.</b> Los dados ruedan y se detienen solos, como sobre una mesa.",
        "<b>Lee el total.</b> Se muestran las caras y la suma, sin tener que sumar de cabeza.",
        "<b>Vuelve a tirar.</b> Cada tirada es independiente de la anterior.",
    ],
    uses=[
        ("Juegos de mesa", "Parchís, Monopoly, rol: el dado que siempre acaba debajo del sofá."),
        ("Desempatar", "El número más alto gana y se acabó la discusión."),
        ("Prendas y castigos", "El más bajo paga, invita o cumple la prenda."),
        ("Deberes de clase", "Probabilidad con dos dados, en directo y sin material."),
        ("Rol de mesa", "Tiradas rápidas cuando falta el set completo."),
        ("Elegir un número", "Del 1 al 6 sin pensarlo demasiado."),
    ],
    sections="""    <h2>Un dado y dos dados no se parecen en nada</h2>
    <p>Con un solo dado, los seis resultados son igual de probables: cada cara tiene 1 entre 6. Es la forma más limpia de repartir seis opciones.</p>
    <p>Con dos dados, la cosa cambia por completo y mucha gente lo usa mal. Hay 36 combinaciones posibles, pero solo una suma 2 (1+1) y solo una suma 12 (6+6), mientras que el 7 sale de seis maneras distintas (1+6, 2+5, 3+4 y sus simétricas). Es decir, <b>el 7 es seis veces más probable que el 12</b>. Si estás repartiendo premios por la suma de dos dados, no estás repartiendo a partes iguales aunque lo parezca.</p>
    <p>La regla práctica: para sortear entre opciones equiprobables, usa <b>un</b> dado y asigna una opción a cada cara. Los dos dados son para jugar, no para repartir.</p>

    <h2>Por qué la tirada tarda</h2>
    <p>El número está decidido en el instante en que pulsas, y aun así el dado rueda un segundo largo antes de parar. Es intencionado. Una cifra que aparece de golpe se lee como una salida de ordenador y siempre queda la duda de si alguien la ha tocado; un dado que rueda y se detiene se lee como algo que ha ocurrido. Cuando el resultado decide quién paga, esa diferencia es la razón de existir de la herramienta.</p>
""",
    faq=[
        ("¿Es gratis?",
         "Sí, es gratuito, sin registro y sin instalación. Elige cuántos dados y lanza."),
        ("¿Cuántos dados puedo tirar a la vez?",
         "De uno a seis. Se muestran todas las caras y la suma total, sin tener que sumar a mano."),
        ("¿La tirada es realmente aleatoria?",
         "Sí. Cada tirada usa el generador de números aleatorios del navegador, y las seis caras tienen la misma probabilidad."),
        ("¿Sirve para repartir entre seis opciones?",
         "Sí, con un solo dado, asignando una opción a cada cara. Con dos dados no reparte a partes iguales: el 7 sale seis veces más a menudo que el 12."),
        ("¿Puedo usarlo para juegos de rol?",
         "Sirve para tiradas de seis caras. Si tu partida necesita dados de otras caras, esta herramienta no las cubre."),
        ("¿Funciona sin conexión una vez abierto?",
         "La tirada ocurre en tu propio navegador, así que no depende de ningún servidor mientras la página siga abierta."),
    ],
)

CONTENT["bingo"] = dict(
    h1="Bingo Online: Bombo Automático",
    short="Canta números sin repetir y con el historial a la vista.",
    title="Bombo de Bingo Online Gratis — Cantar Números al Azar | Lucky Please",
    description="Bombo de bingo online gratis. Saca números al azar sin repetir, deja el historial en pantalla y se ve desde el fondo de la sala. Sin registro ni instalación.",
    keywords="bingo online gratis, bombo de bingo, cantar bingo online, generador de numeros bingo, bingo virtual, sacar numeros bingo, bingo para clase",
    og_title="Bombo de Bingo Online Gratis",
    og_desc="Saca números sin repetir y deja el historial en pantalla. Gratis, sin registro.",
    lead="Saca números al azar, nunca repite uno y deja todos los cantados a la vista para que quien se despiste pueda ponerse al día. Sustituye al bombo, no a los cartones.",
    steps=[
        "<b>Ponlo en la pantalla más grande que tengas.</b> Un portátil en el proyector o una tableta apoyada: el historial se queda visible todo el rato.",
        "<b>Saca un número.</b> Sale de los que aún no han salido, así que repetir es imposible y no hay que comprobarlo a mano.",
        "<b>Cántalo dos veces y espera.</b> La queja más habitual en una partida en directo no es el ritmo lento, es el rápido.",
        "<b>Comprueba contra el historial.</b> Cuando alguien cante, repasa su cartón con la lista de la pantalla. Esa lista es el acta.",
    ],
    uses=[
        ("En clase", "Bingo de vocabulario o de tablas de multiplicar con las manos libres."),
        ("Asociaciones", "Partidas benéficas y de club que tienen cartones pero no bombo."),
        ("Fiestas de empresa", "Cenas de Navidad y dinámicas de presentación."),
        ("Residencias", "Aquí lo que importa de verdad es el tamaño del número en pantalla."),
        ("Reuniones familiares", "El bombo está en el trastero; los cartones no."),
        ("Por videollamada", "Comparte pantalla y todos ven la misma bola a la vez."),
    ],
    sections="""    <h2>Bingo de 75 y de 90 bolas: no son intercambiables</h2>
    <p>En España y Latinoamérica lo más extendido es el <b>bingo de 90 bolas</b>, con cartón de 9&times;3 y quince números, que suele jugarse por fases: línea, dos líneas y bingo (cartón lleno). Los cartones se venden en tiras de seis que entre todas contienen los noventa números exactamente una vez, y por eso con una tira completa siempre marcas algo en cada bola.</p>
    <p>El <b>bingo de 75 bolas</b>, habitual en Norteamérica, usa un cartón de 5&times;5 con casilla libre en el centro y reparte los números por columnas: B va del 1 al 15, I del 16 al 30, N del 31 al 45, G del 46 al 60 y O del 61 al 75. Por eso allí se canta la letra junto al número, lo que permite mirar una sola columna en vez del cartón entero.</p>
    <p>Decide el formato antes de empezar, porque cambia lo que dura la partida.</p>

    <h2>Cuánto dura realmente una partida</h2>
    <p>Es la pregunta que más se falla al organizar un evento. En el bingo de 90 bolas, la primera línea suele caer alrededor de la vigésima bola y el cartón lleno hacia la cincuentena. En el de 75, una línea sencilla cae entre la decimoquinta y la vigesimoquinta, y el cartón completo necesita casi todas las bolas.</p>
    <p>Dos consecuencias prácticas. La primera: <b>cuanta más gente, más corta es la partida</b>, no más larga, porque con más cartones en juego alguien completa el patrón antes. La segunda: si tienes que rellenar un hueco de tiempo concreto, ajusta el <i>patrón</i> y no el ritmo. Pasar de cartón lleno a línea reduce la partida a la mitad de forma mucho más fiable que cantar más rápido.</p>
""",
    faq=[
        ("¿El bombo de bingo es gratis?",
         "Sí, es gratuito, sin registro y sin instalación. Abre la página y empieza a cantar."),
        ("¿Puede salir dos veces el mismo número?",
         "No. Los números se sacan sin reposición, así que una vez cantado sale del bombo y no puede repetirse en la misma partida. Eso es lo que diferencia un bombo de un generador de números al azar."),
        ("¿Se ven los números ya cantados?",
         "Sí. Todos los números salidos se quedan en pantalla, de modo que quien se haya despistado puede ponerse al día y puedes comprobar un cartón ganador contra el registro."),
        ("¿Sirve con cartones de papel?",
         "Sí. Sustituye al bombo y a las bolas, no a los cartones. Funciona con cualquier juego de cartones impresos."),
        ("¿Se puede usar en un proyector o compartiendo pantalla?",
         "Sí. Escala desde el móvil hasta un proyector, así que puedes ponerlo en la pantalla grande de la sala o compartirlo en una videollamada."),
        ("¿Cuántas bolas dura una partida normal?",
         "En el bingo de 90 bolas, la primera línea suele caer sobre la bola veinte y el cartón lleno hacia la cincuenta. En el de 75, una línea cae entre la quince y la veinticinco."),
    ],
)

CONTENT["car-racing"] = dict(
    h1="Carrera Aleatoria: Sorteo con Orden Completo",
    short="Convierte el sorteo en una carrera con orden de llegada.",
    title="Carrera Aleatoria Online — Sorteo con Orden de Llegada | Lucky Please",
    description="Un sorteo que se resuelve como una carrera y te da el orden completo de llegada, no solo un ganador. Gratis, sin registro, funciona en cualquier móvil.",
    keywords="carrera aleatoria, sorteo con orden, ordenar al azar, generador de orden aleatorio, sortear turnos, orden de exposicion al azar, clasificacion aleatoria",
    og_title="Carrera Aleatoria — Sorteo con Orden de Llegada",
    og_desc="El sorteo se resuelve como una carrera y da la clasificación completa. Gratis.",
    lead="Casi todos los sorteos responden a &laquo;&iquest;qui&eacute;n?&raquo;. Este responde a &laquo;&iquest;en qu&eacute; orden?&raquo;: cada nombre corre por su calle y al final tienes una clasificaci&oacute;n entera, no un solo ganador.",
    steps=[
        "<b>Escribe los nombres.</b> A cada uno se le asigna una calle. La calle no influye en el resultado.",
        "<b>Arranca la carrera.</b> Las posiciones cambian hasta el final; ver los adelantamientos es justo lo que se busca.",
        "<b>Lee la clasificación.</b> Del primero al último. Una sola carrera resuelve un calendario entero.",
        "<b>Comparte el resultado.</b> Un enlace reproduce el mismo orden para quien no lo vio.",
    ],
    uses=[
        ("Orden de exposiciones", "Una carrera reparte todos los turnos de una vez."),
        ("Turnos de juego", "Quién empieza y quién va después."),
        ("Tareas de casa", "Ordena a la familia y baja por la lista cada semana."),
        ("Drafts", "Ligas de fantasy y equipos improvisados que necesitan orden de elección."),
        ("Karaoke", "Quién canta primero y quién va detrás del que canta bien."),
        ("La cuenta", "El último paga, o el primero elige sitio la próxima vez."),
    ],
    sections="""    <h2>Una lista barajada y una carrera dan lo mismo, pero no se reciben igual</h2>
    <p>Estadísticamente son idénticas. La diferencia está entera en cómo las recibe el grupo. Una lista aparece ya hecha e invita a preguntar cómo se ha decidido. Una carrera se mira de principio a fin, así que cuando el orden existe todo el mundo ya lo ha visto producirse. Nadie pregunta cómo se decidió porque estaban delante.</p>
    <p>Eso pesa sobre todo en la posición que de verdad importa, que casi siempre es la última. Que te digan que eres el último en una lista se siente arbitrario. Verte adelantado en la recta final se siente como algo que ha pasado. Mismo resultado, recepción muy distinta.</p>

    <h2>Las matemáticas de un orden al azar</h2>
    <p>Con <i>n</i> participantes hay <i>n</i>! órdenes posibles y todos son igual de probables. La cifra crece más deprisa de lo que la intuición espera: cinco nombres dan 120 órdenes, ocho dan 40.320 y diez superan los tres millones y medio. A partir de seis participantes, repetir exactamente la misma clasificación es prácticamente imposible.</p>
    <p>Conviene saberlo por si alguien acusa a la carrera de estar amañada: cada participante tiene 1/<i>n</i> de acabar primero, 1/<i>n</i> de acabar último y 1/<i>n</i> de cualquier puesto intermedio. Ni la calle, ni el orden en que escribiste los nombres, ni la longitud del nombre influyen. Y si alguien queda último dos veces seguidas, es esperable: con seis personas eso ocurre 1 de cada 36 veces, así que en una tarde le pasará a alguien.</p>

    <h2>Cuándo no usarla</h2>
    <p>La carrera dura alrededor de medio minuto, a propósito. Esa lentitud solo compensa si el grupo está mirando. Si cada uno está a lo suyo, o si solo necesitas un nombre para rellenar un formulario, usa la ruleta: responde en dos segundos. La carrera es para cuando el público es el punto.</p>
""",
    faq=[
        ("¿Es gratis?",
         "Sí, es gratuito, sin registro y sin instalación. Escribe los nombres y arranca la carrera."),
        ("¿El orden de llegada es realmente aleatorio?",
         "Sí. Cada participante tiene la misma probabilidad de cualquier puesto. Ni la calle, ni el orden en que escribiste los nombres, ni su longitud influyen en el resultado."),
        ("¿En qué se diferencia de la ruleta?",
         "La ruleta elige un ganador en unos dos segundos. La carrera produce una clasificación completa, del primero al último, en torno a medio minuto. Usa la ruleta si necesitas un nombre y la carrera si necesitas un orden."),
        ("¿Cuánta gente puede correr a la vez?",
         "La suficiente para un grupo o una clase. Cada participante tiene su propia calle y la clasificación final los recoge a todos."),
        ("¿Puedo compartir la clasificación?",
         "Sí. Al terminar obtienes un enlace de un toque y quien lo abra ve exactamente el mismo orden de llegada."),
        ("¿Por qué siempre queda último el mismo?",
         "Es más normal de lo que parece. Con seis participantes, que a uno concreto le toque ser último dos veces seguidas ocurre 1 de cada 36 veces, así que a lo largo de una tarde le pasará a alguien. Cada carrera es independiente de la anterior."),
    ],
)

CONTENT["ladder"] = dict(
    h1="Escalera Aleatoria (Amidakuji)",
    short="Ghost leg / amidakuji: elige tu línea antes de ver los caminos.",
    title="Escalera Aleatoria Online — Amidakuji y Ghost Leg Gratis | Lucky Please",
    description="Escalera aleatoria online, también conocida como amidakuji o ghost leg. Cada persona elige su línea antes de revelar los caminos. Gratis, sin registro, en cualquier móvil.",
    keywords="escalera aleatoria, amidakuji, ghost leg, sorteo escalera, reparto aleatorio, asignar tareas al azar, sorteo amigo invisible, escalera de la suerte",
    og_title="Escalera Aleatoria Online — Amidakuji y Ghost Leg",
    og_desc="Elige tu línea antes de que aparezcan los caminos. Gratis, sin registro.",
    lead="Cada persona se queda con una l&iacute;nea de arriba antes de que se vea ning&uacute;n travesa&ntilde;o. Luego aparecen los caminos y cada l&iacute;nea lleva a un sitio distinto. En Jap&oacute;n se llama <i>amidakuji</i> y en ingl&eacute;s ghost leg.",
    steps=[
        "<b>Pon abajo lo que se reparte.</b> Premios, tareas, papeles, quién paga qué.",
        "<b>Que cada uno elija su línea primero.</b> Esta es la parte importante: se comprometen antes de ver nada.",
        "<b>Revela la escalera.</b> Aparecen los travesaños horizontales, generados al azar.",
        "<b>Sigue el camino hacia abajo.</b> Cada vez que te cruzas con un travesaño pasas a la línea de al lado y sigues bajando.",
    ],
    uses=[
        ("Repartir tareas", "Cada uno recibe una y ninguna se queda sin dueño."),
        ("Amigo invisible", "Empareja quien regala con quien recibe en una sola pasada."),
        ("Dividir una cuenta desigual", "Pon abajo importes distintos en lugar de nombres."),
        ("Papeles en clase", "Reparte temas o funciones de grupo sin discusión."),
        ("Quién paga qué", "Uno la cuenta, otro la propina y el resto se libra."),
        ("Puestos de equipo", "Asignaciones que tienen que ser uno a uno."),
    ],
    sections="""    <h2>Lo que la distingue de una ruleta</h2>
    <p>La escalera no es otra forma de elegir al azar: produce una <b>correspondencia uno a uno</b>. Cada persona cae en exactamente un resultado y cada resultado se lo lleva exactamente una persona. Ninguno se duplica y ninguno se queda sin repartir.</p>
    <p>Una ruleta no puede hacer eso. Si giras seis veces para repartir seis tareas, lo más probable es que alguna salga dos veces mientras otra se queda sin nadie, y tendrías que ir borrando manualmente entre giro y giro. La escalera lo resuelve por construcción, y por eso es la herramienta correcta cuando lo de abajo es un conjunto que hay que repartir y no una bolsa de la que sacar.</p>
    <p>El motivo matemático es elegante: cada travesaño intercambia dos líneas contiguas, y por muchos intercambios que encadenes el resultado sigue siendo una permutación. Añadir travesaños no puede romper la propiedad uno a uno, solo mezclarla más.</p>

    <h2>Por qué hay que elegir la línea antes</h2>
    <p>La verdadera ventaja de la escalera no es matemática sino de procedimiento. Los participantes eligen su línea <i>antes</i> de que existan los caminos. Eso significa que cada uno tomó una decisión real y que nadie, tampoco quien organiza, podía saber a dónde llevaba.</p>
    <p>Ahí se desactiva la sospecha de tongo que cualquier sorteo arrastra. Con una ruleta, el desconfiado tiene que fiarse de la herramienta. Con una escalera solo tiene que fiarse de que los travesaños no estaban a la vista cuando eligió, y eso lo comprueba con sus propios ojos. Por eso el formato lleva siglos usándose en Japón y Corea justo para las decisiones más delicadas.</p>
""",
    faq=[
        ("¿Qué es una escalera aleatoria?",
         "Es una herramienta de reparto al azar, conocida como amidakuji en Japón y ghost leg en inglés. Cada persona elige una línea arriba antes de que se muestren los travesaños horizontales y luego sigue el camino hasta el resultado al que llega."),
        ("¿Es gratis?",
         "Sí, es gratuita, sin registro y sin instalación. Pon los resultados abajo, que cada uno coja su línea y revela la escalera."),
        ("¿En qué se diferencia de la ruleta?",
         "La escalera produce una correspondencia uno a uno: cada persona recibe exactamente un resultado y cada resultado se asigna una sola vez. La ruleta puede repetir el mismo resultado en giros sucesivos y dejar otro sin asignar."),
        ("¿El resultado es realmente aleatorio?",
         "Sí. Los travesaños se generan al azar y no se muestran hasta que todo el mundo ha elegido su línea de salida, así que ninguna posición de partida es mejor que otra."),
        ("¿Por qué hay que elegir la línea antes de revelar la escalera?",
         "Ese orden es lo que hace convincente el sorteo. Cada participante decide en un momento en que nadie, tampoco quien organiza, puede saber a dónde lleva esa línea, lo que elimina la sospecha de que el reparto estuviera preparado."),
        ("¿Sirve para el amigo invisible?",
         "Sí, es uno de sus usos más habituales, porque garantiza que cada persona regale a una sola y reciba de una sola."),
    ],
)
