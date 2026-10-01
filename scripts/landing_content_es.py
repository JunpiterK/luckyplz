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
    description="Ruleta de nombres gratis para elegir al azar. Escribe las opciones, gira y sale una. Sin registro, funciona en el celular y se comparte con un toque.",
    keywords="ruleta de nombres, ruleta aleatoria, girar la ruleta, ruleta online gratis, sorteo de nombres, elegir al azar, ruleta para decidir, sorteador de nombres, quien paga",
    og_title="Ruleta de Nombres Online Gratis",
    og_desc="Escribe nombres, gira y deja que la ruleta elija. Gratis y sin registro.",
    lead="Escribe cualquier lista de nombres u opciones, gira, y la ruleta elige una. Sin registro y sin instalar nada: funciona aquí mismo en el navegador del celular o de la computadora.",
    steps=[
        "<b>Escribe las opciones.</b> Nombres de personas, restaurantes, tareas, premios: lo que sea que haya que repartir.",
        "<b>Gira.</b> Toca la ruleta o el botón. Acelera, frena y se detiene en un sector al azar.",
        "<b>Lee el resultado.</b> La aguja marca el sector ganador. Puedes volver a girar las veces que quieras.",
        "<b>Compártelo.</b> El resultado se envía con un toque por WhatsApp, LINE u otra app; y si abres una sala, los demás ven el mismo giro en directo en su celular.",
    ],
    uses=[
        ("Quién paga", "La ronda de café, la cena o la cuenta del bar."),
        ("Decidir sin discutir", "Qué comer, qué ver, a dónde ir."),
        ("En clase", "Sacar a alguien al pizarrón o elegir al siguiente en exponer."),
        ("Sorteos", "Mete los nombres de los participantes y saca un ganador en vivo."),
        ("Turnos", "Quién empieza la partida o quién lava los platos hoy."),
        ("Desempates", "Cualquier discusión de dos, o de diez, en un solo giro."),
    ],
    sections="""    <h2>Por qué una ruleta y no un número al azar</h2>
    <p>Cualquier generador de números aleatorios haría el mismo trabajo en una línea de código, y sin embargo nadie lo usa para decidir quién paga. El motivo no es matemático sino social: la decisión necesita ser <b>presenciada</b>. Cuando todo el grupo mira cómo la misma ruleta va frenando, el resultado deja de pertenecer a una persona y pasa a pertenecer al procedimiento. Nadie puede decir "lo has elegido tú" porque todos estaban delante.</p>
    <p>De ahí que la animación no sea un adorno. Es la parte que hace que el resultado se acepte sin discusión, y por eso conviene girar con el celular a la vista de todos y no en el bolsillo.</p>

    <h2>Qué tan justo es en realidad</h2>
    <p>Cada giro usa el generador de números aleatorios del propio navegador. Todos los sectores tienen el mismo tamaño y la misma probabilidad, y da igual dónde esté cada nombre en la rueda. Con <i>n</i> opciones, cada una tiene 1/<i>n</i> en cada giro.</p>
    <p>Un detalle que provoca muchas acusaciones injustas: los giros son <b>independientes</b>. Salir una vez no reduce tu probabilidad en el siguiente giro. Con seis personas, que a la misma le toque dos veces seguidas tiene una probabilidad de 1 entre 36, así que en una noche cualquiera le pasará a alguien. Si quieres que quien ya salió deje de participar, bórralo de la lista antes de volver a girar: la ruleta no lo hace sola a propósito.</p>
""",
    faq=[
        ("¿La ruleta es gratis?",
         "Sí, es totalmente gratis y sin registro. Abre la página, escribe tus opciones y gira."),
        ("¿El giro es realmente aleatorio?",
         "Sí. Cada giro usa el generador de números aleatorios del navegador, así que todas las opciones tienen la misma probabilidad de salir."),
        ("¿Cuántos nombres puedo añadir?",
         "Hasta 30, suficiente para una clase entera. La ruleta ajusta el tamaño de cada sector automáticamente para que todas las entradas se sigan leyendo."),
        ("¿Funciona en el celular?",
         "Sí. Está diseñada primero para pantalla de celular y escala a tableta y computadora, sin instalar nada."),
        ("¿Puedo compartir el resultado?",
         "Sí. El resultado se envía con un toque por WhatsApp, LINE u otra app. En una sala, el enlace de resultado deja repetir el giro y comprobarlo."),
        ("¿Hace falta crear una cuenta?",
         "No. Ni girar ni abrir una sala para verlo juntos requieren iniciar sesión: en la sala basta un apodo. La cuenta solo sirve para guardar listas de nombres entre dispositivos."),
    ],
)

CONTENT["team"] = dict(
    h1="Sorteo de Equipos",
    short="Escribe los nombres y repártelos en equipos del mismo tamaño.",
    title="Sorteo de Equipos Aleatorio — Generador de Equipos Gratis | Lucky Please",
    description="Generador de equipos aleatorio y gratuito. Escribe hasta 40 participantes y se reparten en grupos del mismo tamaño, al azar o equilibrados por nivel. Sin registro, funciona en cualquier celular.",
    keywords="sorteo de equipos, generador de equipos, dividir en equipos, hacer equipos aleatorios, sortear grupos, formar grupos al azar, repartir equipos, generador de grupos",
    og_title="Sorteo de Equipos Aleatorio — Generador Gratis",
    og_desc="Escribe los nombres y se reparten en equipos parejos al instante. Gratis y sin registro.",
    lead="Escribe los participantes, elige cuántos equipos quieres y el reparto se hace solo. Equipos del mismo tamaño, sin que nadie del grupo haya tocado nada.",
    steps=[
        "<b>Escribe los nombres.</b> Hasta 40, uno por casilla. La última lista que usaste se recupera con un toque.",
        "<b>Elige cuántos equipos.</b> De 2 a 8, o cuántas personas por equipo. El reparto mantiene los grupos del mismo tamaño.",
        "<b>Sortea.</b> Una máquina de cápsulas va sacando los nombres equipo por equipo, a la vista de todos.",
        "<b>Comparte el resultado.</b> La composición completa va en el mensaje, así que no circulan versiones distintas. Con «Ver juntos», cada uno sigue el sorteo en directo en su celular.",
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
    <p>Si necesitas equipos <i>equilibrados por nivel</i> y no solo por tamaño, cambia al modo Por Nivel: marcas a cada jugador como T1, T2 o T3 y el reparto va pasando cada nivel por los equipos en turno rotatorio, barajando dentro de cada nivel. Así los fuertes no caen juntos y quién va con quién sigue siendo azar. El modo Aleatorio, en cambio, divide a ciegas, que es justo lo que lo hace incuestionable.</p>
""",
    faq=[
        ("¿Es gratis el sorteo de equipos?",
         "Sí, es gratuito, sin registro y sin instalación. Escribe los nombres y sortea."),
        ("¿Los equipos salen del mismo tamaño?",
         "Sí. Cuando el número de participantes no es divisible entre el de equipos, el sobrante se reparte entre varios grupos en lugar de acumularse en uno solo."),
        ("¿Puedo repetir el sorteo?",
         "Sí, las veces que quieras. Cada sorteo es independiente del anterior, así que dos repartos seguidos no tienen por qué parecerse."),
        ("¿Equilibra por nivel de los jugadores?",
         "Si lo pides. En el modo Por Nivel marcas a cada uno como T1, T2 o T3 y cada nivel se reparte por turnos entre los equipos, para que los mejores no acaben juntos. En el modo Aleatorio el reparto es ciego, que es lo que hace que nadie pueda cuestionarlo."),
        ("¿Cuántas personas admite?",
         "Hasta 40 participantes, en 2 a 8 equipos o en grupos de 2 a 8 personas. Suficiente para una clase o una plantilla completa."),
        ("¿Puedo compartir los equipos?",
         "Sí. La composición completa se envía con un toque por WhatsApp, LINE u otra app, así que no circulan versiones distintas."),
    ],
)

CONTENT["dice"] = dict(
    h1="Tirar Dados Online",
    short="Cada jugador tira de uno a tres dados y pierde el menor.",
    title="Tirar Dados Online Gratis — Dado Virtual y Duelo de Dados | Lucky Please",
    description="Tira dados online gratis con física real. De 2 a 12 jugadores, de uno a tres dados cada uno: pierde el número más bajo, o el más alto. Incluye el juego del Cerdo. Sin registro.",
    keywords="tirar dados online, dado virtual, lanzar dados, dado online gratis, tirar dado 6 caras, dados 3d online, simulador de dados, dado aleatorio",
    og_title="Tirar Dados Online Gratis — Dado Virtual",
    og_desc="Cada jugador tira de uno a tres dados y pierde el menor. Gratis, sin registro.",
    lead="Dados que ruedan de verdad antes de parar. Cada jugador tira de uno a tres y pierde el número más bajo (o el más alto, si lo prefieres). Para cualquier cosa que se resuelva antes con un par de números que con una discusión.",
    steps=[
        "<b>Escribe los jugadores.</b> De 2 a 12, y si quieres, la prenda o el premio de cada puesto.",
        "<b>Elige el modo.</b> Tiro rápido, de uno a tres dados por jugador, o el juego del Cerdo.",
        "<b>Agita y lanza.</b> Mantén pulsado para agitar y suelta para tirar. Los dados ruedan y se detienen solos.",
        "<b>Lee el resultado.</b> Se muestran las caras y la suma de cada uno. Si empatan en el puesto que pierde, los empatados vuelven a tirar.",
    ],
    uses=[
        ("Quién empieza", "Parchís, Monopoly: el que saque más sale primero."),
        ("Desempatar", "El número más alto gana y se acabó la discusión."),
        ("Prendas y castigos", "El más bajo paga, invita o cumple la prenda."),
        ("Deberes de clase", "Probabilidad con dos dados, en vivo y sin material."),
        ("Juego del Cerdo", "Arriesgar o plantarse: gana el primero en llegar a la meta."),
        ("La ronda del bar", "Quién paga la siguiente, en una sola tirada."),
    ],
    sections="""    <h2>Un dado y dos dados no se parecen en nada</h2>
    <p>Con un solo dado, los seis resultados son igual de probables: cada cara tiene 1 entre 6. Es la forma más limpia de repartir seis opciones.</p>
    <p>Con dos dados, la cosa cambia por completo y mucha gente lo usa mal. Hay 36 combinaciones posibles, pero solo una suma 2 (1+1) y solo una suma 12 (6+6), mientras que el 7 sale de seis maneras distintas (1+6, 2+5, 3+4 y sus simétricas). Es decir, <b>el 7 es seis veces más probable que el 12</b>. Si estás repartiendo premios por la suma de dos dados, no estás repartiendo a partes iguales aunque lo parezca.</p>
    <p>La regla práctica: para sortear entre opciones equiprobables, usa <b>un</b> dado y asigna una opción a cada cara. Los dos dados son para jugar, no para repartir.</p>

    <h2>El juego del Cerdo y la regla de los 20</h2>
    <p>En el Cerdo tiras un dado las veces que quieras y vas sumando, pero si sale un 1 pierdes todo lo del turno. La cuenta es sencilla: con <i>t</i> puntos acumulados, tirar otra vez gana de media 4 puntos en cinco de cada seis casos y te cuesta <i>t</i> en el sexto, así que solo compensa mientras <i>t</i> sea menor que 20. Por eso plantarse hacia los 20 puntos por turno es la estrategia que más rinde.</p>

    <h2>Por qué la tirada tarda</h2>
    <p>El número está decidido en el instante en que pulsas, y aun así el dado rueda un segundo largo antes de parar. Es intencionado. Una cifra que aparece de golpe se lee como una salida de computadora y siempre queda la duda de si alguien la ha tocado; un dado que rueda y se detiene se lee como algo que ha ocurrido. Cuando el resultado decide quién paga, esa diferencia es la razón de existir de la herramienta.</p>
""",
    faq=[
        ("¿Es gratis?",
         "Sí, es gratuito, sin registro y sin instalación. Escribe los jugadores y lanza."),
        ("¿Cuántos dados puedo tirar a la vez?",
         "De uno a tres por jugador en el Tiro rápido, con hasta 12 jugadores en la misma tirada. Se muestran las caras y la suma de cada uno. El juego del Cerdo usa un solo dado."),
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
    lead="Saca números al azar, nunca repite uno y deja todos los cantados a la vista para que quien se despiste pueda ponerse al día. Con cartones de papel hace de bombo; en una sala, cada jugador recibe su cartón en el celular.",
    steps=[
        "<b>Elige el rango y la pantalla.</b> De 1 a 75 o de 1 a 90, según tus cartones, en la pantalla más grande que tengas: el historial se queda visible todo el rato.",
        "<b>Saca un número.</b> A mano o en automático cada pocos segundos. Sale de los que aún no han salido, así que repetir es imposible.",
        "<b>Cántalo dos veces y espera.</b> La queja más habitual en una partida en vivo no es el ritmo lento, es el rápido.",
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
    <p>El bombo canta los dos: elige el rango 1–75 o 1–90 antes de empezar, porque el formato cambia lo que dura la partida.</p>

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
         "Sí. En el modo Sin conexión la página solo canta números, sin repartir cartones: elige el rango de los tuyos (1–75 o 1–90) y funciona con cualquier juego de cartones impresos."),
        ("¿Se puede usar en un proyector o compartiendo pantalla?",
         "Sí. Escala desde el celular hasta un proyector, así que puedes ponerlo en la pantalla grande de la sala o compartirlo en una videollamada."),
        ("¿Cuántas bolas dura una partida normal?",
         "En el bingo de 90 bolas, la primera línea suele caer sobre la bola veinte y el cartón lleno hacia la cincuenta. En el de 75, una línea cae entre la quince y la veinticinco."),
    ],
)

CONTENT["car-racing"] = dict(
    h1="Carrera Aleatoria: Sorteo con Orden Completo",
    short="Convierte el sorteo en una carrera con orden de llegada.",
    title="Carrera Aleatoria Online — Sorteo con Orden de Llegada | Lucky Please",
    description="Un sorteo que se resuelve como una carrera y te da el orden completo de llegada, no solo un ganador. Gratis, sin registro, funciona en cualquier celular.",
    keywords="carrera aleatoria, sorteo con orden, ordenar al azar, generador de orden aleatorio, sortear turnos, orden de exposicion al azar, clasificacion aleatoria",
    og_title="Carrera Aleatoria — Sorteo con Orden de Llegada",
    og_desc="El sorteo se resuelve como una carrera y da la clasificación completa. Gratis.",
    lead="Casi todos los sorteos responden a &laquo;&iquest;qui&eacute;n?&raquo;. Este responde a &laquo;&iquest;en qu&eacute; orden?&raquo;: cada nombre es un coche y al final tienes una clasificaci&oacute;n entera, no un solo ganador.",
    steps=[
        "<b>Escribe los nombres.</b> De 2 a 12. A cada uno le toca un coche y la posición de salida se sortea, así que el orden en que los escribes no influye.",
        "<b>Arranca la carrera.</b> Con objetos y adelantamientos, las posiciones cambian hasta el final, y una llegada apretada se ve a cámara lenta.",
        "<b>Lee la clasificación.</b> Del primero al último. Una sola carrera resuelve un calendario entero.",
        "<b>Comparte el resultado.</b> La clasificación completa va en el mensaje; en una sala, todos ven la carrera en directo.",
    ],
    uses=[
        ("Orden de exposiciones", "Una carrera reparte todos los turnos de una vez."),
        ("Turnos de juego", "Quién empieza y quién va después."),
        ("Tareas de casa", "Ordena a la familia y baja por la lista cada semana."),
        ("Drafts", "Ligas de fantasy y equipos improvisados que necesitan orden de elección."),
        ("Karaoke", "Quién canta primero y quién va detrás del que canta bien."),
        ("La cuenta", "Reparte el importe por puestos, o que pague el último."),
    ],
    sections="""    <h2>Una lista barajada y una carrera dan lo mismo, pero no se reciben igual</h2>
    <p>Estadísticamente son idénticas. La diferencia está entera en cómo las recibe el grupo. Una lista aparece ya hecha e invita a preguntar cómo se ha decidido. Una carrera se mira de principio a fin, así que cuando el orden existe todo el mundo ya lo ha visto producirse. Nadie pregunta cómo se decidió porque estaban delante.</p>
    <p>Eso pesa sobre todo en la posición que de verdad importa, que casi siempre es la última. Que te digan que eres el último en una lista se siente arbitrario. Verte adelantado en la recta final se siente como algo que ha pasado. Mismo resultado, recepción muy distinta.</p>

    <h2>Las matemáticas de un orden al azar</h2>
    <p>Con <i>n</i> participantes hay <i>n</i>! órdenes posibles y todos son igual de probables. La cifra crece más deprisa de lo que la intuición espera: cinco nombres dan 120 órdenes, ocho dan 40.320 y diez superan los tres millones y medio. A partir de seis participantes, repetir exactamente la misma clasificación es prácticamente imposible.</p>
    <p>Conviene saberlo por si alguien acusa a la carrera de estar amañada: cada participante tiene 1/<i>n</i> de acabar primero, 1/<i>n</i> de acabar último y 1/<i>n</i> de cualquier puesto intermedio. Ni la posición de salida, ni el orden en que escribiste los nombres, ni la longitud del nombre influyen. Y si alguien queda último dos veces seguidas, es esperable: con seis personas eso ocurre 1 de cada 36 veces, así que en una tarde le pasará a alguien.</p>

    <h2>Cuándo no usarla</h2>
    <p>Con los ajustes por defecto la carrera dura algo más de un minuto, a propósito. Esa lentitud solo compensa si el grupo está mirando. Si cada uno está a lo suyo, o si solo necesitas un nombre para rellenar un formulario, usa la ruleta: responde en unos segundos. La carrera es para cuando el público es el punto.</p>
""",
    faq=[
        ("¿Es gratis?",
         "Sí, es gratuito, sin registro y sin instalación. Escribe los nombres y arranca la carrera."),
        ("¿El orden de llegada es realmente aleatorio?",
         "Sí. Cada participante tiene la misma probabilidad de cualquier puesto. Ni la posición de salida, ni el orden en que escribiste los nombres, ni su longitud influyen en el resultado."),
        ("¿En qué se diferencia de la ruleta?",
         "La ruleta elige un ganador en unos segundos. La carrera produce una clasificación completa, del primero al último, en algo más de un minuto. Usa la ruleta si necesitas un nombre y la carrera si necesitas un orden."),
        ("¿Cuánta gente puede correr a la vez?",
         "De 2 a 12. Cada participante tiene su propio coche y la clasificación final los recoge a todos."),
        ("¿Puedo compartir la clasificación?",
         "Sí. Al terminar envías la clasificación completa con un toque por WhatsApp, LINE u otra app."),
        ("¿Por qué siempre queda último el mismo?",
         "Es más normal de lo que parece. Con seis participantes, que a uno concreto le toque ser último dos veces seguidas ocurre 1 de cada 36 veces, así que a lo largo de una tarde le pasará a alguien. Cada carrera es independiente de la anterior."),
    ],
)

CONTENT["ladder"] = dict(
    h1="Escalera Aleatoria (Amidakuji)",
    short="Ghost leg / amidakuji: elige tu línea antes de ver los caminos.",
    title="Escalera Aleatoria Online — Amidakuji y Ghost Leg Gratis | Lucky Please",
    description="Escalera aleatoria online, también conocida como amidakuji o ghost leg. Cada persona elige su línea antes de revelar los caminos. Gratis, sin registro, en cualquier celular.",
    keywords="escalera aleatoria, amidakuji, ghost leg, sorteo escalera, reparto aleatorio, asignar tareas al azar, sorteo amigo invisible, escalera de la suerte",
    og_title="Escalera Aleatoria Online — Amidakuji y Ghost Leg",
    og_desc="Elige tu línea antes de que aparezcan los caminos. Gratis, sin registro.",
    lead="Cada persona se queda con una l&iacute;nea de arriba antes de que se vea ning&uacute;n travesa&ntilde;o. Luego aparecen los caminos y cada l&iacute;nea lleva a un sitio distinto. En Jap&oacute;n se llama <i>amidakuji</i> y en ingl&eacute;s ghost leg.",
    steps=[
        "<b>Pon abajo lo que se reparte.</b> Premios, tareas, papeles, quién paga qué.",
        "<b>Que cada uno elija su línea primero.</b> Esta es la parte importante: se comprometen antes de ver nada.",
        "<b>Pulsa Empezar.</b> Aparecen los travesaños, generados al azar, y los resultados de abajo se barajan. Hasta 12 personas.",
        "<b>Sigue el camino hacia abajo.</b> Uno a uno, todos a la vez o en cadena. Cada travesaño te pasa a la línea de al lado.",
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
    <p>Además, al pulsar Empezar los resultados de abajo se barajan en posiciones nuevas. Aunque los travesaños se vean antes (en la vista previa de una pantalla grande), nadie puede dirigir el reparto: cada persona tiene exactamente 1/<i>n</i> de recibir cada resultado, tenga la escalera la forma que tenga.</p>
""",
    faq=[
        ("¿Qué es una escalera aleatoria?",
         "Es una herramienta de reparto al azar, conocida como amidakuji en Japón y ghost leg en inglés. Cada persona elige una línea arriba antes de que se muestren los travesaños horizontales y luego sigue el camino hasta el resultado al que llega."),
        ("¿Es gratis?",
         "Sí, es gratuita, sin registro y sin instalación. Pon los resultados abajo, que cada uno coja su línea y revela la escalera."),
        ("¿En qué se diferencia de la ruleta?",
         "La escalera produce una correspondencia uno a uno: cada persona recibe exactamente un resultado y cada resultado se asigna una sola vez. La ruleta puede repetir el mismo resultado en giros sucesivos y dejar otro sin asignar."),
        ("¿El resultado es realmente aleatorio?",
         "Sí. Los travesaños se generan al azar y, al empezar, los resultados de abajo se barajan en posiciones nuevas. Aunque alguien haya visto la escalera en la vista previa, cada persona tiene exactamente 1/n de recibir cada resultado."),
        ("¿Por qué hay que elegir la línea antes de revelar la escalera?",
         "Ese orden es lo que hace convincente el sorteo. Cada participante decide en un momento en que nadie, tampoco quien organiza, puede saber a dónde lleva esa línea, lo que elimina la sospecha de que el reparto estuviera preparado."),
        ("¿Sirve para el amigo invisible?",
         "Sí, es uno de sus usos más habituales, porque garantiza que cada persona regale a una sola y reciba de una sola. Con los mismos nombres arriba y abajo, en unos 2 de cada 3 sorteos a alguien le toca él mismo: entonces, repite."),
    ],
)
