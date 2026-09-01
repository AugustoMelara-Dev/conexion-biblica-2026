import json, pathlib
ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

results = [
  {
    "blind_batch_id": "blind-28f71b1e6f53d3157e8b",
    "target_batch": "DAN1-C20",
    "reviews": [
      {
        "id": "V14-R2-DAN1-C20-001",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto bíblico de Daniel 1:1 declara explícitamente la fecha cronológica y el monarca judío reinante durante la incursión militar babilónica: 'En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió'. La opción en el índice 2 es la única correcta.",
        "source_alignment_reason": "Correspondencia textual directa e incontrovertible con Daniel 1:1."
      },
      {
        "id": "V14-R2-DAN1-C20-002",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 1:2 describe con precisión geográfica y cultual el traslado de los vasos sagrados: 'los trajo a tierra de Sinar, a la casa de su dios, y colocó los utensilios en la casa del tesoro de su dios'. La opción en el índice 1 reproduce fielmente este doble destino.",
        "source_alignment_reason": "Alineación literal y completa con Daniel 1:2."
      },
      {
        "id": "V14-R2-DAN1-C20-003",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "De acuerdo con Daniel 1:3, la orden real fue dirigida 'a Aspenaz, jefe de sus eunucos, que trajera de los hijos de Israel, del linaje real de los príncipes'. La opción en el índice 0 contiene con total exactitud tanto el funcionario como la ascendencia requerida.",
        "source_alignment_reason": "Correspondencia exacta con el texto de Daniel 1:3."
      },
      {
        "id": "V14-R2-DAN1-C20-004",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 1:4 enumera rigurosamente las condiciones físicas, cognitivas e institucionales exigidas ('en quienes no hubiera tacha alguna, de buen parecer, instruidos en toda sabiduría, sabios en ciencia, de buen entendimiento e idóneos para estar en el palacio del rey') junto al currículo formativo ('y que les enseñara las letras y la lengua de los caldeos'). La opción en el índice 1 es inequívocamente exacta.",
        "source_alignment_reason": "Reproducción exhaustiva y fiel de los requisitos y asignación de Daniel 1:4."
      },
      {
        "id": "V14-R2-DAN1-C20-005",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 1:5 estipula con absoluta claridad la provisión y el término educativo: 'una porción diaria de la comida del rey y del vino que él bebía; y que los educara durante tres años, para que al fin de ellos se presentaran delante del rey'. La opción en el índice 2 refleja estos dos elementos sin ambigüedad.",
        "source_alignment_reason": "Concordancia precisa con Daniel 1:5."
      },
      {
        "id": "V14-R2-DAN1-C20-006",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El registro de Daniel 1:6 identifica nominativamente a los cuatro jóvenes: 'Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá'. La opción en el índice 0 concuerda textualmente.",
        "source_alignment_reason": "Coincidencia canónica unívoca con Daniel 1:6."
      },
      {
        "id": "V14-R2-DAN1-C20-007",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 1:7 detalla la cuádruple asignación onomástica babilónica: 'a Daniel, Beltsasar; a Ananías, Sadrac; a Misael, Mesac; y a Azarías, Abed-nego'. La opción en el índice 3 reproduce con precisión los cuatro nombres en su correspondiente orden.",
        "source_alignment_reason": "Exactitud absoluta respecto a Daniel 1:7."
      },
      {
        "id": "V14-R2-DAN1-C20-008",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 1:8 relata el compromiso ético-religioso del profeta y su gestión ante el oficial: 'Daniel propuso en su corazón no contaminarse con la porción de la comida del rey ni con el vino que él bebía; pidió, por tanto, al jefe de los eunucos que no se le obligara a contaminarse'. La opción en el índice 0 es la formulación textual exacta.",
        "source_alignment_reason": "Concordancia directa y estricta con Daniel 1:8."
      },
      {
        "id": "V14-R2-DAN1-C20-009",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "En Daniel 1:10, el jefe de los eunucos externa su justificado temor ante las repercusiones físicas del régimen alimenticio: '«Temo a mi señor el rey, que asignó vuestra comida y vuestra bebida; pues luego que él vea vuestros rostros más pálidos que los de los muchachos que son semejantes a vosotros, haréis que el rey me condene a muerte.»'. La opción en el índice 3 es una correspondencia literal incontrovertible.",
        "source_alignment_reason": "Alineación fidedigna con la declaración de Daniel 1:10."
      },
      {
        "id": "V14-R2-DAN1-C20-010",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 1:13 presenta la propuesta empírica de evaluación fisonómica tras diez días de prueba: 'Compara luego nuestros rostros con los rostros de los muchachos que comen de la porción de la comida del rey, y haz después con tus siervos según veas'. La opción en el índice 0 coincide palabra por palabra con el texto canónico.",
        "source_alignment_reason": "Correspondencia literal con Daniel 1:13."
      }
    ]
  },
  {
    "blind_batch_id": "blind-e20d4291c8d12c8622bc",
    "target_batch": "DAN2-C16",
    "reviews": [
      {
        "id": "V14-R2-DAN2-C16-001",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:2 cataloga los cuatro gremios de sabios convocados por el monarca: 'Hizo llamar el rey a magos, astrólogos, encantadores y caldeos, para que le explicaran sus sueños'. La opción en el índice 3 lista exactamente las cuatro categorías bíblicas.",
        "source_alignment_reason": "Correspondencia textual estricta con Daniel 2:2."
      },
      {
        "id": "V14-R2-DAN2-C16-002",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "En Daniel 2:3, las palabras de apertura del soberano definen su aflicción mental: 'El rey les dijo: —He tenido un sueño, y mi espíritu se ha turbado por saber el sueño'. La opción en el índice 2 coincide palabra por palabra con el reporte bíblico.",
        "source_alignment_reason": "Concordancia directa e idéntica con Daniel 2:3."
      },
      {
        "id": "V14-R2-DAN2-C16-003",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:4 señala el idioma de interlocución cortesana y la respuesta condicional de los caldeos: 'Entonces hablaron los caldeos al rey en lengua aramea: —¡Rey, para siempre vive! Cuenta el sueño a tus siervos, y te daremos la interpretación'. La opción en el índice 1 captura tanto el idioma como la fórmula ceremonial y la petición.",
        "source_alignment_reason": "Alineación rigurosa con Daniel 2:4."
      },
      {
        "id": "V14-R2-DAN2-C16-004",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:5 pronuncia el drástico doble castigo corporal y patrimonial: 'seréis hechos pedazos y vuestras casas serán convertidas en estercoleros'. La opción en el índice 2 cita textualmente las dos penalidades.",
        "source_alignment_reason": "Correspondencia literal con Daniel 2:5."
      },
      {
        "id": "V14-R2-DAN2-C16-005",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:6 especifica la triple recompensa ofrecida por el monarca: 'de mí recibiréis dones, favores y gran honra'. La opción en el índice 2 reproduce con fidelidad los tres conceptos bíblicos.",
        "source_alignment_reason": "Coincidencia unívoca y exacta con Daniel 2:6."
      },
      {
        "id": "V14-R2-DAN2-C16-006",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "En Daniel 2:7, los sabios caldeos reiteran su postura: 'Respondieron por segunda vez, y dijeron: —Cuente el rey el sueño a sus siervos, y le daremos la interpretación'. La opción en el índice 3 recoge textualmente esta segunda réplica.",
        "source_alignment_reason": "Alineación canónica estricta con Daniel 2:7."
      },
      {
        "id": "V14-R2-DAN2-C16-007",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:8 expone la acusación de dilación táctica formulada por el rey: 'Yo conozco ciertamente que vosotros ponéis dilaciones, porque veis que el asunto se me ha ido'. La opción en el índice 3 coincide plenamente con la cita.",
        "source_alignment_reason": "Concordancia textual exacta con Daniel 2:8."
      },
      {
        "id": "V14-R2-DAN2-C16-008",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:9 formula la sospecha de colusión y engaño ('Ciertamente preparáis una respuesta mentirosa y perversa que decir delante de mí, entre tanto que pasa el tiempo') y la condición epistemológica exigida ('Contadme, pues, el sueño, para que yo sepa que me podéis dar su interpretación'). La opción en el índice 1 sintetiza con exactitud ambos componentes.",
        "source_alignment_reason": "Fidelidad temática y textual respecto a Daniel 2:9."
      },
      {
        "id": "V14-R2-DAN2-C16-009",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:10 consigna la doble defensa caldea: la incapacidad universal humana ('No hay hombre sobre la tierra que pueda declarar el asunto del rey') y la ausencia de precedente imperial ('ningún rey, príncipe ni señor preguntó cosa semejante a ningún mago ni astrólogo ni caldeo'). La opción en el índice 3 articula con exactitud ambas afirmaciones.",
        "source_alignment_reason": "Correspondencia completa con Daniel 2:10."
      },
      {
        "id": "V14-R2-DAN2-C16-010",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:11 concluye el argumento caldeo restringiendo la revelación a un plano trascendente: 'salvo los dioses cuya morada no está entre los hombres'. La opción en el índice 0 contiene la cita textual exacta.",
        "source_alignment_reason": "Concordancia literal con Daniel 2:11."
      }
    ]
  },
  {
    "blind_batch_id": "blind-68efef1d540c0d40d9b7",
    "target_batch": "DAN2-C20",
    "reviews": [
      {
        "id": "V14-R2-DAN2-C20-001",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:12 declara el estado afectivo violento y la orden de ejecución masiva: 'Por esto el rey, con ira y con gran enojo, mandó que mataran a todos los sabios de Babilonia'. La opción en el índice 0 coincide palabra por palabra con el pasaje.",
        "source_alignment_reason": "Alineación textual directa con Daniel 2:12."
      },
      {
        "id": "V14-R2-DAN2-C20-002",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:13 define el alcance del decreto y la búsqueda fatal de los jóvenes hebreos: 'Se publicó, pues, el edicto de que los sabios fueran llevados a la muerte; y buscaron también a Daniel y a sus compañeros para matarlos'. La opción en el índice 2 es la formulación canónica exacta.",
        "source_alignment_reason": "Fidelidad absoluta con Daniel 2:13."
      },
      {
        "id": "V14-R2-DAN2-C20-003",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:14 subraya el dominio propio y prudencia de Daniel frente al verdugo real: 'Entonces Daniel habló sabia y prudentemente a Arioc, capitán de la guardia del rey, que había salido para matar a los sabios de Babilonia'. La opción en el índice 3 reproduce textualmente este versículo.",
        "source_alignment_reason": "Correspondencia literal con Daniel 2:14."
      },
      {
        "id": "V14-R2-DAN2-C20-004",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:15 registra la interrogante de Daniel y la subsiguiente aclaración del oficial: '—¿Cuál es la causa de que este edicto se publique de parte del rey tan apresuradamente? Entonces Arioc hizo saber a Daniel lo que había'. La opción en el índice 1 concuerda palabra por palabra.",
        "source_alignment_reason": "Concordancia directa e idéntica con Daniel 2:15."
      },
      {
        "id": "V14-R2-DAN2-C20-005",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:16 refiere la petición de tiempo y la promesa ante el rey: 'y Daniel entró y pidió al rey que le concediera tiempo, que él daría al rey la interpretación'. La opción en el índice 3 coincide fielmente con el texto canónico.",
        "source_alignment_reason": "Alineación estricta con Daniel 2:16."
      },
      {
        "id": "V14-R2-DAN2-C20-006",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:17 indica la acción inmediata de Daniel: 'Luego se fue Daniel a su casa e hizo saber a Ananías, Misael y Azarías, sus compañeros, lo que sucedía'. La opción en el índice 1 reproduce con precisión el lugar y los receptores de la noticia.",
        "source_alignment_reason": "Correspondencia literal con Daniel 2:17."
      },
      {
        "id": "V14-R2-DAN2-C20-007",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:18 formula el objetivo de la oración comunitaria: 'para que pidieran misericordias del Dios del cielo sobre este misterio, a fin de que Daniel y sus compañeros no perecieran con los otros sabios de Babilonia'. La opción en el índice 2 es la transcripción exacta del versículo.",
        "source_alignment_reason": "Concordancia plena con Daniel 2:18."
      },
      {
        "id": "V14-R2-DAN2-C20-008",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:19 describe el canal de iluminación y la subsiguiente alabanza: 'El secreto le fue revelado a Daniel en visión de noche, por lo cual bendijo Daniel al Dios del cielo'. La opción en el índice 2 es la única respuesta canónica válida.",
        "source_alignment_reason": "Fidelidad textual absoluta con Daniel 2:19."
      },
      {
        "id": "V14-R2-DAN2-C20-009",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:20 recoge el inicio del cántico de alabanza: 'Sea bendito el nombre de Dios de siglos en siglos, porque suyos son el poder y la sabiduría'. La opción en el índice 1 reproduce con exactitud estos dos atributos y la doxología.",
        "source_alignment_reason": "Alineación literal con Daniel 2:20."
      },
      {
        "id": "V14-R2-DAN2-C20-010",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 2:21 detalla las cuatro prerrogativas divinas: 'Él muda los tiempos y las edades, quita reyes y pone reyes; da la sabiduría a los sabios y la ciencia a los entendidos'. La opción en el índice 1 es la formulación textual completa y exacta.",
        "source_alignment_reason": "Correspondencia incontrovertible con Daniel 2:21."
      }
    ]
  },
  {
    "blind_batch_id": "blind-388c3e24bc84711c1c38",
    "target_batch": "DAN3-C16",
    "reviews": [
      {
        "id": "V14-R2-DAN3-C16-001",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:1 registra las dimensiones y el emplazamiento de la imagen: 'cuya altura era de sesenta codos y la anchura de seis codos; la levantó en el campo de Dura, en la provincia de Babilonia'. La opción en el índice 0 coincide punto por punto con los datos canónicos.",
        "source_alignment_reason": "Correspondencia cuantitativa y geográfica exacta con Daniel 3:1."
      },
      {
        "id": "V14-R2-DAN3-C16-002",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:2 señala el propósito ceremonial de la gran asamblea: 'para que vinieran a la dedicación de la estatua que el rey Nabucodonosor había levantado'. La opción en el índice 3 refleja textualmente la motivación de la convocatoria.",
        "source_alignment_reason": "Concordancia directa con Daniel 3:2."
      },
      {
        "id": "V14-R2-DAN3-C16-003",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:4 cita la fórmula universal proclamada por el pregonero: '«Se os ordena a vosotros, pueblos, naciones y lenguas»'. La opción en el índice 3 contiene la triple categorización bíblica.",
        "source_alignment_reason": "Alineación literal con la proclama de Daniel 3:4."
      },
      {
        "id": "V14-R2-DAN3-C16-004",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:5 cataloga la orquesta cúltica imperial: 'al oír el son de la bocina, la flauta, la cítara, el arpa, el salterio, la zampoña y todo instrumento de música'. La opción en el índice 2 incluye con exactitud el elenco instrumental.",
        "source_alignment_reason": "Concordancia rigurosa y completa con Daniel 3:5."
      },
      {
        "id": "V14-R2-DAN3-C16-005",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:6 conmina con una penalidad instantánea: 'inmediatamente será echado dentro de un horno de fuego ardiente'. La opción en el índice 3 transcribe textualmente el plazo y el suplicio.",
        "source_alignment_reason": "Correspondencia exacta con Daniel 3:6."
      },
      {
        "id": "V14-R2-DAN3-C16-006",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:9 presenta el saludo ceremonial cortesano de los acusadores caldeos: '—¡Rey, para siempre vive!'. La opción en el índice 0 coincide con la salutación textual.",
        "source_alignment_reason": "Alineación literal con Daniel 3:9."
      },
      {
        "id": "V14-R2-DAN3-C16-007",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:11 repite el mandato sancionatorio: 'y el que no se postre y adore, sea echado dentro de un horno de fuego ardiente'. La opción en el índice 0 reproduce textualmente la cita del versículo.",
        "source_alignment_reason": "Correspondencia unívoca con Daniel 3:11."
      },
      {
        "id": "V14-R2-DAN3-C16-008",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:18 registra la firme e incondicional declaración de fe: 'Y si no, has de saber, oh rey, que no serviremos a tus dioses ni tampoco adoraremos la estatua que has levantado'. La opción en el índice 3 coincide fielmente con el testimonio bíblico.",
        "source_alignment_reason": "Fidelidad textual estricta con Daniel 3:18."
      },
      {
        "id": "V14-R2-DAN3-C16-009",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:20 identifica al contingente militar seleccionado: 'hombres muy vigorosos que tenía en su ejército'. La opción en el índice 2 refleja exactamente la designación bíblica.",
        "source_alignment_reason": "Concordancia directa con Daniel 3:20."
      },
      {
        "id": "V14-R2-DAN3-C16-010",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:21 enumera de manera pormenorizada las cuatro prendas con que fueron atados: 'con sus mantos, sus calzados, sus turbantes y sus vestidos'. La opción en el índice 1 lista exactamente las cuatro piezas indumentarias.",
        "source_alignment_reason": "Correspondencia exhaustiva y literal con Daniel 3:21."
      }
    ]
  }
]

for res in results:
    p_id = res["blind_batch_id"]
    payload = {
        "schema_version": "competitive-v13-review/v1",
        "blind_batch_id": p_id,
        "reviewer": {
            "id": "arbitro-ciego-subagent-2",
            "conversation_id": "c1418f52-6e95-419a-8033-b691b9955203",
            "model": "gemini-3.7-flash"
        },
        "reviewed_at": "2026-09-01T05:13:38Z",
        "total_reviewed": len(res["reviews"]),
        "verdict_counts": {
            "approved": sum(1 for r in res["reviews"] if r["decision"] == "approved"),
            "rewrite": sum(1 for r in res["reviews"] if r["decision"] == "rewrite"),
            "rejected": sum(1 for r in res["reviews"] if r["decision"] == "rejected")
        },
        "decisions": res["reviews"]
    }
    rf = reviews_dir / f"{p_id}.json"
    rf.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved review for {p_id} ({res['target_batch']})")
