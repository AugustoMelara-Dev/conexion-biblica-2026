import json
import pathlib

ROOT = pathlib.Path("c:/Users/melar/OneDrive/Desktop/Conexion biblica/.worktrees/emergencia-competitiva-unica-v13")
dossier_file = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "dossiers" / "pilot_batch_2.json"
dossiers_data = json.loads(dossier_file.read_text(encoding="utf-8"))["dossiers"]

# Let's define the 30 questions
raw_questions = [
    # Item 31
    {
        "pilot_index": 31,
        "id": "V16-R3-PILOT-031",
        "question": "Según Elena G. de White en Profetas y Reyes (p. 27), ante las presiones idolátricas en la corte de Babilonia, el deber primordial de los jóvenes cautivos consistía en que ____.",
        "correct_text": "no debían en caso alguno transigir con los idólatras, sino considerar como alto honor su fe y el nombre de adoradores del Dios viviente",
        "distractors": [
            ("no debían rechazar los manjares reales de inmediato, sino esperar una oportunidad propicia para dar testimonio público de su fe", "Elena White no aconseja contemporizar ni posponer la fidelidad, sino rechazar en caso alguno cualquier transigencia."),
            ("debían someterse externamente a los ritos de la corte caldea mientras conservaran en secreto la adoración al Dios de sus padres", "La sumisión externa y el culto secreto contradicen la orden de considerar como alto honor confesar abiertamente el nombre de adoradores del Dios viviente."),
            ("debían aislarse de toda función oficial en el palacio real para evitar el contacto continuo con los sabios y sacerdotes caldeos", "No se les mandó aislarse de la corte o el servicio de estado, sino servir allí sin claudicar en sus principios morales.")
        ],
        "correct_pos": 0,
        "explanation": "Profetas y Reyes (p. 27) enfatiza que no debían en caso alguno transigir con los idólatras, sino considerar un alto honor la fe que sostenían y el nombre de adoradores del Dios viviente."
    },
    # Item 32
    {
        "pilot_index": 32,
        "id": "V16-R3-PILOT-032",
        "question": "Al describir la fidelidad incondicional de los jóvenes hebreos en el cautiverio, Profetas y Reyes (p. 27) sintetiza la reciprocidad de su relación con el Altísimo afirmando que ____.",
        "correct_text": "honraron a Dios en la prosperidad y en la adversidad; y Dios los honró a ellos",
        "distractors": [
            ("sirvieron a Dios únicamente durante la adversidad; y Dios los libró en su corte", "No sirvieron a Dios únicamente en tiempos difíciles, sino que lo honraron tanto en la prosperidad como en la adversidad."),
            ("glorificaron a Dios al recuperar su libertad; y Dios restauró su linaje real", "Su testimonio fiel ocurrió en pleno cautiverio babilónico y no tras una supuesta liberación o restauración terrenal."),
            ("obedecieron a Dios solo al enfrentar el peligro; y Dios les concedió sabiduría", "Su honra a Dios fue un principio permanente y no una reacción oportunista motivada únicamente ante el peligro inminente.")
        ],
        "correct_pos": 1,
        "explanation": "El texto de PR39 declara explícitamente: «Honraron a Dios en la prosperidad y en la adversidad; y Dios los honró a ellos»."
    },
    # Item 33
    {
        "pilot_index": 33,
        "id": "V16-R3-PILOT-033",
        "question": "De acuerdo con Profetas y Reyes (p. 27), los vencedores caldeos esgrimían como prueba jactanciosa de que su religión y costumbres superaban a las de los hebreos el hecho de que ____.",
        "correct_text": "los adoradores de Jehová estuviesen cautivos en Babilonia y los vasos de la casa de Dios se hallaran en el templo de sus dioses",
        "distractors": [
            ("el templo de Salomón hubiera sido incendiado por completo y los príncipes de Judá estuviesen bajo la tutela de los magos caldeos", "La jactancia babilónica descrita por Elena White no se basaba en el incendio del edificio, sino en tener a los adoradores cautivos y los vasos sagrados en su templo pagano."),
            ("los sacerdotes caldeos hubieran superado en astronomía a Judá y sometido a los jóvenes a servir en el templo de sus divinidades", "El relato no menciona una disputa astronómica o científica como base de su jactancia religiosa."),
            ("el monarca babilónico rigiera los tesoros de las naciones y retuviera a los sabios hebreos bajo el dominio de su propia religión", "La evidencia exhibida consistía en la posesión de los vasos sagrados en el templo de los dioses caldeos y el cautiverio de los adoradores de Jehová.")
        ],
        "correct_pos": 2,
        "explanation": "PR39 (p. 27) señala que los caldeos mencionaban jactanciosamente la presencia de los adoradores de Jehová cautivos y los vasos de Dios en el templo de sus dioses como prueba de su superioridad."
    },
    # Item 34
    {
        "pilot_index": 34,
        "id": "V16-R3-PILOT-034",
        "question": "En la perspectiva teológica de Elena G. de White (PR, p. 27), Dios transformó las mismas humillaciones acarreadas por la apostasía de Israel para dar a Babilonia evidencia explícita de ____.",
        "correct_text": "su supremacía, la santidad de sus requerimientos y los seguros resultados que produce la obediencia",
        "distractors": [
            ("su poder destructor, el fin irrevocable del reino caldeo y el juicio inmediato sobre sus sacerdotes", "El propósito del testimonio en ese momento no era anunciar la destrucción inmediata de Babilonia, sino manifestar la santidad y supremacía de Dios."),
            ("la superioridad moral de Judá, la excelencia de su linaje regio y la pureza ritual de sus levitas", "La humillación no vindicaba el orgullo nacional judío, sino la soberanía de Dios frente al propio desvío de Israel."),
            ("la futilidad de la ciencia babilónica, la necesidad de tributos y la imposibilidad de arrepentimiento", "Dios no buscaba condenar la ciencia sin dar testimonio, sino demostrar los resultados bienhechores de obedecer sus mandamientos.")
        ],
        "correct_pos": 3,
        "explanation": "PR39 (p. 27) indica que Dios dio a Babilonia evidencia de «su supremacía, de la santidad de sus requerimientos y de los seguros resultados que produce la obediencia»."
    },
    # Item 35
    {
        "pilot_index": 35,
        "id": "V16-R3-PILOT-035",
        "question": "Al explicar cómo Dios vindicó su soberanía y la santidad de su ley en medio de la idolatría pagana, Profetas y Reyes (p. 27) destaca que el Señor dio este testimonio ____.",
        "correct_text": "de la única manera que podía ser dado, por medio de los que le eran leales",
        "distractors": [
            ("mediante señales portentosas en el cielo que aterraron a los magos caldeos", "Dios no dio este testimonio mediante prodigios astronómicos o terrores celestes, sino a través de la vida de sus siervos."),
            ("por la mediación directa de profetas ancianos que censuraron al rey pagano", "El testimonio fue dado por jóvenes cautivos leales en su vida diaria en la corte, no por profetas ancianos censores."),
            ("a través de decretos imperiales promulgados antes del inicio del cautiverio", "Los decretos imperiales vinieron después como fruto del testimonio de los leales, no antes del cautiverio.")
        ],
        "correct_pos": 0,
        "explanation": "PR39 (p. 27) resalta: «Y dió este testimonio de la única manera que podía ser dado, por medio de los que le eran leales»."
    },
    # Item 36
    {
        "pilot_index": 36,
        "id": "V16-R3-PILOT-036",
        "question": "En la evaluación histórica de Profetas y Reyes (p. 27), la vida y conducta de Daniel y sus tres compañeros en Babilonia constituían ilustres ejemplos de ____.",
        "correct_text": "lo que pueden llegar a ser los hombres que se unen con el Dios de sabiduría y poder",
        "distractors": [
            ("la capacidad innata de la juventud hebrea para sobresalir en la diplomacia pagana", "La autora no atribuye sus logros a una capacidad innata secular, sino a la comunión viva con Dios."),
            ("cómo la formación en ciencias caldeas supera a la instrucción patriarcal de Judá", "La sabiduría babilónica no era superior a la revelación divina ni la causa de su excelencia moral."),
            ("la imposibilidad absoluta de mantenerse sin mancha al servir en un palacio regio", "Daniel y sus compañeros demostraron lo contrario: que con Dios es posible mantenerse puro aun en una corte idólatra.")
        ],
        "correct_pos": 1,
        "explanation": "PR39 (p. 27) define a los jóvenes como «ilustres ejemplos de lo que pueden llegar a ser los hombres que se unen con el Dios de sabiduría y poder»."
    },
    # Item 37
    {
        "pilot_index": 37,
        "id": "V16-R3-PILOT-037",
        "question": "Al contrastar el entorno originario de los cautivos con su destino en Babilonia, Profetas y Reyes (p. 27) señala con exactitud textual que estos jóvenes del linaje real fueron trasladados ____.",
        "correct_text": "desde la comparativa sencillez de su hogar judío a la más magnífica de las ciudades y a la corte del mayor monarca del mundo",
        "distractors": [
            ("desde la opulencia refinada del palacio en Judá a las severas escuelas caldeas establecidas en los confines de Babilonia", "Elena White no describe su origen como opulento palaciego sino como la «comparativa sencillez de su hogar judío» frente a la magnífica metrópoli."),
            ("desde el recinto sagrado del templo de Jerusalén al aislamiento forzado en las fortalezas militares del imperio babilónico", "No residían en el templo ni fueron destinados a fortalezas militares, sino a la corte del mayor monarca del mundo."),
            ("desde la severa instrucción del campamento hebreo a los suntuosos banquetes ofrecidos por los gobernantes caldeos en Sinar", "No eran soldados de campamento militar, sino príncipes educados en su hogar llevados al palacio real.")
        ],
        "correct_pos": 2,
        "explanation": "PR39 (p. 27) describe literalmente: «Desde la comparativa sencillez de su hogar judío, estos jóvenes del linaje real fueron llevados a la más magnífica de las ciudades, y a la corte del mayor monarca del mundo»."
    },
    # Item 38
    {
        "pilot_index": 38,
        "id": "V16-R3-PILOT-038",
        "question": "Conforme a la orden de selección impartida por Nabucodonosor a Aspenaz citada en Profetas y Reyes (p. 27), los cautivos elegidos debían reunir como requisitos que fuesen ____.",
        "correct_text": "del linaje real de los príncipes, sin tacha alguna, de buen parecer, enseñados en sabiduría, sabios en ciencia e idóneos para el palacio",
        "distractors": [
            ("de la tribu sacerdotal de Leví, adiestrados en artes de guerra, expertos en lenguas extranjeras y consagrados por voto de nazareato", "La orden no buscaba levitas guerreros con votos de nazareato, sino príncipes idóneos con facultades intelectuales y físicas."),
            ("hijos de los ancianos consejeros de Judá, peritos en edificación de ciudades, versados en leyes caldeas y sumisos a los decretos del rey", "No se seleccionaban constructores o juristas entre los ancianos, sino muchachos nobles, sabios y sin tacha."),
            ("jóvenes de la servidumbre de Joacim, hábiles en música del templo, instruidos en astronomía babilónica y exentos de castigo público", "No procedían de la servidumbre ni de los músicos, sino del linaje real de los príncipes de Israel.")
        ],
        "correct_pos": 3,
        "explanation": "PR39 (p. 27) cita los requisitos de Daniel 1:3-4: del linaje real, sin tacha alguna, de buen parecer, enseñados en toda sabiduría, sabios en ciencia, de buen entendimiento e idóneos para estar en el palacio."
    },
    # Item 39
    {
        "pilot_index": 39,
        "id": "V16-R3-PILOT-039",
        "question": "Al identificar a los cuatro hebreos seleccionados dentro del grupo de príncipes cautivos, Profetas y Reyes (p. 27) precisa expresamente que pertenecían a ____.",
        "correct_text": "los hijos de Judá, siendo sus nombres hebreos Daniel, Ananías, Misael y Azarías",
        "distractors": [
            ("los hijos de Efraín, figurando entre ellos Daniel, Jonatán, Misael y Malaquías", "No pertenecían a la tribu de Efraín ni se nombra a Jonatán o Malaquías."),
            ("los hijos de Benjamín, cuyos nombres eran Beltsasar, Sadrac, Mesac y Abednego", "Eran de los hijos de Judá (no Benjamín) y el texto cita en este versículo sus nombres hebreos originales."),
            ("los hijos de Leví, seleccionados como Daniel, Elieser, Azarías y Abdías en Judá", "No eran levitas ni se mencionan nombres como Elieser o Abdías en el grupo.")
        ],
        "correct_pos": 0,
        "explanation": "PR39 (p. 27) cita: «Y fueron entre ellos, de los hijos de Judá, Daniel, Ananías, Misael y Azarías»."
    },
    # Item 40
    {
        "pilot_index": 40,
        "id": "V16-R3-PILOT-040",
        "question": "Al evaluar el potencial de los cuatro jóvenes cautivos de Judá, el rey Nabucodonosor tomó la determinación de educarlos formalmente debido a que ____.",
        "correct_text": "vio en ellos una promesa de capacidad notable para que ocupasen puestos importantes en su reino",
        "distractors": [
            ("deseaba emplearlos exclusivamente como intérpretes militares en las campañas de conquista en Tiro", "El rey no buscaba intérpretes para el frente de batalla, sino capacitarlos para ocupar altos puestos en su administración civil."),
            ("temía una conspiración entre los cautivos hebreos y buscaba asimilarlos a los sabios de Babilonia", "La decisión no fue motivada por temor a conspiraciones, sino por la notable promesa de capacidad que vio en ellos."),
            ("pretendía exhibir su sumisión pública como trofeo religioso ante los dignatarios reunidos en Dura", "La educación no era una demostración idolátrica temporal para el llano de Dura, sino un plan formativo de servicio de estado.")
        ],
        "correct_pos": 1,
        "explanation": "PR39 (p. 27) expone: «Viendo en estos jóvenes una promesa de capacidad notable, Nabucodonosor resolvió que se los educase para que pudiesen ocupar puestos importantes en su reino»."
    },
    # Item 41
    {
        "pilot_index": 41,
        "id": "V16-R3-PILOT-041",
        "question": "Para asegurar que los jóvenes quedasen plenamente capacitados para su futura carrera cortesana, las disposiciones reales de Nabucodonosor estipulaban que ____.",
        "correct_text": "aprendiesen el idioma de los caldeos y recibiesen durante tres años las ventajas educativas de los príncipes",
        "distractors": [
            ("estudiasen la astrología caldea y permaneciesen durante siete años bajo la tutela de los magos de Babilonia", "El período decretado fue de tres años (no siete) y centrado en el idioma y educación de los príncipes."),
            ("memorizasen los anales de Sinar y practicasen durante dos años el protocolo sagrado en el templo de Marduk", "No se les asignó un adiestramiento sacerdotal idolátrico de dos años en templos paganos."),
            ("asumiesen las leyes de Media y fuesen instruidos durante cuatro años en el gobierno de todas las satrapías", "El programa correspondía al reino caldeo (no medo) y tenía una duración fijada de tres años.")
        ],
        "correct_pos": 2,
        "explanation": "PR39 (p. 27) señala: «ordenó que aprendiesen el idioma de los caldeos, y que durante tres años se les concediesen las ventajas educativas que tenían los príncipes del reino»."
    },
    # Item 42
    {
        "pilot_index": 42,
        "id": "V16-R3-PILOT-042",
        "question": "En el proceso de asimilación cultural y religiosa impuesto en Babilonia, la modificación de los nombres originales de Daniel y sus compañeros obedeció a que ____.",
        "correct_text": "los nuevos nombres asignados conmemoraban divinidades caldeas para influir en su lealtad espiritual",
        "distractors": [
            ("la legislación imperial prohibía formalmente el uso de nombres foráneos en los registros de palacio", "No era un impedimento burocrático o legal, sino una estrategia religiosa conmemorativa de deidades caldeas."),
            ("los apelativos hebreos resultaban impronunciables para los cortesanos y los eunucos de Nabucodonosor", "La imposición de nombres no obedecía a dificultades lingüísticas, sino a ensalzar los dioses de Babilonia."),
            ("el monarca pretendía honrar las campañas de sus generales confiriendo títulos de la nobleza caldea", "Los nombres sustitutos no honraban a generales ni hazañas bélicas, sino a ídolos babilónicos.")
        ],
        "correct_pos": 3,
        "explanation": "PR39 (p. 27) afirma taxativamente: «Los nombres de Daniel y sus compañeros fueron cambiados por otros que conmemoraban divinidades caldeas»."
    },
    # Item 43
    {
        "pilot_index": 43,
        "id": "V16-R3-PILOT-043",
        "question": "Al analizar la profunda relevancia teológica y familiar de la identidad hebrea, Profetas y Reyes (p. 27) destaca que la costumbre de los padres en Judá consistía en que ____.",
        "correct_text": "solían dar a sus hijos nombres que tenían gran significado para vincular su existencia al Dios vivo",
        "distractors": [
            ("imponían nombres derivados únicamente de títulos sacerdotales para asegurar el favor divino en Judá", "Los nombres no se limitaban a fórmulas sacerdotales fijas, sino que contenían un significado vital de fe y carácter."),
            ("escogían apelativos basados en las constelaciones celestes para predecir el destino secular del niño", "La astrología y adivinación celeste eran prácticas idolátricas prohibidas en la fe hebrea."),
            ("adoptaban apelativos conmemorativos de victorias militares obtenidas en los tiempos de la monarquía", "La tradición hebrea no se fundaba en ensalzar batallas seculares, sino en conferir nombres de profundo valor espiritual.")
        ],
        "correct_pos": 0,
        "explanation": "PR39 (p. 27) declara: «Los padres hebreos solían dar a sus hijos nombres que tenían gran significado»."
    },
    # Item 44
    {
        "pilot_index": 44,
        "id": "V16-R3-PILOT-044",
        "question": "De acuerdo con la explicación pedagógica y espiritual de Profetas y Reyes (p. 27), el propósito formativo de los padres hebreos al asignar el nombre a sus descendientes era que ____.",
        "correct_text": "con frecuencia expresaban en ellos los rasgos de carácter que deseaban ver desarrollarse en sus hijos",
        "distractors": [
            ("buscaban asegurarles títulos de propiedad hereditaria dentro de las demarcaciones tribales de Canaán", "El propósito de los nombres no era registrar títulos de propiedad de tierras, sino plasmar aspiraciones morales y espirituales."),
            ("pretendían ocultar su linaje tribal para protegerlos de las constantes invasiones de naciones paganas", "No buscaban camuflar su identidad, sino educar a sus hijos con nombres significativos."),
            ("intentaban perpetuar los nombres de los monarcas de Judá para consolidar su lealtad a la casa de David", "El objetivo no era la propaganda dinástica cortesana, sino modelar el carácter personal de los hijos.")
        ],
        "correct_pos": 1,
        "explanation": "PR39 (p. 27) indica expresamente: «Con frecuencia expresaban en ellos los rasgos de carácter que deseaban ver desarrollarse en sus hijos»."
    },
    # Item 45
    {
        "pilot_index": 45,
        "id": "V16-R3-PILOT-045",
        "question": "En la asignación nominal babilónica registrada en Profetas y Reyes (p. 27), la correspondencia biunívoca exacta entre los cuatro jóvenes de Judá y sus apelativos caldeos quedó establecida de modo que ____.",
        "correct_text": "a Daniel se le llamó Beltsasar, a Ananías Sadrach, a Misael Mesach y a Azarías Abednego",
        "distractors": [
            ("a Daniel se le llamó Beltsasar, a Ananías Mesach, a Misael Abednego y a Azarías Sadrach", "Asigna incorrectamente Mesach a Ananías, Abednego a Misael y Sadrach a Azarías."),
            ("a Daniel se le llamó Sadrach, a Ananías Beltsasar, a Misael Mesach y a Azarías Abednego", "Intercambia erróneamente los nombres de Daniel y Ananías."),
            ("a Daniel se le llamó Abednego, a Ananías Sadrach, a Misael Beltsasar y a Azarías Mesach", "Confunde totalmente la asignación nominal de los cuatro jóvenes.")
        ],
        "correct_pos": 0,
        "explanation": "PR39 (p. 27) cita textualmente: «puso a Daniel, Beltsasar; y a Ananías, Sadrach; y a Misael, Mesach; y a Azarías, Abednego»."
    },
    # Item 46
    {
        "pilot_index": 46,
        "id": "V16-R3-PILOT-046",
        "question": "Al evaluar la historicidad y datación del inicio del asedio a Jerusalén según Daniel 1:1, ¿cuál de las siguientes declaraciones expresa una conclusión verdadera fundamentada en el texto bíblico?",
        "correct_text": "Es verdadera la afirmación de que el asedio ocurrió en el año tercero del rey Joacim de Judá cuando vino Nabucodonosor y sitió a Jerusalén",
        "distractors": [
            ("Es falsa la afirmación del asedio en el año tercero de Joacim, porque el primer ataque de Nabucodonosor acaeció en el reinado de Sedequías", "Daniel 1:1 sitúa el asedio explícitamente en el tercer año de Joacim rey de Judá y no en el de Sedequías."),
            ("Es falsa la mención de Nabucodonosor en Daniel 1:1, porque la primera incursión militar contra Judá fue comandada por el rey Nabopolasar", "El texto bíblico nombra de forma directa a Nabucodonosor como el monarca que vino y sitió la ciudad."),
            ("Es verdadera la afirmación de que el asedio ocurrió en el año tercero de Joaquín, cuando las huestes caldeas saquearon los muros de la ciudad", "Confunde a Joacim con su hijo Joaquín, quien reinó solo tres meses y no es el monarca citado en Daniel 1:1.")
        ],
        "correct_pos": 0,
        "explanation": "Daniel 1:1 declara: «En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió»."
    },
    # Item 47
    {
        "pilot_index": 47,
        "id": "V16-R3-PILOT-047",
        "question": "Respecto al desenlace del asedio a Jerusalén y el destino de los utensilios sagrados según Daniel 1:2, ¿cuál de las siguientes evaluaciones teológico-narrativas es correcta?",
        "correct_text": "Es verdadera, porque el Señor entregó a Joacim y parte de los utensilios, los cuales Nabucodonosor llevó a Sinar a la casa del tesoro de su dios",
        "distractors": [
            ("Es falsa, porque el texto bíblico afirma que la totalidad absoluta de los vasos sagrados fue destruida en Jerusalén antes del traslado a Sinar", "Daniel 1:2 indica claramente que se tomó «parte de los utensilios de la casa de Dios» y fueron llevados intactos al tesoro babilónico."),
            ("Es verdadera, porque Joacim entregó voluntariamente el arca del pacto a los caldeos para ser colocada en el templo sagrado de la gran Nínive", "El texto no menciona una entrega voluntaria del arca ni un traslado a Nínive, sino a tierra de Sinar a la casa del tesoro de su dios."),
            ("Es falsa, porque Nabucodonosor no llevó utensilio alguno a Sinar, sino que los repartió de inmediato entre los reyes de los medos y los persas", "El pasaje confirma que Nabucodonosor los trajo a tierra de Sinar y los guardó en la casa del tesoro de su propio dios.")
        ],
        "correct_pos": 1,
        "explanation": "Daniel 1:2 afirma que el Señor entregó en sus manos a Joacim y parte de los utensilios de la casa de Dios, llevándolos a tierra de Sinar a la casa del tesoro de su dios."
    },
    # Item 48
    {
        "pilot_index": 48,
        "id": "V16-R3-PILOT-048",
        "question": "Al analizar la orden de deportación y selección de la nobleza hebrea en Daniel 1:3, ¿cuál de las siguientes proposiciones evalúa con precisión el mandato real y su destinatario?",
        "correct_text": "Es verdadera la orden dada a Aspenaz jefe de los eunucos, requiriendo traer de los hijos de Israel, del linaje real de los príncipes",
        "distractors": [
            ("Es falsa la designación de Aspenaz, porque el rey encomendó la selección a Melsar por ser el mayordomo a cargo del palacio babilónico", "La orden real fue dirigida formalmente a Aspenaz, jefe de los eunucos, y no al mayordomo Melsar."),
            ("Es falsa la condición del linaje, porque el mandato exigía reclutar únicamente muchachos de la clase campesina sin instrucción previa", "El texto bíblico requiere de forma explícita jóvenes «del linaje real de los príncipes» y de los hijos de Israel."),
            ("Es verdadera la instrucción dada a Arioc jefe de la guardia, ordenándole escoger sacerdotes consagrados entre las familias de Leví", "El oficial comisionado en Daniel 1:3 fue Aspenaz (no Arioc) y el grupo objetivo era el linaje real principesco (no sacerdotes levitas).")
        ],
        "correct_pos": 2,
        "explanation": "Daniel 1:3 registra: «Y dijo el rey a Aspenaz, jefe de sus eunucos, que trajera de los hijos de Israel, del linaje real de los príncipes»."
    },
    # Item 49
    {
        "pilot_index": 49,
        "id": "V16-R3-PILOT-049",
        "question": "En cuanto a los rigurosos requisitos pedagógicos y físicos estipulados en Daniel 1:4 (RVR1995), ¿cuál de los siguientes enunciados constituye una evaluación textual fidedigna?",
        "correct_text": "Es verdadera, pues exigía muchachos sin tacha, de buen parecer, instruidos en sabiduría, sabios en ciencia y aptos para aprender letras y lengua caldeas",
        "distractors": [
            ("Es falsa, pues el texto bíblico prescindía del aspecto físico y demandaba únicamente que fuesen peritos en artes bélicas y magia sacerdotal de Sinar", "Daniel 1:4 exigía expresamente muchachos «en quienes no hubiera tacha alguna, de buen parecer», excluyendo artes bélicas o magia idolátrica."),
            ("Es verdadera, pues prescribía que se les adiestrara en la lengua aramea oriental sin requerir buen entendimiento ni aptitud para el palacio del monarca", "El texto demandaba «buen entendimiento e idóneos para estar en el palacio del rey», aprendiendo las letras y lengua de los caldeos."),
            ("Es falsa, pues prohibía terminantemente que los jóvenes aprendieran la literatura caldea para evitar la corrupción de su fe monoteísta en Babilonia", "El mandato real ordenaba específicamente «que les enseñara las letras y la lengua de los caldeos».")
        ],
        "correct_pos": 0,
        "explanation": "Daniel 1:4 enumera los requisitos exactos: sin tacha, buen parecer, instruidos en sabiduría, sabios en ciencia, buen entendimiento, idóneos para el palacio y para aprender letras y lengua caldeas."
    },
    # Item 50
    {
        "pilot_index": 50,
        "id": "V16-R3-PILOT-050",
        "question": "En relación con la provisión alimentaria y el programa formativo decretado por el monarca en Daniel 1:5, ¿cuál de las siguientes afirmaciones evalúa correctamente el mandato real?",
        "correct_text": "Es verdadera, porque el rey les señaló una porción diaria de su comida y de su vino, fijando tres años de educación antes de comparecer ante él",
        "distractors": [
            ("Es falsa, porque la ración de comida y vino real era de suministro semanal y el período de adiestramiento en la corte abarcaba cinco años enteros", "La asignación era diaria (no semanal) y el tiempo formativo correspondía a tres años (no cinco)."),
            ("Es falsa, porque el rey ordenó que los cautivos comieran legumbres desde el inicio para verificar su resistencia física ante los nobles caldeos", "La dieta de legumbres fue una propuesta de Daniel a Melsar en Daniel 1:12, no un decreto de Nabucodonosor en Daniel 1:5."),
            ("Es verdadera, porque la dieta incluía carne consagrada y sidra, fijando un período formativo de diez meses previo a su presentación ante el rey", "El texto especifica comida del rey y el vino que él bebía durante tres años, no diez meses.")
        ],
        "correct_pos": 3,
        "explanation": "Daniel 1:5 estipula: «Y les señaló el rey una porción diaria de la comida del rey y del vino que él bebía; y que los educara durante tres años, para que al fin de ellos se presentaran delante del rey»."
    },
    # Item 51
    {
        "pilot_index": 51,
        "id": "V16-R3-PILOT-051",
        "question": "Sobre la nómina y procedencia tribal de los cuatro jóvenes destacados en Daniel 1:6, ¿cuál de las siguientes declaraciones contiene una evaluación correcta según el texto bíblico?",
        "correct_text": "Es verdadera la mención de Daniel, Ananías, Misael y Azarías como príncipes procedentes del linaje de los hijos de Judá",
        "distractors": [
            ("Es falsa la inclusión de Azarías, puesto que el cuarto joven hebreo seleccionado en la corte real fue el profeta Nehemías", "Azarías es el cuarto joven expresamente nombrado en Daniel 1:6 junto a Daniel, Ananías y Misael."),
            ("Es falsa la filiación con Judá, porque el texto bíblico afirma que los cuatro jóvenes procedían de la tribu de Benjamín", "Daniel 1:6 declara literalmente que pertenecían a los «hijos de Judá» y no a Benjamín."),
            ("Es verdadera la afirmación de que procedían de Manasés, siendo inscritos de inmediato con sus nombres babilónicos en Sinar", "Procedían de Judá y son presentados con sus nombres hebreos originales.")
        ],
        "correct_pos": 1,
        "explanation": "Daniel 1:6 declara: «Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá»."
    },
    # Item 52
    {
        "pilot_index": 52,
        "id": "V16-R3-PILOT-052",
        "question": "Al evaluar la imposición de nombres cortesanos por el jefe de los eunucos en Daniel 1:7 (RVR1995), ¿cuál de las siguientes afirmaciones es textualmente correcta?",
        "correct_text": "Es verdadera, porque a Daniel llamó Beltsasar, a Ananías Sadrac, a Misael Mesac y a Azarías Abed-nego",
        "distractors": [
            ("Es falsa, porque a Daniel llamó Sadrac, a Ananías Beltsasar, a Misael Abed-nego y a Azarías Mesac", "Intercambia erróneamente los nombres asignados a los cuatro jóvenes."),
            ("Es falsa, porque el rey Nabucodonosor en persona y no el jefe de los eunucos impuso los nuevos nombres", "El texto bíblico atribuye expresamente la acción al «jefe de los eunucos» («A estos el jefe de los eunucos puso nombres»)."),
            ("Es verdadera, porque a Daniel llamó Baltasar, a Ananías Mesac, a Misael Sadrac y a Azarías Aspenaz", "Confunde las asignaciones y utiliza Aspenaz como si fuera el nombre de Azarías.")
        ],
        "correct_pos": 2,
        "explanation": "Daniel 1:7 detalla: «A estos el jefe de los eunucos puso nombres: a Daniel, Beltsasar; a Ananías, Sadrac; a Misael, Mesac; y a Azarías, Abed-nego»."
    },
    # Item 53
    {
        "pilot_index": 53,
        "id": "V16-R3-PILOT-053",
        "question": "En cuanto a la resolución de integridad tomada por Daniel y su petición ante las autoridades caldeas en Daniel 1:8, ¿cuál de las siguientes proposiciones es correcta?",
        "correct_text": "Es verdadera, porque Daniel propuso en su corazón no contaminarse con la comida ni el vino del rey, pidiendo al jefe de los eunucos no ser obligado a contaminarse",
        "distractors": [
            ("Es falsa, porque Daniel aceptó consumir la comida y el vino real durante los primeros tres años para no despertar sospechas ante los magistrados de Babilonia", "Daniel no contemporizó ni aceptó la comida real en ningún momento, resolviendo en su corazón no contaminarse desde el inicio."),
            ("Es falsa, porque la solicitud de abstinencia alimentaria fue presentada por Daniel directamente ante Nabucodonosor en una audiencia pública en su palacio", "Daniel presentó su petición respetuosa ante el jefe de los eunucos y no ante el rey en audiencia pública."),
            ("Es verdadera, porque Daniel resolvió ayunar de todo alimento durante los tres años de su preparación, sustentándose únicamente por intervención angélica", "Daniel no propuso un ayuno absoluto prolongado con sustento angélico, sino una alimentación basada en legumbres y agua.")
        ],
        "correct_pos": 0,
        "explanation": "Daniel 1:8 relata: «Daniel propuso en su corazón no contaminarse con la porción de la comida del rey ni con el vino que él bebía; pidió, por tanto, al jefe de los eunucos que no se le obligara a contaminarse»."
    },
    # Item 54
    {
        "pilot_index": 54,
        "id": "V16-R3-PILOT-054",
        "question": "Al considerar la intervención divina en favor de Daniel ante las autoridades de la corte babilónica en Daniel 1:9, ¿cuál de los siguientes juicios es verdadero?",
        "correct_text": "Es verdadera la declaración de que Dios puso a Daniel en gracia y en buena voluntad con el jefe de los eunucos",
        "distractors": [
            ("Es falsa la intervención divina, porque Daniel obtuvo el favor del jefe de los eunucos mediante sobornos de oro", "La Biblia afirma con total claridad que fue Dios quien intervino directamente poniendo a Daniel en gracia y benevolencia."),
            ("Es falsa la mención del jefe de los eunucos, porque el texto bíblico indica que la gracia fue ante el rey Ciro", "Daniel 1:9 sitúa este favor ante el jefe de los eunucos de Babilonia y no ante Ciro monarca de Persia."),
            ("Es verdadera la afirmación de que Dios infundió terror en el corazón de Aspenaz mediante un sueño amenazante", "Dios no provocó terror ni envió sueños punitivos a Aspenaz, sino que dispuso su corazón con buena voluntad hacia Daniel.")
        ],
        "correct_pos": 3,
        "explanation": "Daniel 1:9 dice textualmente: «Puso Dios a Daniel en gracia y en buena voluntad con el jefe de los eunucos»."
    },
    # Item 55
    {
        "pilot_index": 55,
        "id": "V16-R3-PILOT-055",
        "question": "Al evaluar la respuesta y el temor expresado por el jefe de los eunucos ante la solicitud de Daniel en Daniel 1:10, ¿cuál de las siguientes proposiciones es correcta?",
        "correct_text": "Es verdadera, porque temía que el rey viese los rostros más pálidos que los de muchachos semejantes y lo condenase a muerte",
        "distractors": [
            ("Es falsa, porque el funcionario temía que los jóvenes aumentasen de peso y fuesen descalificados para el servicio palaciego", "El temor del eunuco radicaba en que los rostros lucieran más pálidos o desmejorados, no en un aumento de peso."),
            ("Es falsa, porque el jefe de los eunucos rehusó la petición alegando que las leyes caldeas castigaban el consumo de legumbres", "No apeló a leyes sobre legumbres, sino a la orden directa del rey sobre la asignación de comida y bebida y el riesgo de pena capital."),
            ("Es verdadera, porque temía que los otros muchachos se amotinaran al notar una distinción en las raciones de comida del rey", "El peligro temido era la sentencia de muerte dictada por el monarca si veía a los cautivos desmejorados, no un motín.")
        ],
        "correct_pos": 1,
        "explanation": "Daniel 1:10 registra el temor de Aspenaz: que el rey viese sus rostros más pálidos que los de los muchachos semejantes y condenase al oficial a muerte."
    },
    # Item 56
    {
        "pilot_index": 56,
        "id": "V16-R3-PILOT-056",
        "question": "Respecto a la estructura jerárquica y el interlocutor inmediato al que acudió Daniel según Daniel 1:11 (RVR1995), ¿cuál de las siguientes declaraciones es textualmente fidedigna?",
        "correct_text": "Es verdadera, porque Daniel acudió a Melsar, a quien el jefe de los eunucos había puesto sobre Daniel, Ananías, Misael y Azarías",
        "distractors": [
            ("Es falsa, porque Daniel acudió a Arioc jefe de la guardia, quien ejercía supervisión directa sobre la ración de los cuatro jóvenes", "Daniel acudió a Melsar (mayordomo asignado) y no a Arioc, capitán de la guardia."),
            ("Es falsa, porque Melsar había sido nombrado por el monarca como gobernador de Babilonia y no como mayordomo de los cuatro jóvenes", "Melsar era el encargado puesto por el jefe de los eunucos sobre los cuatro jóvenes de Judá, no el gobernador provincial."),
            ("Es verdadera, porque Daniel acudió al mayordomo que Aspenaz había designado como custodio de los sacerdotes caldeos del palacio", "Melsar estaba puesto específicamente sobre Daniel, Ananías, Misael y Azarías, no sobre sacerdotes caldeos.")
        ],
        "correct_pos": 0,
        "explanation": "Daniel 1:11 afirma: «Entonces dijo Daniel a Melsar, a quien el jefe de los eunucos había puesto sobre Daniel, Ananías, Misael y Azarías»."
    },
    # Item 57
    {
        "pilot_index": 57,
        "id": "V16-R3-PILOT-057",
        "question": "Al evaluar los términos exactos de la propuesta de prueba alimentaria presentada por Daniel en Daniel 1:12, ¿cuál de los siguientes enunciados es verdadero según el texto bíblico?",
        "correct_text": "Es verdadero, porque Daniel solicitó una prueba de diez días pidiendo que se les diera legumbres para comer y agua para beber",
        "distractors": [
            ("Es falso, porque Daniel propuso una prueba de cuarenta días en la cual demandó consumir pan sin levadura y frutos secos de Judá", "La prueba pedida fue de diez días con legumbres y agua, no de cuarenta días ni con frutos secos."),
            ("Es falso, porque la petición contemplaba una duración de siete días con una dieta de pescado, hierbas amargas y agua de manantial", "El período no fue de siete días ni incluía pescado o hierbas amargas pascuales."),
            ("Es verdadero, porque la prueba consistía en tres semanas completas de abstinencia en las cuales no entró carne, vino ni ungüento", "Confunde la aflicción y duelo de Daniel 10:2-3 con la prueba de diez días de Daniel 1:12.")
        ],
        "correct_pos": 2,
        "explanation": "Daniel 1:12 expresa: «Te ruego que hagas la prueba con tus siervos durante diez días: que nos den legumbres para comer y agua para beber»."
    },
    # Item 58
    {
        "pilot_index": 58,
        "id": "V16-R3-PILOT-058",
        "question": "En cuanto al criterio comparativo y la decisión subsiguiente propuestos por Daniel en Daniel 1:13, ¿cuál de las siguientes afirmaciones contiene una evaluación verdadera?",
        "correct_text": "Es verdadera, pues propuso comparar sus rostros con los de los muchachos que comían de la comida del rey y actuar según lo observado",
        "distractors": [
            ("Es falsa, pues Daniel pidió someter a ambos grupos a un examen de astronomía ante los sacerdotes caldeos para juzgar el vigor corporal", "La evaluación no consistía en un certamen astronómico, sino en la observación directa de su aspecto y semblante."),
            ("Es falsa, pues exigió que Nabucodonosor en persona fuera el único juez autorizado para examinar la complexión física de los cautivos", "Daniel encomendó el examen a Melsar («haz después con tus siervos según veas») y no a una audiencia imperial inmediata."),
            ("Es verdadera, pues propuso que si sus rostros desmejoraban, aceptarían de inmediato el vino y los manjares reales ofrecidos en palacio", "Daniel no hizo una promesa de transigencia idolátrica, sino que confió plenamente en los resultados que Dios produciría.")
        ],
        "correct_pos": 3,
        "explanation": "Daniel 1:13 dice: «Compara luego nuestros rostros con los rostros de los muchachos que comen de la porción de la comida del rey, y haz después con tus siervos según veas»."
    },
    # Item 59
    {
        "pilot_index": 59,
        "id": "V16-R3-PILOT-059",
        "question": "Respecto a la anuencia y ejecución de la prueba por parte del mayordomo en Daniel 1:14, ¿cuál de los siguientes juicios es textualmente correcto?",
        "correct_text": "Es verdadero, porque Melsar consintió con ellos en esto y probó con ellos durante diez días en la corte",
        "distractors": [
            ("Es falso, porque el mayordomo rechazó el pedido por temor a ser ejecutado de inmediato por el rey pagano", "Daniel 1:14 indica expresamente que Melsar consintió con ellos y probó durante diez días."),
            ("Es falso, porque Melsar redujo el plazo a tres días tras consultar en secreto con los sabios de Babilonia", "No redujo los días a tres ni consultó a los sabios caldeos."),
            ("Es verdadero, porque Melsar extendió la prueba a treinta días para incluir a todos los príncipes cautivos", "La prueba duró exactamente diez días y se aplicó a los cuatro jóvenes.")
        ],
        "correct_pos": 1,
        "explanation": "Daniel 1:14 ratifica: «Consintió, pues, con ellos en esto, y probó con ellos durante diez días»."
    },
    # Item 60
    {
        "pilot_index": 60,
        "id": "V16-R3-PILOT-060",
        "question": "Al cumplirse el plazo experimental fijado en Daniel 1:15 (RVR1995), ¿cuál de las siguientes afirmaciones evalúa con rigor bíblico el resultado somático comprobado en los jóvenes?",
        "correct_text": "Es verdadera, porque al cabo de los diez días el rostro de ellos pareció mejor y más robusto que el de los otros muchachos",
        "distractors": [
            ("Es falsa, porque sus rostros se demudaron y palidecieron notablemente, obligando a Melsar a suministrarles vino medicinal", "El texto niega cualquier deterioro: su semblante lució mejor y más robusto que el de quienes comían los manjares reales."),
            ("Es falsa, porque no hubo diferencia visible alguna entre los jóvenes hebreos y los muchachos que comían de la mesa del rey", "Hubo una notable superioridad física visible en los rostros de los cuatro jóvenes."),
            ("Es verdadera, porque aunque adelgazaron en extremo, mostraron una memoria superior en las pruebas de cálculo de Babilonia", "No adelgazaron ni se evaluó cálculo en ese momento, sino que su desarrollo físico y nutricional fue marcadamente superior.")
        ],
        "correct_pos": 0,
        "explanation": "Daniel 1:15 testifica: «Y al cabo de los diez días pareció el rostro de ellos mejor y más robusto que el de los otros muchachos que comían de la porción de la comida del rey»."
    }
]

# Validation and assembly
output_questions = []
for rq, dossier in zip(raw_questions, dossiers_data):
    assert rq["id"] == dossier["id"]
    assert rq["pilot_index"] == dossier["pilot_index"]
    
    pos = rq["correct_pos"]
    correct = rq["correct_text"]
    dist_items = rq["distractors"]
    assert len(dist_items) == 3
    
    options = []
    d_idx = 0
    why_fail = {}
    for i in range(4):
        if i == pos:
            options.append(correct)
        else:
            d_text, d_reason = dist_items[d_idx]
            options.append(d_text)
            why_fail[d_text] = d_reason
            d_idx += 1
            
    # Check length ratio
    lens = [len(opt) for opt in options]
    min_len = min(lens)
    max_len = max(lens)
    ratio = max_len / min_len
    
    print(f"Item {rq['id']}: min={min_len}, max={max_len}, ratio={ratio:.3f}")
    if ratio >= 1.15:
        print(f"WARNING: Ratio too high for {rq['id']}: {ratio:.3f}")
        for opt in options:
            print(f"  ({len(opt)}) {opt}")
            
    q_obj = {
        "id": rq["id"],
        "pilot_index": rq["pilot_index"],
        "question_id": rq["id"],
        "fact_id": dossier["fact_id"],
        "chapter": dossier["chapter"],
        "source_unit_id": dossier["source_unit_id"],
        "source_ref": dossier["source_ref"],
        "source_quote": dossier["source_quote"],
        "source_page": dossier["source_page"],
        "family": dossier["family"],
        "translation_noise": dossier["translation_noise"],
        "target_difficulty": dossier["target_difficulty"],
        "difficulty": dossier["target_difficulty"].lower(),
        "question": rq["question"],
        "options": options,
        "correct_option": pos,
        "accepted_answers": [correct],
        "explanation": rq["explanation"],
        "why_distractors_fail": why_fail
    }
    output_questions.append(q_obj)

print(f"Total compiled questions: {len(output_questions)}")
out_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "authors" / "author_2"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "batch_2.json"
out_file.write_text(json.dumps(output_questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote to {out_file}")
