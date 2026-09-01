import json
import pathlib

# Load dossiers
dossier_path = pathlib.Path(".work/competitive-v16/waves/wave3/dossiers/batch_2.json")
dossier_data = json.loads(dossier_path.read_text(encoding="utf-8"))
dossiers = dossier_data["dossiers"]

# Let's map wave_index or id to our authored questions
# 30 items: V16-R2-W3-031 to V16-R2-W3-060

authored = [
    # 031
    {
        "id": "V16-R2-W3-031",
        "question": "Según Daniel 9:3, ¿de qué manera y con qué elementos buscó Daniel a Dios el Señor?",
        "options": [
            "En oración y ruego, con ayuno, ropas ásperas y ceniza",
            "Con cantos y salmos, mediante vigilias, incienso y mirra",
            "En sacrificios y votos, con ofrendas, cilicio y libación",
            "Con lecturas y ayunos, usando mantos reales y holocaustos"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Con cantos y salmos, mediante vigilias, incienso y mirra": "Daniel 9:3 especifica oración, ruego, ayuno, ropas ásperas y ceniza, no cantos, vigilias ni incienso.",
            "En sacrificios y votos, con ofrendas, cilicio y libación": "El versículo no menciona sacrificios sacerdotales ni libaciones, sino oración, ruego, ayuno, ropas ásperas y ceniza.",
            "Con lecturas y ayunos, usando mantos reales y holocaustos": "El texto indica ropas ásperas y ceniza como señal de humillación, no mantos reales ni holocaustos."
        },
        "explanation": "Daniel 9:3 afirma textualmente: «Volví mi rostro a Dios, el Señor, buscándolo en oración y ruego, en ayuno, ropas ásperas y ceniza»."
    },
    # 032
    {
        "id": "V16-R2-W3-032",
        "question": "Según Daniel 9:4, ¿cómo describió Daniel a Dios al comenzar su oración y confesión?",
        "options": [
            "Rey eterno, lleno de paciencia, que corona a los reyes",
            "Dios grande, digno de ser temido, que guarda el pacto",
            "Juez severo, creador de los cielos, que juzga al impío",
            "Señor fuerte, dueño del universo, que guía a su pueblo"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Rey eterno, lleno de paciencia, que corona a los reyes": "Daniel 9:4 dice textualmente «Dios grande, digno de ser temido, que guardas el pacto», no alude a coronar reyes.",
            "Juez severo, creador de los cielos, que juzga al impío": "El texto inicial de la confesión no emplea estas expresiones sino «Dios grande, digno de ser temido».",
            "Señor fuerte, dueño del universo, que guía a su pueblo": "La invocación exacta en Daniel 9:4 es «Dios grande, digno de ser temido, que guardas el pacto y la misericordia»."
        },
        "explanation": "Daniel 9:4 registra: «Ahora, Señor, Dios grande, digno de ser temido, que guardas el pacto y la misericordia con los que te aman y guardan tus mandamientos»."
    },
    # 033
    {
        "id": "V16-R2-W3-033",
        "question": "¿Cuáles fueron las cuatro acciones iniciales de transgresión que Daniel confesó en Daniel 9:5?",
        "options": [
            "Olvidar la ley, quebrantar el pacto, murmurar y blasfemar",
            "Adorar ídolos, ofrecer sacrificios vanos, mentir y hurtar",
            "Pecar, cometer iniquidad, actuar impíamente y ser rebeldes",
            "Desobedecer la voz, seguir a extranjeros, quejarse y huir"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "Olvidar la ley, quebrantar el pacto, murmurar y blasfemar": "Daniel 9:5 enumera: «hemos pecado, hemos cometido iniquidad, hemos actuado impíamente, hemos sido rebeldes».",
            "Adorar ídolos, ofrecer sacrificios vanos, mentir y hurtar": "La confesión de Daniel 9:5 utiliza los verbos pecar, cometer iniquidad, actuar impíamente y ser rebeldes.",
            "Desobedecer la voz, seguir a extranjeros, quejarse y huir": "No son los términos iniciales expresados en la confesión de Daniel 9:5."
        },
        "explanation": "Daniel 9:5 expresa: «hemos pecado, hemos cometido iniquidad, hemos actuado impíamente, hemos sido rebeldes y nos hemos apartado de tus mandamientos y de tus ordenanzas»."
    },
    # 034
    {
        "id": "V16-R2-W3-034",
        "question": "Según Daniel 9:9, ¿qué atributos pertenecen a Jehová nuestro Dios a pesar de la rebelión del pueblo?",
        "options": [
            "El ejecutar justicia y el castigar",
            "El manifestar poder y el condenar",
            "El guardar silencio y el consumir",
            "El tener misericordia y el perdonar"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "El ejecutar justicia y el castigar": "Daniel 9:9 destaca específicamente que de Jehová es «el tener misericordia y el perdonar» frente a la rebelión.",
            "El manifestar poder y el condenar": "El pasaje no enfatiza condenación o poder destructor, sino misericordia y perdón divinos.",
            "El guardar silencio y el consumir": "El texto bíblico declara que a Dios corresponde la misericordia y el perdón, no guardar silencio ni consumir."
        },
        "explanation": "Daniel 9:9 afirma: «De Jehová, nuestro Dios, es el tener misericordia y el perdonar, aunque contra él nos hemos rebelado»."
    },
    # 035
    {
        "id": "V16-R2-W3-035",
        "question": "Según Daniel 9:17, ¿qué pidió Daniel que hiciera Dios con su rostro sobre el santuario asolado?",
        "options": [
            "Que hiciera resplandecer su rostro",
            "Que no apartara la mirada del altar",
            "Que ocultara su presencia del lugar",
            "Que volviera sus ojos con severidad"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Que no apartara la mirada del altar": "Daniel 9:17 pide específicamente: «haz que tu rostro resplandezca sobre tu santuario asolado».",
            "Que ocultara su presencia del lugar": "La oración busca el favor y resplandor divino sobre el santuario, no el ocultamiento de su presencia.",
            "Que volviera sus ojos con severidad": "Daniel suplica misericordia y gracia manifestada en el resplandor del rostro divino, no una mirada de severidad."
        },
        "explanation": "Daniel 9:17 declara: «haz que tu rostro resplandezca sobre tu santuario asolado, por amor del Señor»."
    },
    # 036
    {
        "id": "V16-R2-W3-036",
        "question": "Según Daniel 9:18, ¿qué elemento sagrado era invocado sobre la ciudad cuyas desolaciones Daniel pidió mirar?",
        "options": [
            "El pacto del templo",
            "El nombre de Jehová",
            "El fuego del altar",
            "El juicio de la ley"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "El pacto del templo": "Daniel 9:18 alude a «la ciudad sobre la cual es invocado tu nombre», no al pacto del templo.",
            "El fuego del altar": "El versículo no menciona el fuego del altar sino el nombre de Dios invocado sobre Jerusalén.",
            "El juicio de la ley": "El texto destaca que sobre la ciudad se invoca el nombre divino."
        },
        "explanation": "En Daniel 9:18, Daniel ruega: «mira nuestras desolaciones y la ciudad sobre la cual es invocado tu nombre»."
    },
    # 037
    {
        "id": "V16-R2-W3-037",
        "question": "Según Daniel 9:21, ¿de qué manera específica vino el varón Gabriel volando hacia Daniel mientras oraba?",
        "options": [
            "Volando con lentitud",
            "Descendiendo en nube",
            "Volando con presteza",
            "Caminando con gloria"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "Volando con lentitud": "Daniel 9:21 señala textualmente que Gabriel vino «volando con presteza».",
            "Descendiendo en nube": "El texto bíblico dice expresamente «volando con presteza», no descendiendo en una nube.",
            "Caminando con gloria": "El pasaje describe que Gabriel vino volando con presteza hacia el profeta."
        },
        "explanation": "Daniel 9:21 declara: «el varón Gabriel, a quien había visto en la visión, al principio, volando con presteza vino a mí como a la hora del sacrificio de la tarde»."
    },
    # 038
    {
        "id": "V16-R2-W3-038",
        "question": "En Daniel 9:4, ¿qué dos cosas guarda Dios con los que le aman y guardan sus mandamientos?",
        "options": [
            "La paz y el discernimiento",
            "El reino y la benevolencia",
            "La gracia y la prosperidad",
            "El pacto y la misericordia"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "La paz y el discernimiento": "Daniel 9:4 afirma que Dios guarda «el pacto y la misericordia», no la paz y el discernimiento.",
            "El reino y la benevolencia": "La confesión de Daniel menciona textualmente «el pacto y la misericordia».",
            "La gracia y la prosperidad": "El versículo resalta que Dios guarda el pacto y la misericordia con quienes le aman."
        },
        "explanation": "Daniel 9:4 dice expresamente: «que guardas el pacto y la misericordia con los que te aman y guardan tus mandamientos»."
    },
    # 039
    {
        "id": "V16-R2-W3-039",
        "question": "Según Daniel 9:21, ¿en qué momento del día vino Gabriel a Daniel mientras este oraba?",
        "options": [
            "Como a la hora del sacrificio de la tarde",
            "Durante el turno del holocausto nocturno",
            "Al tiempo fijado del sacrificio matutino",
            "En el momento del incienso de la mañana"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Durante el turno del holocausto nocturno": "Daniel 9:21 especifica «como a la hora del sacrificio de la tarde», no en un turno nocturno.",
            "Al tiempo fijado del sacrificio matutino": "Gabriel llegó a la hora del sacrificio de la tarde, no de la mañana.",
            "En el momento del incienso de la mañana": "El texto bíblico sitúa la llegada del ángel a la hora del sacrificio vespertino o de la tarde."
        },
        "explanation": "Daniel 9:21 afirma: «el varón Gabriel... vino a mí como a la hora del sacrificio de la tarde»."
    },
    # 040
    {
        "id": "V16-R2-W3-040",
        "question": "Según Daniel 9:23, ¿cuál fue la razón afectuosa que dio Gabriel para venir a enseñar la orden a Daniel?",
        "options": [
            "Porque tú eres fiel siervo",
            "Porque tú eres muy amado",
            "Porque tú fuiste escogido",
            "Porque tú tienes paciencia"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Porque tú eres fiel siervo": "Gabriel dijo explícitamente «porque tú eres muy amado», no por ser siervo fiel.",
            "Porque tú fuiste escogido": "El motivo expresado por el ángel en Daniel 9:23 es el entrañable amor divino: «porque tú eres muy amado».",
            "Porque tú tienes paciencia": "La razón dada por el ángel no fue la paciencia del profeta sino que era «muy amado»."
        },
        "explanation": "Daniel 9:23 declara: «yo he venido para enseñártela, porque tú eres muy amado»."
    },
    # 041
    {
        "id": "V16-R2-W3-041",
        "question": "Según Daniel 9:24, ¿qué tipo de justicia se traería dentro de los propósitos de las setenta semanas?",
        "options": [
            "La justicia transitoria",
            "La justicia sacerdotal",
            "La justicia perdurable",
            "La justicia ceremonial"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "La justicia transitoria": "Daniel 9:24 especifica «traer la justicia perdurable», que es eterna y definitiva, no pasajera.",
            "La justicia sacerdotal": "El texto no habla de una justicia sacerdotal, sino de traer «la justicia perdurable».",
            "La justicia ceremonial": "La profecía señala expresamente «la justicia perdurable», no un sistema ceremonial."
        },
        "explanation": "Daniel 9:24 enumera como uno de los objetivos de las setenta semanas: «para traer la justicia perdurable, sellar la visión y la profecía y ungir al Santo de los santos»."
    },
    # 042
    {
        "id": "V16-R2-W3-042",
        "question": "Según Daniel 9:8, ¿por qué causa correspondía la confusión de rostro al pueblo, reyes, príncipes y padres?",
        "options": [
            "Porque perdieron las tierras",
            "Porque temieron a los caldeos",
            "Porque huyeron de los juicios",
            "Porque pecaron contra Jehová"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "Porque perdieron las tierras": "Daniel 9:8 fundamenta la confusión de rostro en el pecado contra Dios: «porque contra ti pecamos».",
            "Porque temieron a los caldeos": "El texto no atribuye la vergüenza al miedo de los enemigos sino a su transgresión moral contra el Señor.",
            "Porque huyeron de los juicios": "La causa explícita en Daniel 9:8 es haber pecado contra Jehová."
        },
        "explanation": "Daniel 9:8 dice: «Nuestra es, Jehová, la confusión de rostro... porque contra ti pecamos»."
    },
    # 043
    {
        "id": "V16-R2-W3-043",
        "question": "En Daniel 9:11, ¿qué consecuencias cayeron sobre Israel por traspasar la Ley y no obedecer la voz de Dios?",
        "options": [
            "La maldición y el juramento escrito en la ley de Moisés",
            "El destierro perpetuo y la pérdida final del santuario",
            "La ruina económica y el olvido total de los mandamientos",
            "El desprecio de los reyes y la destrucción de la memoria"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "El destierro perpetuo y la pérdida final del santuario": "Daniel 9:11 menciona expresamente que cayó «la maldición y el juramento que está escrito en la ley de Moisés».",
            "La ruina económica y el olvido total de los mandamientos": "El pasaje no utiliza estas formulaciones, sino la maldición y el juramento consignados en la ley mosaica.",
            "El desprecio de los reyes y la destrucción de la memoria": "El texto bíblico identifica el juicio como el cumplimiento de la maldición y el juramento de la ley de Moisés."
        },
        "explanation": "Daniel 9:11 afirma: «Por lo cual ha caído sobre nosotros la maldición y el juramento que está escrito en la ley de Moisés, siervo de Dios, porque contra Dios pecamos»."
    },
    # 044
    {
        "id": "V16-R2-W3-044",
        "question": "Según Daniel 9:12, ¿qué afirmó Daniel respecto a la magnitud del mal traído sobre Jerusalén?",
        "options": [
            "Que ya había acontecido una ruina idéntica en reinos del desierto",
            "Que nunca fue hecho debajo del cielo nada semejante a lo ocurrido",
            "Que era un castigo menor en comparación con las plagas de Egipto",
            "Que muchos pueblos vecinos habían padecido desolaciones similares"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Que ya había acontecido una ruina idéntica en reinos del desierto": "Daniel 9:12 afirma lo contrario: «nunca fue hecho debajo del cielo nada semejante a lo que se ha hecho contra Jerusalén».",
            "Que era un castigo menor en comparación con las plagas de Egipto": "El versículo enfatiza la singularidad sin precedentes del juicio sobre Jerusalén.",
            "Que muchos pueblos vecinos habían padecido desolaciones similares": "El texto declara tajantemente que jamás se había hecho debajo del cielo algo comparable a lo sucedido contra Jerusalén."
        },
        "explanation": "Daniel 9:12 asegura: «pues nunca fue hecho debajo del cielo nada semejante a lo que se ha hecho contra Jerusalén»."
    },
    # 045
    {
        "id": "V16-R2-W3-045",
        "question": "A pesar del mal venido según la ley de Moisés, ¿qué actitud persistente del pueblo denunció Daniel en Daniel 9:13?",
        "options": [
            "Buscar auxilio en reyes extraños sin consultar a los levitas",
            "Reclamar justicia ante las naciones olvidando los sacrificios",
            "No implorar el favor de Jehová ni convertirse de sus maldades",
            "Ofrecer holocaustos continuos sin respetar el sábado de reposo"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "Buscar auxilio en reyes extraños sin consultar a los levitas": "Daniel 9:13 señala que no imploraron el favor de Jehová, no se convirtieron de sus maldades ni entendieron su verdad.",
            "Reclamar justicia ante las naciones olvidando los sacrificios": "La denuncia de Daniel 9:13 se enfoca en no buscar a Dios ni arrepentirse de la maldad moral.",
            "Ofrecer holocaustos continuos sin respetar el sábado de reposo": "El versículo no trata sobre rituales externos, sino sobre no implorar la gracia de Dios ni apartarse del pecado."
        },
        "explanation": "Daniel 9:13 declara: «todo este mal vino sobre nosotros; pero no hemos implorado el favor de Jehová, nuestro Dios, y no nos hemos convertido de nuestras maldades ni entendido tu verdad»."
    },
    # 046
    {
        "id": "V16-R2-W3-046",
        "question": "¿Cómo describe Daniel el carácter de Jehová al explicar por qué trajo el mal sobre su pueblo en Daniel 9:14?",
        "options": [
            "Severo e inflexible ante el ruego de los siervos",
            "Distante e indiferente a la suerte de su pueblo",
            "Airado y vengativo por la desobediencia sufrida",
            "Justo es Jehová nuestro Dios en todas sus obras"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "Severo e inflexible ante el ruego de los siervos": "Daniel 9:14 no describe a Dios como inflexible, sino que proclama: «justo es Jehová, nuestro Dios, en todas sus obras que ha hecho».",
            "Distante e indiferente a la suerte de su pueblo": "El texto muestra la justicia activa de Dios al velar sobre su palabra y ejecutar sus juicios.",
            "Airado y vengativo por la desobediencia sufrida": "La afirmación doctrinal central de Daniel 9:14 es la rectitud y justicia de Dios en todas sus obras."
        },
        "explanation": "Daniel 9:14 afirma: «Por tanto, Jehová veló sobre el mal y lo trajo sobre nosotros; porque justo es Jehová, nuestro Dios, en todas sus obras que ha hecho»."
    },
    # 047
    {
        "id": "V16-R2-W3-047",
        "question": "Según Daniel 9:15, ¿mediante qué manifestación de poder sacó Dios a su pueblo de la tierra de Egipto?",
        "options": [
            "Con mano poderosa haciéndose renombre",
            "Con carros de fuego guiando al pueblo",
            "Mediante grandes señales en el templo",
            "Por el auxilio de varios reyes amigos"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Con carros de fuego guiando al pueblo": "Daniel 9:15 afirma expresamente que Dios sacó a su pueblo «con mano poderosa y te hiciste renombre».",
            "Mediante grandes señales en el templo": "El texto alude a la liberación de Egipto con mano poderosa, mucho antes de la existencia del templo.",
            "Por el auxilio de varios reyes amigos": "El versículo atribuye la salvación exclusivamente a la mano poderosa de Dios, no a reyes humanos."
        },
        "explanation": "Daniel 9:15 recuerda: «Señor, Dios nuestro, que sacaste a tu pueblo de la tierra de Egipto con mano poderosa y te hiciste renombre cual lo tienes hoy»."
    },
    # 048
    {
        "id": "V16-R2-W3-048",
        "question": "En Daniel 9:16, ¿por qué causa llegaron Jerusalén y el pueblo a ser el oprobio de todos los que los rodeaban?",
        "options": [
            "Por la debilidad militar frente a los reinos vecinos",
            "Por los pecados propios y por la maldad de los padres",
            "Por la ruina de los muros y el colapso del comercio",
            "Por el pacto secreto hecho con los príncipes paganos"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Por la debilidad militar frente a los reinos vecinos": "Daniel 9:16 declara que el oprobio se debió a causas espirituales: «a causa de nuestros pecados y por la maldad de nuestros padres».",
            "Por la ruina de los muros y el colapso del comercio": "El oprobio no fue originado por factores materiales o comerciales, sino por la transgresión moral acumulada.",
            "Por el pacto secreto hecho con los príncipes paganos": "El texto bíblico identifica la culpa en los propios pecados y la iniquidad de los antepasados."
        },
        "explanation": "Daniel 9:16 afirma: «porque a causa de nuestros pecados y por la maldad de nuestros padres, Jerusalén y tu pueblo son el oprobio de todos los que nos rodean»."
    },
    # 049
    {
        "id": "V16-R2-W3-049",
        "question": "Al final de Daniel 9:17, ¿por consideración a quién rogó Daniel que resplandeciera el rostro divino sobre el santuario asolado?",
        "options": [
            "Por el amor a David",
            "Por la grey cautiva",
            "Por amor del Señor",
            "Por la casa de Judá"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "Por el amor a David": "Daniel 9:17 pide la restauración «por amor del Señor», no invocando méritos de David.",
            "Por la grey cautiva": "La súplica no se fundamenta en la compasión humana de los cautivos sino en la gloria y amor del Señor.",
            "Por la casa de Judá": "El texto bíblico concluye expresamente con la frase «por amor del Señor»."
        },
        "explanation": "Daniel 9:17 concluye rogando: «haz que tu rostro resplandezca sobre tu santuario asolado, por amor del Señor»."
    },
    # 050
    {
        "id": "V16-R2-W3-050",
        "question": "Según Daniel 9:22, ¿con qué propósito específico declaró Gabriel que había salido hacia Daniel?",
        "options": [
            "Para anunciarle el fin de Babilonia",
            "Para ordenar la reedificación santa",
            "Para revelarle la caída del enemigo",
            "Para darle sabiduría y entendimiento"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "Para anunciarle el fin de Babilonia": "Daniel 9:22 cita a Gabriel diciendo: «Daniel, ahora he salido para darte sabiduría y entendimiento».",
            "Para ordenar la reedificación santa": "El ángel vino directamente a instruir y dar entendimiento profético al profeta, no a dar órdenes de edificación.",
            "Para revelarle la caída del enemigo": "El objetivo declarado en este versículo es dotar a Daniel de sabiduría y entendimiento sobre la visión."
        },
        "explanation": "Daniel 9:22 registra las palabras de Gabriel: «Daniel, ahora he salido para darte sabiduría y entendimiento»."
    },
    # 051
    {
        "id": "V16-R2-W3-051",
        "question": "Según Daniel 9:27, ¿por cuánto tiempo se confirmará el pacto con muchos en el período profético final?",
        "options": [
            "Por otra semana más",
            "Por dos semanas más",
            "Por siete meses más",
            "Por tres años y más"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Por dos semanas más": "Daniel 9:27 especifica: «Por otra semana más confirmará el pacto con muchos».",
            "Por siete meses más": "La unidad de tiempo profético establecida en el versículo es una semana («otra semana más»).",
            "Por tres años y más": "El texto bíblico no utiliza años sino la expresión profética «otra semana más»."
        },
        "explanation": "Daniel 9:27 comienza diciendo: «Por otra semana más confirmará el pacto con muchos; a la mitad de la semana hará cesar el sacrificio y la ofrenda»."
    },
    # 052
    {
        "id": "V16-R2-W3-052",
        "question": "¿Sobre qué lugar asolado suplicó Daniel a Dios que hiciera resplandecer su rostro en Daniel 9:17?",
        "options": [
            "Sobre el muro quebrantado",
            "Sobre su santuario asolado",
            "Sobre el palacio derribado",
            "Sobre el vallado arruinado"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Sobre el muro quebrantado": "Daniel 9:17 especifica «sobre tu santuario asolado», no sobre los muros de la ciudad.",
            "Sobre el palacio derribado": "La oración se enfoca en el santuario de Dios, no en las residencias reales o palacios.",
            "Sobre el vallado arruinado": "El texto pide el favor de Dios directamente sobre su santo recinto sagrado («tu santuario asolado»)."
        },
        "explanation": "Daniel 9:17 dice: «haz que tu rostro resplandezca sobre tu santuario asolado, por amor del Señor»."
    },
    # 053
    {
        "id": "V16-R2-W3-053",
        "question": "Según Daniel 9:18, ¿qué acciones corporales metafóricas rogó Daniel a Dios que hiciera para atender la ruina del pueblo?",
        "options": [
            "Extender la mano y alzar el brazo",
            "Descubrir la faz y mover los pies",
            "Inclinar el oído y abrir los ojos",
            "Levantar la diestra y alzar la voz"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "Extender la mano y alzar el brazo": "Daniel 9:18 suplica textualmente: «Inclina, Dios mío, tu oído, y oye; abre tus ojos y mira nuestras desolaciones».",
            "Descubrir la faz y mover los pies": "El profeta implora a Dios que incline su oído para oír y abra sus ojos para mirar.",
            "Levantar la diestra y alzar la voz": "La petición apela a la escucha y contemplación compasiva de Dios: oído inclinado y ojos abiertos."
        },
        "explanation": "Daniel 9:18 inicia con las palabras: «Inclina, Dios mío, tu oído, y oye; abre tus ojos y mira nuestras desolaciones y la ciudad sobre la cual es invocado tu nombre»."
    },
    # 054
    {
        "id": "V16-R2-W3-054",
        "question": "En Daniel 9:19, ¿con qué apremiante expresión culmina Daniel la petición de acción divina tras pedir que preste oído?",
        "options": [
            "¡Presta oído, Señor, y juzga! ¡No calles!",
            "¡Presta oído, Señor, y sana! ¡No olvides!",
            "¡Presta oído, Señor, y reina! ¡No reposes!",
            "¡Presta oído, Señor, y hazlo! ¡No tardes!"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "¡Presta oído, Señor, y juzga! ¡No calles!": "Daniel 9:19 clama textualmente: «¡Presta oído, Señor, y hazlo! No tardes, por amor de ti mismo».",
            "¡Presta oído, Señor, y sana! ¡No olvides!": "La frase bíblica exacta es «¡Presta oído, Señor, y hazlo! No tardes».",
            "¡Presta oído, Señor, y reina! ¡No reposes!": "El texto contiene las exclamaciones de acción y no demora: «¡hazlo! No tardes»."
        },
        "explanation": "Daniel 9:19 expresa el clímax de la súplica: «¡Oye, Señor! ¡Señor, perdona! ¡Presta oído, Señor, y hazlo! No tardes, por amor de ti mismo, Dios mío»."
    },
    # 055
    {
        "id": "V16-R2-W3-055",
        "question": "Según Daniel 9:20, ¿por qué lugar sagrado específico derramaba Daniel su ruego delante de Jehová?",
        "options": [
            "Por el monte santo de mi Dios",
            "Por el valle del gran juicio",
            "Por el atrio mayor del templo",
            "Por los muros santos de Judá"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Por el valle del gran juicio": "Daniel 9:20 declara que oraba «por el monte santo de mi Dios», no por un valle de juicio.",
            "Por el atrio mayor del templo": "El texto bíblico usa la designación profética «por el monte santo de mi Dios».",
            "Por los muros santos de Judá": "Daniel dirigía su intercesión específicamente por el monte santo de Dios (el monte del templo en Jerusalén)."
        },
        "explanation": "Daniel 9:20 dice: «derramaba mi ruego delante de Jehová, mi Dios, por el monte santo de mi Dios»."
    },
    # 056
    {
        "id": "V16-R2-W3-056",
        "question": "¿Qué dos facultades espirituales e intelectuales vino a otorgar Gabriel a Daniel según Daniel 9:22?",
        "options": [
            "Fortaleza y discernimiento",
            "Sabiduría y entendimiento",
            "Autoridad y conocimientos",
            "Inspiración y consolación"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Fortaleza y discernimiento": "Daniel 9:22 cita a Gabriel diciendo: «ahora he salido para darte sabiduría y entendimiento».",
            "Autoridad y conocimientos": "La expresión textual del ángel une «sabiduría y entendimiento», no autoridad ni conocimientos.",
            "Inspiración y consolación": "El propósito explícito del emisario celestial fue impartir sabiduría y entendimiento al profeta."
        },
        "explanation": "Daniel 9:22 declara: «Daniel, ahora he salido para darte sabiduría y entendimiento»."
    },
    # 057
    {
        "id": "V16-R2-W3-057",
        "question": "Según Daniel 9:23, ¿en qué momento preciso de la oración de Daniel fue emitida la orden celestial?",
        "options": [
            "Al término de sus vigilias",
            "A la mitad de sus cánticos",
            "Al principio de sus ruegos",
            "Al momento de sus ofrendas"
        ],
        "correct_option": 2,
        "why_distractors_fail": {
            "Al término de sus vigilias": "Daniel 9:23 indica que la orden fue dada «al principio de tus ruegos», no al terminar.",
            "A la mitad de sus cánticos": "El texto señala el comienzo mismo de la intercesión («al principio de tus ruegos»)",
            "Al momento de sus ofrendas": "La orden celestial fue dictada tan pronto como Daniel comenzó a orar, no al ofrecer dones."
        },
        "explanation": "Daniel 9:23 afirma: «Al principio de tus ruegos fue dada la orden, y yo he venido para enseñártela»."
    },
    # 058
    {
        "id": "V16-R2-W3-058",
        "question": "En Daniel 9:25, ¿qué dos estructuras urbanas de Jerusalén se profetizó que se volverían a edificar en tiempos angustiosos?",
        "options": [
            "El templo y la torre del vigía",
            "Las casas y las puertas reales",
            "El palacio y los altos vallados",
            "La plaza y el muro de la ciudad"
        ],
        "correct_option": 3,
        "why_distractors_fail": {
            "El templo y la torre del vigía": "Daniel 9:25 especifica: «se volverán a edificar la plaza y el muro en tiempos angustiosos».",
            "Las casas y las puertas reales": "El texto profético menciona concretamente la plaza y el muro, no las casas ni puertas reales.",
            "El palacio y los altos vallados": "La profecía alude a la plaza y el muro de Jerusalén reedificados bajo condiciones de angustia."
        },
        "explanation": "Daniel 9:25 declara: «se volverán a edificar la plaza y el muro en tiempos angustiosos»."
    },
    # 059
    {
        "id": "V16-R2-W3-059",
        "question": "Según Daniel 9:26, ¿de qué manera figurada y arrolladora se describe que llegará el final de la destrucción?",
        "options": [
            "Llegará como una inundación",
            "Vendrá como una gran plaga",
            "Caerá como fuego del cielo",
            "Surgirá como un torbellino"
        ],
        "correct_option": 0,
        "why_distractors_fail": {
            "Vendrá como una gran plaga": "Daniel 9:26 describe metafóricamente que «su final llegará como una inundación».",
            "Caerá como fuego del cielo": "El versículo emplea la figura de una inundación arrasadora, no de fuego del cielo.",
            "Surgirá como un torbellino": "La comparación textual empleada por el profeta es la de una inundación."
        },
        "explanation": "Daniel 9:26 afirma: «El pueblo de un príncipe que ha de venir destruirá la ciudad y el santuario, su final llegará como una inundación»."
    },
    # 060
    {
        "id": "V16-R2-W3-060",
        "question": "¿En qué fundamento declaró Daniel que presentaban sus ruegos ante Dios en Daniel 9:18?",
        "options": [
            "Confiados en la piedad de los antepasados y en los sacrificios del templo",
            "Confiados no en justicias propias sino en las muchas misericordias de Dios",
            "Confiados en la fidelidad de los sacerdotes y en las oraciones continuas",
            "Confiados en el pacto de las obras santas y en los ayunos de los ancianos"
        ],
        "correct_option": 1,
        "why_distractors_fail": {
            "Confiados en la piedad de los antepasados y en los sacrificios del templo": "Daniel 9:18 descarta toda justicia o mérito humano, apelando únicamente a «tus muchas misericordias».",
            "Confiados en la fidelidad de los sacerdotes y en las oraciones continuas": "El profeta rechaza la confianza en obras o intermediarios humanos, descansando solo en la misericordia de Dios.",
            "Confiados en el pacto de las obras santas y en los ayunos de los ancianos": "El texto dice expresamente: «no elevamos nuestros ruegos ante ti confiados en nuestras justicias, sino en tus muchas misericordias»."
        },
        "explanation": "Daniel 9:18 subraya: «no elevamos nuestros ruegos ante ti confiados en nuestras justicias, sino en tus muchas misericordias»."
    }
]

# Validation and Merge
dossier_by_id = {d["id"]: d for d in dossiers}
final_items = []

for item in authored:
    d = dossier_by_id[item["id"]]
    opts = item["options"]
    c_idx = item["correct_option"]
    c_ans = opts[c_idx]
    
    # Check length symmetry
    lengths = [len(o) for o in opts]
    ratio = max(lengths) / min(lengths)
    assert ratio < 1.15, f"Length ratio {ratio:.3f} >= 1.15 for {item['id']}: {lengths}"
    
    # Check distractors
    distractors = [o for i, o in enumerate(opts) if i != c_idx]
    for dist in distractors:
        assert dist in item["why_distractors_fail"], f"Missing distractor '{dist}' in why_distractors_fail for {item['id']}"
    assert c_ans not in item["why_distractors_fail"], f"Correct answer '{c_ans}' should NOT be in why_distractors_fail for {item['id']}"
    
    full_item = {
        "id": d["id"],
        "question_id": d["question_id"],
        "fact_id": d["fact_id"],
        "chapter": d["chapter"],
        "source_unit_id": d["source_unit_id"],
        "source_ref": d["source_ref"],
        "source_quote": d["source_quote"],
        "source_page": d.get("source_page"),
        "family": d.get("family", "single_choice_contextual"),
        "lane": d.get("lane", "CARRIL_R2_COBERTURA"),
        "question": item["question"],
        "options": opts,
        "correct_option": c_idx,
        "correct_answer": c_ans,
        "accepted_answers": [c_ans],
        "why_distractors_fail": item["why_distractors_fail"],
        "explanation": item["explanation"],
        "difficulty": "medium",
        "importance": "high"
    }
    final_items.append(full_item)

print(f"Validated {len(final_items)} items successfully!")
out_dir = pathlib.Path(".work/competitive-v16/waves/wave3/authors/author_2")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "batch_2.json"
out_file.write_text(json.dumps(final_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote final authored batch to {out_file}")
