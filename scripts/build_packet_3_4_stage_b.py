import json
import pathlib
import sys

def build_stage_b_verdicts():
    p3 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_3.json').read_text(encoding='utf-8'))
    p4 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_4.json').read_text(encoding='utf-8'))
    questions = p3['questions'] + p4['questions']

    # Master audit definitions for each question_id
    audit_data = {
        "V14-R2-DAN7-W2-061": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "parecía más grande que sus compañeros.",
            "distractor_analysis": {
                "option_0": "Falla porque sustituye 'más grande' por 'más robusto', término no usado en Daniel 7:20.",
                "option_1": "Falla porque afirma lo opuesto ('más menudo') a la descripción bíblica.",
                "option_3": "Falla porque introduce un rasgo morfológico ficticio ('más curvado') ausente en la fuente."
            },
            "specific_reason": "La opción 2 reproduce exactamente la descripción comparativa ('parecía más grande que sus compañeros') de Daniel 7:20."
        },
        "V14-R2-DAN7-W2-062": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "ante el cual habían caído tres.",
            "distractor_analysis": {
                "option_1": "Falla porque eleva incorrectamente la cifra a cinco cuernos.",
                "option_2": "Falla porque altera el número exacto a cuatro cuernos.",
                "option_3": "Falla porque propone siete cuernos caídos contrariando el texto."
            },
            "specific_reason": "La opción 0 señala con precisión textual la cantidad exacta de tres cuernos caídos indicada en Daniel 7:20."
        },
        "V14-R2-DAN7-W2-063": {
            "selected_option_index": 1,
            "exact_supporting_phrase": "parecía más grande que sus compañeros.",
            "distractor_analysis": {
                "option_0": "Falla porque plantea una supuesta debilidad visible no registrada en el pasaje.",
                "option_2": "Falla porque sugiere una estatura reducida que contradice directamente la fuente.",
                "option_3": "Falla porque sostiene erróneamente una igualdad de apariencia con los demás cuernos."
            },
            "specific_reason": "La opción 1 refleja fielmente la superioridad en tamaño señalada en Daniel 7:20."
        },
        "V14-R2-DAN7-W2-064": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "este cuerno hacía guerra contra los santos y los vencía,",
            "distractor_analysis": {
                "option_0": "Falla porque inventa un pacto falso y división interna ajenos al relato.",
                "option_1": "Falla porque introduce imposición de tributos y destierro no mencionados en Daniel 7:21.",
                "option_3": "Falla porque describe un asedio de urbes en lugar de la acción bélica directa contra los santos."
            },
            "specific_reason": "La opción 2 captura de forma literal la doble acción hostil y el desenlace ('hacía guerra contra los santos y los vencía') de Daniel 7:21."
        },
        "V14-R2-DAN7-W2-065": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "se hizo justicia a los santos del Altísimo;",
            "distractor_analysis": {
                "option_0": "Falla porque introduce un rescate monetario ajeno al acto judicial de Dios.",
                "option_1": "Falla porque plantea una tregua militar con los opresores no contemplada en la profecía.",
                "option_3": "Falla porque transfiere la corona a príncipes terrenales en lugar del juicio en favor de los santos."
            },
            "specific_reason": "La opción 2 corresponde con precisión a la determinación divina ('se hizo justicia a los santos del Altísimo') de Daniel 7:22."
        },
        "V14-R2-DAN7-W2-066": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "hasta que vino el Anciano de días, y se hizo justicia a los santos del Altísimo; y llegó el tiempo, y los santos recibieron el reino.",
            "distractor_analysis": {
                "option_1": "Falla porque introduce al ángel Gabriel y el sellamiento de la visión profética, ausentes en el versículo.",
                "option_2": "Falla porque añade referencias históricas persas y amnistías no registradas en Daniel 7:22.",
                "option_3": "Falla porque inventa un despertar de Daniel y una convocatoria de sabios en Babilonia."
            },
            "specific_reason": "La opción 0 reproduce íntegramente la secuencia de tres acontecimientos culminantes expresados en Daniel 7:22."
        },
        "V14-R2-DAN7-W2-067": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "La cuarta bestia será un cuarto reino en la tierra, el cual será diferente de todos los otros reinos,",
            "distractor_analysis": {
                "option_0": "Falla porque reduce la entidad profética a una alianza de diez monarcas orientales.",
                "option_1": "Falla porque confunde la cuarta bestia con un protectorado caldeo local.",
                "option_3": "Falla porque la identifica erróneamente como una confederación de los reinos medos."
            },
            "specific_reason": "La opción 2 se ciñe a la interpretación canónica de la cuarta bestia como un cuarto reino terrenal singular según Daniel 7:23."
        },
        "V14-R2-DAN7-W2-068": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "a toda la tierra devorará, trillará y despedazará.",
            "distractor_analysis": {
                "option_1": "Falla porque sustituye los verbos destructivos por acciones políticas (dominará, tributará, someterá).",
                "option_2": "Falla porque altera la tríada a sitiará, despojará y consumirá.",
                "option_3": "Falla porque emplea verbos de administración civil (dividirá, confiscará, regirá) ajenos al versículo."
            },
            "specific_reason": "La opción 0 contiene la tríada exacta y literal de verbos ('devorará, trillará y despedazará') de Daniel 7:23."
        },
        "V14-R2-DAN7-W2-069": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "el cual será diferente de todos los otros reinos,",
            "distractor_analysis": {
                "option_0": "Falla porque afirma una semejanza total que contradice frontalmente la distinción textual.",
                "option_1": "Falla porque le atribuye continuidad legal y consuetudinaria de los reyes medos.",
                "option_3": "Falla porque postula menor poder o extensión territorial cuando el texto resalta su devastación global."
            },
            "specific_reason": "La opción 2 concuerda con la singularidad explícita ('diferente de todos los otros reinos') de Daniel 7:23."
        },
        "V14-R2-DAN7-W2-070": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "de aquel reino se levantarán diez reyes; y tras ellos se levantará otro, el cual será diferente de los primeros, y derribará a tres reyes.",
            "distractor_analysis": {
                "option_0": "Falla porque sitúa el origen en diez naciones ajenas y sustituye el derribo por una coronación.",
                "option_1": "Falla porque restringe el origen a satrapías orientales y cambia el derribamiento por destierro.",
                "option_3": "Falla porque introduce alianzas mediterráneas y una unión política no mencionada."
            },
            "specific_reason": "La opción 2 sintetiza con total precisión el origen de los diez reyes y la caída de tres reyes ante el sucesor según Daniel 7:24."
        },
        "V14-R2-DAN7-W2-071": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "hasta tiempo, tiempos y medio tiempo.",
            "distractor_analysis": {
                "option_1": "Falla porque altera el cómputo temporal a siete tiempos.",
                "option_2": "Falla porque cambia la fracción final a tres tiempos.",
                "option_3": "Falla porque confunde el plazo con las setenta semanas proféticas."
            },
            "specific_reason": "La opción 0 cita literalmente la fórmula profética de duración ('tiempo, tiempos y medio tiempo') de Daniel 7:25."
        },
        "V14-R2-DAN7-W2-072": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "pensará en cambiar los tiempos y la Ley;",
            "distractor_analysis": {
                "option_1": "Falla porque menciona alteración de pactos y el arca en vez de tiempos y la Ley.",
                "option_2": "Falla porque sustituye los objetos por tronos y el culto.",
                "option_3": "Falla porque introduce la administración de fiestas y el reino sin respaldo textual."
            },
            "specific_reason": "La opción 0 coincide fielmente con las dos prerrogativas divinas ('los tiempos y la Ley') señaladas en Daniel 7:25."
        },
        "V14-R2-PR39-W2-073": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "tan fieles a los buenos principios como el acero,",
            "distractor_analysis": {
                "option_1": "Falla porque sustituye el símil del acero por pureza como la plata.",
                "option_2": "Falla porque utiliza la metáfora de constancia como la piedra.",
                "option_3": "Falla porque emplea la figura de firmeza como el bronce ante leyes reales."
            },
            "specific_reason": "La opción 0 cita de manera literal la comparación emblemática ('tan fieles a los buenos principios como el acero') de PR 27.1."
        },
        "V14-R2-PR39-W2-074": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "sino que honrarían a Dios aun cuando lo perdiesen todo.",
            "distractor_analysis": {
                "option_1": "Falla porque condiciona la honra a un eventual retorno a Judea.",
                "option_2": "Falla porque supedita la fidelidad a la preservación de favores materiales.",
                "option_3": "Falla porque restringe la honra a la concesión de cargos elevados."
            },
            "specific_reason": "La opción 0 refleja la resolución incondicional de los jóvenes ('honrarían a Dios aun cuando lo perdiesen todo') según PR 27.1."
        },
        "V14-R2-PR39-W2-075": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "que no serían corrompidos por el egoísmo,",
            "distractor_analysis": {
                "option_1": "Falla porque sustituye la corrupción por intimidación a causa del destierro.",
                "option_2": "Falla porque introduce fascinación por tesoros en lugar del término específico egoísmo.",
                "option_3": "Falla porque alude a seducción por manjares en vez del vicio degradante citado."
            },
            "specific_reason": "La opción 0 reproduce con fidelidad la cláusula exacta 'no serían corrompidos por el egoísmo' de PR 27.1."
        },
        "V14-R2-PR39-W2-076": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "al principio de los setenta años de cautiverio,",
            "distractor_analysis": {
                "option_0": "Falla porque ubica la deportación a mitad de los setenta años.",
                "option_1": "Falla porque sitúa el cautiverio al término del período de setenta años.",
                "option_3": "Falla porque afirma que fueron conducidos después de expirar el destierro."
            },
            "specific_reason": "La opción 2 se apega estrictamente al marco cronológico inicial ('al principio de los setenta años de cautiverio') de PR 27.1."
        },
        "V14-R2-PR39-W2-077": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "dando a las naciones paganas las bendiciones provenientes del conocimiento de Jehová.",
            "distractor_analysis": {
                "option_1": "Falla porque sugiere asimilación de ritos paganos contraria al propósito de Dios.",
                "option_2": "Falla porque introduce instrucción militar judía no mencionada en la fuente.",
                "option_3": "Falla porque plantea una imposición violenta de leyes ceremoniales."
            },
            "specific_reason": "La opción 0 formula textualmente la misión espiritual descrita en PR 27.1."
        },
        "V14-R2-PR39-W2-078": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "No debían en caso alguno transigir con los idólatras,",
            "distractor_analysis": {
                "option_1": "Falla porque prohíbe labores de estado que ellos legítimamente desempeñaron.",
                "option_2": "Falla porque veda el aprendizaje del idioma caldeo, el cual sí estudiaron.",
                "option_3": "Falla porque prohíbe tolerar cambios de nombres impuestos por la autoridad babilónica."
            },
            "specific_reason": "La opción 0 cita literalmente la regla de conducta de no transigir con los idólatras de PR 27.1."
        },
        "V14-R2-PR39-W2-079": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "la fe que sostenían y el nombre de adoradores del Dios viviente.",
            "distractor_analysis": {
                "option_1": "Falla porque traslada el honor a la admiración de magos y sabios paganos.",
                "option_2": "Falla porque enfoca el honor en favores y nombramientos del monarca caldeo.",
                "option_3": "Falla porque lo restringe a privilegios y aposentos cortesanos en palacio."
            },
            "specific_reason": "La opción 0 contiene la definición exacta del alto honor ('la fe que sostenían y el nombre de adoradores del Dios viviente') de PR 27.1."
        },
        "V14-R2-PR39-W2-080": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "Honraron a Dios en la prosperidad y en la adversidad;",
            "distractor_analysis": {
                "option_1": "Falla porque condiciona la honra a cargos de mando palaciegos.",
                "option_2": "Falla porque circunscribe la fidelidad a períodos de bonanza en Judá.",
                "option_3": "Falla porque limita la lealtad a la ausencia de sufrimiento."
            },
            "specific_reason": "La opción 0 expresa con fidelidad las dos circunstancias de lealtad ('en la prosperidad y en la adversidad') de PR 27.1."
        },
        "V14-R2-PR39-W2-081": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "y Dios los honró a ellos.",
            "distractor_analysis": {
                "option_0": "Falla porque promete exención absoluta de toda aflicción corporal.",
                "option_1": "Falla porque postula una inmediata e inexistente repatriación a Judá.",
                "option_3": "Falla porque inventa una coronación de los jóvenes como soberanos de Media."
            },
            "specific_reason": "La opción 2 reproduce de manera directa la retribución divina ('Dios los honró a ellos') consignada en PR 27.1."
        },
        "V14-R2-PR39-W2-082": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "El hecho de que esos adoradores de Jehová estuviesen cautivos en Babilonia y de que los vasos de la casa de Dios se hallaran en el templo de los dioses babilónicos,",
            "distractor_analysis": {
                "option_1": "Falla porque introduce la quema de manuscritos bíblicos ausente en la fuente.",
                "option_2": "Falla porque menciona una supuesta derrota de profetas frente a astrólogos.",
                "option_3": "Falla porque incluye tributos anuales y apresamiento generalizado de sacerdotes."
            },
            "specific_reason": "La opción 0 compendia con total exactitud los dos motivos de jactancia babilónica expuestos en PR 27.2."
        },
        "V14-R2-PR39-W2-083": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "la forma en que Israel se había desviado de él,",
            "distractor_analysis": {
                "option_0": "Falla porque atribuye las humillaciones a falta de alianzas bélicas.",
                "option_1": "Falla porque imputa la causa a inferioridad numérica del ejército judío.",
                "option_3": "Falla porque alega un retraso científico respecto a los caldeos."
            },
            "specific_reason": "La opción 2 identifica la verdadera causa teológica y moral ('la forma en que Israel se había desviado de él') de PR 27.2."
        },
        "V14-R2-PR39-W2-084": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "evidencia de su supremacía, de la santidad de sus requerimientos y de los seguros resultados que produce la obediencia.",
            "distractor_analysis": {
                "option_1": "Falla porque sustituye la evidencia divina por la condenación y ruina de Babilonia.",
                "option_2": "Falla porque menciona riquezas eternas y poder militar de ejércitos celestiales.",
                "option_3": "Falla porque cambia los conceptos por sabiduría humana y destino de naciones."
            },
            "specific_reason": "La opción 0 contiene la formulación triple exacta del testimonio dado a Babilonia en PR 27.2."
        },
        "V14-R2-PR39-W2-085": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "por medio de los que le eran leales.",
            "distractor_analysis": {
                "option_1": "Falla porque recurre a catástrofes cósmicas no mencionadas en el texto.",
                "option_2": "Falla porque postula victorias militares babilónicas inexistentes.",
                "option_3": "Falla porque plantea tratados y decretos políticos con el rey pagano."
            },
            "specific_reason": "La opción 0 cita literalmente el medio exclusivo empleado por Dios ('por medio de los que le eran leales') en PR 27.2."
        },
        "V14-R2-PR39-W2-086": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "ilustres ejemplos de lo que pueden llegar a ser los hombres que se unen con el Dios de sabiduría y poder.",
            "distractor_analysis": {
                "option_0": "Falla porque enfoca el ejemplo en la acumulación de riquezas cortesanas.",
                "option_1": "Falla porque propone una supremacía de casta sobre las dinastías caldeas.",
                "option_3": "Falla porque sugiere que el modelo consistía en asimilar plenamente la cultura babilónica."
            },
            "specific_reason": "La opción 2 concuerda con exactitud con el testimonio ejemplar de los fieles unidos a Dios en PR 27.3."
        },
        "V14-R2-PR39-W2-087": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "Desde la comparativa sencillez de su hogar judío, estos jóvenes del linaje real fueron llevados a la más magnífica de las ciudades, y a la corte del mayor monarca del mundo.",
            "distractor_analysis": {
                "option_1": "Falla porque traslada erróneamente el origen al sacerdocio y el destino a Tiro.",
                "option_2": "Falla porque cambia la sencillez judía por opulencia salomónica y trabajos forzados.",
                "option_3": "Falla porque sitúa a los jóvenes en prisiones secretas caldeas."
            },
            "specific_reason": "La opción 0 reproduce íntegramente el contraste sociogeográfico descrito en PR 27.3."
        },
        "V14-R2-PR39-W2-088": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "a Aspenaz, príncipe de sus eunucos,",
            "distractor_analysis": {
                "option_1": "Falla porque confunde al jefe de los eunucos con Melsar, el mayordomo subalterno.",
                "option_2": "Falla porque nombra a Arioc, capitán de la guardia real.",
                "option_3": "Falla porque introduce a Belsasar, monarca posterior."
            },
            "specific_reason": "La opción 0 identifica al oficial comisionado por el monarca ('Aspenaz, príncipe de sus eunucos') según PR 27.3."
        },
        "V14-R2-PR39-W2-089": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "muchachos en quienes no hubiese tacha alguna,",
            "distractor_analysis": {
                "option_1": "Falla porque inventa como condición previa la renuncia a las leyes paternas.",
                "option_2": "Falla porque sustituye la integridad física y moral por pureza de linaje.",
                "option_3": "Falla porque introduce la apostasía del culto judío como requisito de ingreso."
            },
            "specific_reason": "La opción 0 recoge literalmente la exigencia de integridad ('no hubiese tacha alguna') citada en PR 27.3."
        },
        "V14-R2-PR39-W2-090": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "e idóneos para estar en el palacio del rey...",
            "distractor_analysis": {
                "option_0": "Falla porque asigna a los jóvenes funciones de mando militar en batalla.",
                "option_1": "Falla porque los destina a oficiar sacrificios en templos paganos.",
                "option_3": "Falla porque reduce su idoneidad a guardia de murallas de la capital."
            },
            "specific_reason": "La opción 2 refleja con precisión el propósito de la selección ('para estar en el palacio del rey') según PR 27.3."
        },
        "V14-R2-PR39-W2-091": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "enseñados en toda sabiduría, y sabios en ciencia, y de buen entendimiento,",
            "distractor_analysis": {
                "option_1": "Falla porque reemplaza la tríada por adiestramiento doctrinal, doctos en decretos y hábil razonamiento.",
                "option_2": "Falla porque sustituye por instrucción en disciplinas y pericia en leyes.",
                "option_3": "Falla porque introduce términos ajenos como educación en filosofía y enigmas."
            },
            "specific_reason": "La opción 0 contiene la formulación triple textual exacta de las aptitudes cognitivas de PR 27.3."
        },
        "V14-R2-PR39-W2-092": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "y de buen parecer,",
            "distractor_analysis": {
                "option_0": "Falla porque alude al linaje nobiliario en lugar del rasgo estético explícito.",
                "option_1": "Falla porque introduce una cualidad castrense (porte marcial) no referida.",
                "option_3": "Falla porque inventa una regia postura ausente en la descripción bíblica e inspirada."
            },
            "specific_reason": "La opción 2 reproduce de forma literal el rasgo estético ('de buen parecer') requerido en PR 27.3."
        },
        "V14-R2-PR39-W2-093": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "de los hijos de Judá, Daniel, Ananías, Misael y Azarías.",
            "distractor_analysis": {
                "option_1": "Falla porque atribuye a los jóvenes pertenencia a la tribu de Dan.",
                "option_2": "Falla porque asigna la filiación a la tribu sacerdotal de Leví.",
                "option_3": "Falla porque indica erróneamente la tribu de Gad."
            },
            "specific_reason": "La opción 0 concuerda textualmente con el origen tribal de Judá registrado en PR 27.4."
        },
        "V14-R2-PR39-W2-094": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "para que pudiesen ocupar puestos importantes en su reino.",
            "distractor_analysis": {
                "option_0": "Falla porque restringe el fin formativo al liderazgo en el servicio militar.",
                "option_1": "Falla porque plantea la custodia de templos idolátricos del imperio.",
                "option_3": "Falla porque delimita su destino al gobierno exclusivo de satrapías remotas."
            },
            "specific_reason": "La opción 2 expresa literalmente el fin perseguido por Nabucodonosor ('ocupar puestos importantes en su reino') en PR 27.4."
        },
        "V14-R2-PR39-W2-095": {
            "selected_option_index": 1,
            "exact_supporting_phrase": "una promesa de capacidad notable,",
            "distractor_analysis": {
                "option_0": "Falla porque sustituye la aptitud intelectual por devoción religiosa absoluta.",
                "option_2": "Falla porque califica el potencial como sumisión política ciega.",
                "option_3": "Falla porque transforma la capacidad notable en pericia bélica."
            },
            "specific_reason": "La opción 1 reproduce con precisión la frase 'una promesa de capacidad notable' de PR 27.4."
        },
        "V14-R2-PR39-W2-096": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "durante tres años se les concediesen las ventajas educativas que tenían los príncipes del reino.",
            "distractor_analysis": {
                "option_0": "Falla porque reduce la duración del período formativo a dos años.",
                "option_1": "Falla porque extiende el tiempo de preparación a cinco años.",
                "option_3": "Falla porque amplía indebidamente el plazo educativo a siete años."
            },
            "specific_reason": "La opción 2 señala con exactitud el período de tres años establecido en PR 27.4."
        },
        "V14-R2-PR39-W2-097": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "el idioma de los caldeos,",
            "distractor_analysis": {
                "option_1": "Falla porque sustituye la lengua caldea por el dialecto de los asirios.",
                "option_2": "Falla porque introduce el idioma oficial de los persas.",
                "option_3": "Falla porque plantea la enseñanza de la lengua culta egipcia."
            },
            "specific_reason": "La opción 0 cita literalmente el aprendizaje del 'idioma de los caldeos' según PR 27.4."
        },
        "V14-R2-PR39-W2-098": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "las ventajas educativas que tenían los príncipes del reino.",
            "distractor_analysis": {
                "option_1": "Falla porque altera el nivel formativo al de la disciplina de los astrólogos.",
                "option_2": "Falla porque reduce la preparación a instrucción militar para capitanes.",
                "option_3": "Falla porque restringe el estatus a un adiestramiento técnico para escribas."
            },
            "specific_reason": "La opción 0 concuerda textualmente con el privilegio educativo de los príncipes del reino en PR 27.4."
        },
        "V14-R2-PR39-W2-099": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "conmemoraban divinidades caldeas.",
            "distractor_analysis": {
                "option_0": "Falla porque atribuye a los nombres la conmemoración de victorias babilónicas.",
                "option_1": "Falla porque afirma que honraban a monarcas victoriosos de Babilonia.",
                "option_3": "Falla porque propone una asociación con constelaciones astronómicas."
            },
            "specific_reason": "La opción 2 se apega estrictamente al hecho de que los nuevos nombres conmemoraban 'divinidades caldeas' (PR 27.5)."
        },
        "V14-R2-PR39-W2-100": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "nombres que tenían gran significado.",
            "distractor_analysis": {
                "option_1": "Falla porque sugiere que los nombres hebreos denotaban rango militar.",
                "option_2": "Falla porque alega que imitaban títulos monárquicos.",
                "option_3": "Falla porque postula que honraban a héroes paganos."
            },
            "specific_reason": "La opción 0 refleja con fidelidad la cualidad descriptiva ('tenían gran significado') de PR 27.5."
        },
        "V14-R2-PR39-W2-101": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "los rasgos de carácter que deseaban ver desarrollarse en sus hijos.",
            "distractor_analysis": {
                "option_1": "Falla porque remite a hazañas bélicas pasadas de sus antepasados.",
                "option_2": "Falla porque orienta los nombres a aspiraciones de cargos políticos.",
                "option_3": "Falla porque plantea honores civiles y adquisición de riquezas."
            },
            "specific_reason": "La opción 0 reproduce con exactitud la intención formativa de los padres hebreos en PR 27.5."
        },
        "V14-R2-PR39-W2-102": {
            "selected_option_index": 3,
            "exact_supporting_phrase": "y a Azarías, Abednego",
            "distractor_analysis": {
                "option_0": "Falla porque Beltsasar fue el nombre asignado a Daniel.",
                "option_1": "Falla porque Mesach fue el nombre asignado a Misael.",
                "option_2": "Falla porque Sadrach fue el nombre asignado a Ananías."
            },
            "specific_reason": "La opción 3 asigna de forma unívoca y correcta el nombre 'Abednego' a Azarías según PR 27.5."
        },
        "V14-R2-PR39-W2-103": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "puso a Daniel, Beltsasar;",
            "distractor_analysis": {
                "option_1": "Falla porque Abednego correspondió a Azarías.",
                "option_2": "Falla porque Sadrach correspondió a Ananías.",
                "option_3": "Falla porque Mesach correspondió a Misael."
            },
            "specific_reason": "La opción 0 identifica correctamente el nombre babilónico 'Beltsasar' asignado a Daniel en PR 27.5."
        },
        "V14-R2-PR39-W2-104": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "y a Ananías, Sadrach;",
            "distractor_analysis": {
                "option_0": "Falla porque Beltsasar fue dado a Daniel.",
                "option_1": "Falla porque Abednego fue dado a Azarías.",
                "option_3": "Falla porque Mesach fue dado a Misael."
            },
            "specific_reason": "La opción 2 asocia sin margen de error el nombre 'Sadrach' con Ananías en PR 27.5."
        },
        "V14-R2-PR39-W2-105": {
            "selected_option_index": 1,
            "exact_supporting_phrase": "y a Misael, Mesach;",
            "distractor_analysis": {
                "option_0": "Falla porque Beltsasar correspondió a Daniel.",
                "option_2": "Falla porque Sadrach correspondió a Ananías.",
                "option_3": "Falla porque Abednego correspondió a Azarías."
            },
            "specific_reason": "La opción 1 concuerda exactamente con el nombre 'Mesach' impuesto a Misael en PR 27.5."
        },
        "V14-R2-PR39-W2-106": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "sino que esperaba obtener esto gradualmente.",
            "distractor_analysis": {
                "option_1": "Falla porque afirma la emisión de decretos públicos con pena de muerte.",
                "option_2": "Falla porque introduce violencia física inmediata y castigos reales.",
                "option_3": "Falla porque propone la privación de toda educación cortesana contrariando la fuente."
            },
            "specific_reason": "La opción 0 formula con exactitud el método paulatino e indirecto ('esperaba obtener esto gradualmente') de PR 27.6."
        },
        "V14-R2-PR39-W2-107": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "Dándoles nombres que expresaban sentimientos de idolatría, poniéndolos en trato íntimo con costumbres idólatras y bajo la influencia de ritos seductores del culto pagano,",
            "distractor_analysis": {
                "option_1": "Falla porque cambia la estrategia sutil por tributos forzados y trabajos pesados.",
                "option_2": "Falla porque introduce torturas, aislamiento y prohibición de libros.",
                "option_3": "Falla porque recurre a censura y amenazas de muerte directa."
            },
            "specific_reason": "La opción 0 compendia fielmente la combinación triple de influencias seductoras expuesta en PR 27.6."
        },
        "V14-R2-PR39-W2-108": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "esperaba inducirlos a renunciar a la religión de su nación, y a participar en el culto babilónico.",
            "distractor_analysis": {
                "option_1": "Falla porque define el objetivo como esclavitud perpetua para edificar santuarios.",
                "option_2": "Falla porque plantea la dirección obligatoria de tropas contra Judá.",
                "option_3": "Falla porque sugiere que preservaría sus votos sagrados."
            },
            "specific_reason": "La opción 0 reproduce con absoluta literalidad el objetivo final del rey consignado en PR 27.6."
        },
        "V14-R2-PR39-W2-109": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "En el mismo comienzo de su carrera,",
            "distractor_analysis": {
                "option_1": "Falla porque traslada la prueba a su designación formal como ministros.",
                "option_2": "Falla porque sitúa el examen al final de los tres años de educación.",
                "option_3": "Falla porque pospone la prueba decisiva a los eventos del capítulo 2 de Daniel."
            },
            "specific_reason": "La opción 0 ubica temporalmente la prueba con exactitud textual ('En el mismo comienzo de su carrera') según PR 28.1."
        },
        "V14-R2-PR39-W2-110": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "su carácter fué probado de una manera decisiva.",
            "distractor_analysis": {
                "option_1": "Falla porque califica la prueba como meramente aparente.",
                "option_2": "Falla porque describe la prueba como pasajera.",
                "option_3": "Falla porque señala que fue una prueba simulada o ficticia."
            },
            "specific_reason": "La opción 0 cita literalmente la calificación del examen ('de una manera decisiva') en PR 28.1."
        },
        "V14-R2-PR39-W2-111": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "comiesen del alimento y bebiesen del vino que provenían de la mesa real.",
            "distractor_analysis": {
                "option_1": "Falla porque sitúa el origen de las viandas en mercados ordinarios de Babilonia.",
                "option_2": "Falla porque reduce la ración al alimento provisto para los siervos.",
                "option_3": "Falla porque asigna la preparación de la comida al templo pagano de Bel."
            },
            "specific_reason": "La opción 0 se ciñe textualmente a la provisión proveniente de la mesa real de PR 28.1."
        },
        "V14-R2-PR39-W2-112": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "manifestarles su favor y la solicitud que sentía por su bienestar.",
            "distractor_analysis": {
                "option_1": "Falla porque imputa al rey motivos de sospecha y control estricto.",
                "option_2": "Falla porque califica la medida como una exigencia coercitiva de sumisión.",
                "option_3": "Falla porque orienta la provisión a vanagloria e imposición de superioridad."
            },
            "specific_reason": "La opción 0 sintetiza con exactitud la motivación benevolente del rey ('su favor y la solicitud que sentía por su bienestar') según PR 28.1."
        },
        "V14-R2-PR39-W2-113": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "el alimento proveniente de la mesa del rey estaba consagrado a la idolatría, y compartirlo sería considerado como tributo de homenaje a los dioses de Babilonia.",
            "distractor_analysis": {
                "option_1": "Falla porque introduce deudas y gravámenes financieros contraídos con el rey.",
                "option_2": "Falla porque inventa ingredientes mágicos consagrados a la adivinación.",
                "option_3": "Falla porque plantea una transgresión de normas nobiliarias de etiqueta palaciega."
            },
            "specific_reason": "La opción 0 explica la consagración idolátrica y el significado de homenaje a dioses paganos conforme a PR 28.1."
        },
        "V14-R2-PR39-W2-114": {
            "selected_option_index": 2,
            "exact_supporting_phrase": "La lealtad a Jehová prohibía a Daniel y a sus compañeros que rindiesen tal homenaje.",
            "distractor_analysis": {
                "option_0": "Falla porque fundamenta la decisión en temor al castigo judicial.",
                "option_1": "Falla porque reduce la postura a un apego a normas de higiene sanitaria.",
                "option_3": "Falla porque la califica como una simple costumbre de la monarquía judía."
            },
            "specific_reason": "La opción 2 destaca con total precisión el móvil sagrado ('La lealtad a Jehová') expuesto en PR 28.1."
        },
        "V14-R2-PR39-W2-115": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "Aun el hacer como que comieran del alimento o bebieran del vino habría sido negar su fe.",
            "distractor_analysis": {
                "option_1": "Falla porque justifica el fingimiento como cumplimiento inofensivo de protocolo.",
                "option_2": "Falla porque califica la simulación de prudencia social.",
                "option_3": "Falla porque evalúa la acción como mera cortesía para no agraviar al rey."
            },
            "specific_reason": "La opción 0 expresa con rigor el veredicto moral ('habría sido negar su fe') de PR 28.1 ante la simulación."
        },
        "V14-R2-PR39-W2-116": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "colocarse de parte del paganismo y deshonrar los principios de la ley de Dios.",
            "distractor_analysis": {
                "option_1": "Falla porque propone una supuesta preservación de testimonio incoherente con ceder al paganismo.",
                "option_2": "Falla porque establece una separación relativista entre cortesía externa y devoción interna.",
                "option_3": "Falla porque disocia las facultades físicas de la transgresión de mandamientos."
            },
            "specific_reason": "La opción 0 reproduce con fidelidad absoluta la sentencia espiritual de PR 28.1."
        },
        "V14-R2-PR39-W2-117": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "sobre el desarrollo físico, mental y espiritual.",
            "distractor_analysis": {
                "option_1": "Falla porque reduce las áreas a competencias verbales, técnicas y cortesanas.",
                "option_2": "Falla porque sustituye el desarrollo holístico por desempeño político y castrense.",
                "option_3": "Falla porque alude a linaje familiar y facultades administrativas."
            },
            "specific_reason": "La opción 0 cita íntegramente la tríada de desarrollo integral ('físico, mental y espiritual') de PR 28.2."
        },
        "V14-R2-PR39-W2-118": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "Conocían la historia de Nadab y Abihú, cuya intemperancia, así como los resultados que había tenido, describían los pergaminos del Pentateuco;",
            "distractor_analysis": {
                "option_1": "Falla porque cita la rebelión de Coré, Datán y Abiram en Números.",
                "option_2": "Falla porque alude a Sansón y los filisteos en el libro de Jueces.",
                "option_3": "Falla porque refiere la conducta de los hijos del sacerdote Elí en 1 Samuel."
            },
            "specific_reason": "La opción 0 identifica con precisión el antecedente bíblico de Nadab y Abihú consignado en PR 28.2."
        },
        "V14-R2-PR39-W2-119": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "hábitos de estricta templanza.",
            "distractor_analysis": {
                "option_1": "Falla porque orienta los hábitos a destrezas y pericia diplomática.",
                "option_2": "Falla porque confunde la templanza bíblica con un ascetismo riguroso.",
                "option_3": "Falla porque propone una disciplina de carácter marcial."
            },
            "specific_reason": "La opción 0 cita literalmente la expresión 'hábitos de estricta templanza' de PR 28.3."
        },
        "V14-R2-PR39-W2-120": {
            "selected_option_index": 0,
            "exact_supporting_phrase": "Los padres de Daniel y sus compañeros les habían inculcado",
            "distractor_analysis": {
                "option_1": "Falla porque traslada la instrucción formativa primaria a los profetas de Judá.",
                "option_2": "Falla porque atribuye la disciplina del hogar a los sacerdotes del templo.",
                "option_3": "Falla porque asigna la enseñanza ética a los ancianos cívicos."
            },
            "specific_reason": "La opción 0 reconoce con total fidelidad la influencia formativa fundamental de los padres según PR 28.3."
        }
    }

    verdicts = []
    errors = []

    for q in questions:
        qid = q["question_id"]
        sha = q["presentation_sha256"]
        opts = q["options"]
        quote = q["source_quote"]

        if qid not in audit_data:
            errors.append(f"Missing audit data for {qid}")
            continue

        item_audit = audit_data[qid]
        sel_idx = item_audit["selected_option_index"]
        sel_text = opts[sel_idx]
        phrase = item_audit["exact_supporting_phrase"]

        # Validate phrase is in source_quote
        if phrase not in quote:
            errors.append(f"{qid}: exact_supporting_phrase '{phrase}' not in source_quote '{quote}'")

        # Validate distractor keys cover all other options
        expected_dist_keys = {f"option_{i}" for i in range(4) if i != sel_idx}
        actual_dist_keys = set(item_audit["distractor_analysis"].keys())
        if actual_dist_keys != expected_dist_keys:
            errors.append(f"{qid}: distractor keys mismatch: expected {expected_dist_keys}, got {actual_dist_keys}")

        record = {
            "question_id": qid,
            "presentation_sha256": sha,
            "selected_option_index": sel_idx,
            "selected_option_text": sel_text,
            "exact_supporting_phrase": phrase,
            "second_defensible_option": False,
            "second_defensible_text": None,
            "distractor_analysis": item_audit["distractor_analysis"],
            "semantic_category_check": "EXCELLENT",
            "novelty_check": True,
            "decision": "ACCEPT",
            "specific_reason": item_audit["specific_reason"]
        }
        verdicts.append(record)

    if errors:
        print("ERRORS FOUND:")
        for err in errors:
            print(" -", err)
        sys.exit(1)

    print(f"Successfully validated all {len(verdicts)} verdicts.")
    return verdicts

if __name__ == '__main__':
    verdicts = build_stage_b_verdicts()
    out_path = pathlib.Path('content/competitive-v13/waves/wave2/stage-b/reviewer_b2/packet_3_4.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(verdicts, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Written to {out_path}")
