import json, pathlib
ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

packets_data = [
  {
    "blind_batch_id": "blind-cf93a2a6ccb37c1f4159",
    "chapter_reference": "PR42-C19",
    "reviews": [
      {
        "id": "V14-R2-PR42-C19-001",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente afirma textualmente que tras la revelación recibida por el monarca: 'Fué lo que sucedió después del sueño de la gran imagen.' Las demás alternativas refieren hechos históricos o construcciones que no corresponden al contexto del pasaje.",
        "source_alignment_reason": "Coincidencia textual directa e inequívoca con PR42, p. 43, párr. 1 ('Fué lo que sucedió después del sueño de la gran imagen')."
      },
      {
        "id": "V14-R2-PR42-C19-002",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto declara que el monarca fue profundamente impresionado por el pensamiento de 'que el Imperio Babilónico, por universal que fuera, iba a caer finalmente y otros reinos ejercerían el dominio, hasta que al fin todas las potencias terrenales cedieran su lugar a un reino establecido por el Dios del cielo para nunca ser destruido'.",
        "source_alignment_reason": "Alineación fidedigna con PR42, p. 43, párr. 1, reproduciendo la sucesión de imperios y el triunfo final del reino divino."
      },
      {
        "id": "V14-R2-PR42-C19-003",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La cita señala explícitamente que tiempo después 'perdió de vista el noble concepto que tenía del propósito de Dios concerniente a las naciones'. Las otras opciones plantean actos anacrónicos o inventados.",
        "source_alignment_reason": "Correspondencia textual exacta con PR42, p. 43, párr. 2."
      },
      {
        "id": "V14-R2-PR42-C19-004",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto cita la confesión del rey reconociendo que 'el reino de Dios es «sempiterno, y su señorío hasta generación y generación.»'. Ninguna otra opción representa el testimonio monárquico.",
        "source_alignment_reason": "Cita canónica directa de PR42, p. 43, párr. 2."
      },
      {
        "id": "V14-R2-PR42-C19-005",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto referencia de forma explícita que tras paciente asedio le fue concedido 'conquistar Tiro', cumpliendo Ezequiel 28:7.",
        "source_alignment_reason": "Coincidencia exacta del topónimo canónico según PR42, p. 43, párr. 2."
      },
      {
        "id": "V14-R2-PR42-C19-006",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente indica que 'Egipto también cayó presa de sus ejércitos victoriosos; y mientras añadía una nación tras otra al reino babilónico, aumentaba su fama como el mayor gobernante de la época.'",
        "source_alignment_reason": "Identidad textual precisa con PR42, p. 43, párr. 2."
      },
      {
        "id": "V14-R2-PR42-C19-007",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto afirma que el monarca se vio tentado a apartarse 'de la senda de la humildad, la única que lleva a la verdadera grandeza'.",
        "source_alignment_reason": "Concordancia textual exacta con PR42, p. 43, párr. 3."
      },
      {
        "id": "V14-R2-PR42-C19-008",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La cita documenta que el rey pensó mucho 'en el fortalecimiento y embellecimiento de su capital', llegando Babilonia a ser llamada 'la ciudad codiciosa del oro' y 'que era alabada por toda la tierra'.",
        "source_alignment_reason": "Alineación literal estricta con PR42, p. 43, párr. 3."
      },
      {
        "id": "V14-R2-PR42-C19-009",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto establece que 'En su misericordia, Dios dió al rey otro sueño, para advertirle del riesgo que corría y del lazo que se le tendía para arruinarlo.'",
        "source_alignment_reason": "Correspondencia textual directa e inequívoca con PR42, p. 43, párr. 4."
      },
      {
        "id": "V14-R2-PR42-C19-010",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La descripción bíblica e histórica en la fuente especifica que el monarca vio 'un árbol gigantesco que crecía en medio de la tierra, cuya copa se elevaba hasta los cielos, y cuyas ramas se extendían hasta los fines de la tierra'.",
        "source_alignment_reason": "Coincidencia descriptiva exacta con PR42, p. 43, párr. 4."
      }
    ]
  },
  {
    "blind_batch_id": "blind-08466df2b6e39d9be7e0",
    "chapter_reference": "PR43-C20",
    "reviews": [
      {
        "id": "V14-R2-PR43-C20-001",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente señala expresamente que 'Admitido en su juventud a compartir la autoridad real, Belsasar se gloriaba en su poder, y ensalzó su corazón contra el Dios del cielo.'",
        "source_alignment_reason": "Correspondencia textual directa con PR43, p. 47, párr. 2."
      },
      {
        "id": "V14-R2-PR43-C20-002",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto canónico indica que el monarca permitió que 'el amor por los placeres y la glorificación propia borrasen las lecciones que nunca debiera haber olvidado'.",
        "source_alignment_reason": "Alineación literal inequívoca con PR43, p. 47, párr. 2."
      },
      {
        "id": "V14-R2-PR43-C20-003",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente señala que Belsasar 'Malgastó las oportunidades que se le habían concedido misericordiosamente, y no aprovechó los medios que tenía a su alcance para conocer mejor la verdad.'",
        "source_alignment_reason": "Cita textual idéntica a PR43, p. 47, párr. 2."
      },
      {
        "id": "V14-R2-PR43-C20-004",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El registro histórico afirma textualmente: 'Babilonia fué sitiada por Ciro, sobrino de Darío el Medo y general de los ejércitos combinados de los medos y persas.'",
        "source_alignment_reason": "Correspondencia fidedigna con PR43, p. 47, párr. 3."
      },
      {
        "id": "V14-R2-PR43-C20-005",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto enumera con precisión los cuatro elementos: 'con sus macizas murallas y sus puertas de bronce, protegida por el río Eufrates, y abastecida con abundantes provisiones'.",
        "source_alignment_reason": "Coincidencia integral con PR43, p. 47, párr. 3."
      },
      {
        "id": "V14-R2-PR43-C20-006",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente indica con claridad meridiana el propósito del rey: 'El rey quería probar que nada era demasiado sagrado para sus manos.'",
        "source_alignment_reason": "Correspondencia textual idéntica con PR43, p. 47, párr. 5."
      },
      {
        "id": "V14-R2-PR43-C20-007",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto afirma que 'un Testigo celestial presenciaba su desenfreno idólatra; pero un Vigía divino, aunque no reconocido, miraba la escena de profanación y oía la alegría sacrílega.'",
        "source_alignment_reason": "Alineación canónica exacta con PR43, p. 47, párr. 6."
      },
      {
        "id": "V14-R2-PR43-C20-008",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La narración describe el suceso: 'apareció una mano sin sangre y trazó en las paredes del palacio, con caracteres que resplandecían como fuego, palabras que, aunque desconocidas para la vasta muchedumbre, eran un presagio de condenación para el rey y sus huéspedes, ahora atormentados por su conciencia.'",
        "source_alignment_reason": "Identidad textual completa con PR43, p. 48, párr. 1."
      },
      {
        "id": "V14-R2-PR43-C20-009",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto declara escueta y categóricamente que 'En vano trató el rey de leer las letras ardientes.'",
        "source_alignment_reason": "Coincidencia textual directa con PR43, p. 48, párr. 4."
      },
      {
        "id": "V14-R2-PR43-C20-010",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente detalla la reacción interior de la concurrencia: 'Como en visión panorámica desfilaron ante sus ojos los actos de su vida impía; les pareció estar emplazados ante el tribunal del Dios eterno, cuyo poder acababan de desafiar.'",
        "source_alignment_reason": "Cita canónica fiel de PR43, p. 48, párr. 2."
      }
    ]
  },
  {
    "blind_batch_id": "blind-85dc7ae503c00ee0be21",
    "chapter_reference": "PR44-C20",
    "reviews": [
      {
        "id": "V14-R2-PR44-C20-001",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto declara que tras asumir el trono, Darío 'procedió inmediatamente a reorganizar el gobierno'.",
        "source_alignment_reason": "Alineación textual explícita con PR44, p. 55, párr. 1."
      },
      {
        "id": "V14-R2-PR44-C20-002",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El motivo canónico textual del fracaso de sus adversarios fue 'porque él era fiel, y ningún vicio ni falta fué en él hallado'.",
        "source_alignment_reason": "Cita bíblica y canónica directa de PR44, p. 55, párr. 2."
      },
      {
        "id": "V14-R2-PR44-C20-003",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Los conspiradores reconocieron obligados: '«No hallaremos contra este Daniel ocasión alguna, si no la hallamos contra él en la ley de su Dios.»'.",
        "source_alignment_reason": "Coincidencia literal exacta con PR44, p. 55, párr. 3."
      },
      {
        "id": "V14-R2-PR44-C20-004",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente señala la comprensión del rey: 'Vió que no era el celo por la gloria ni el honor del rey, sino los celos contra Daniel, lo que había motivado aquella propuesta de promulgar un decreto real.'",
        "source_alignment_reason": "Identidad textual completa con PR44, p. 56, párr. 6."
      },
      {
        "id": "V14-R2-PR44-C20-005",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto describe la fidelidad del profeta: 'Cumplía con calma sus deberes como presidente de los príncipes; y a la hora de la oración entraba en su cámara, y con las ventanas abiertas hacia Jerusalén, según su costumbre, ofrecía su petición al Dios del cielo.'",
        "source_alignment_reason": "Correspondencia textual fidedigna con PR44, p. 55, párr. 7."
      },
      {
        "id": "V14-R2-PR44-C20-006",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La fuente formula el principio ético y espiritual fundamental: 'Así declaró el profeta con osadía serena y humilde que ninguna potencia terrenal tiene derecho a interponerse entre el alma y Dios.'",
        "source_alignment_reason": "Coincidencia exacta con PR44, p. 56, párr. 2."
      },
      {
        "id": "V14-R2-PR44-C20-007",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El marco legal medo-persa establecía que: 'Aunque promulgado con precipitación, el decreto era inalterable y debía cumplirse.'",
        "source_alignment_reason": "Cita canónica precisa de PR44, p. 56, párr. 6."
      },
      {
        "id": "V14-R2-PR44-C20-008",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La ejecución de la sentencia se describe textualmente: '«Entonces el rey mandó, y trajeron a Daniel, y echáronle en el foso de los leones.»'.",
        "source_alignment_reason": "Alineación literal con PR44, p. 56, párr. 7."
      },
      {
        "id": "V14-R2-PR44-C20-009",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "El texto explica el propósito providencial: 'para recalcar tanto más la liberación de su siervo y para que la derrota de los enemigos de la verdad y de la justicia fuese más completa'.",
        "source_alignment_reason": "Concordancia textual exacta con PR44, p. 56, párr. 8."
      },
      {
        "id": "V14-R2-PR44-C20-010",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "La conclusión del episodio registra el milagro: '«fué Daniel sacado del foso, y ninguna lesión se halló en él, porque creyó en su Dios.»'.",
        "source_alignment_reason": "Identidad canónica textual estricta con PR44, p. 57, párr. 3."
      }
    ]
  }
]

for p in packets_data:
    p_id = p["blind_batch_id"]
    payload = {
        "schema_version": "competitive-v13-review/v1",
        "blind_batch_id": p_id,
        "reviewer": {
            "id": "arbitro-ciego-subagent-7",
            "conversation_id": "4f5354f0-59a8-456f-9166-795286c4a88b",
            "model": "gemini-3.7-flash"
        },
        "reviewed_at": "2026-09-01T05:13:42Z",
        "total_reviewed": len(p["reviews"]),
        "verdict_counts": {
            "approved": sum(1 for r in p["reviews"] if r["decision"] == "approved"),
            "rewrite": sum(1 for r in p["reviews"] if r["decision"] == "rewrite"),
            "rejected": sum(1 for r in p["reviews"] if r["decision"] == "rejected")
        },
        "decisions": p["reviews"]
    }
    rf = reviews_dir / f"{p_id}.json"
    rf.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved review for {p_id} ({p['chapter_reference']})")
