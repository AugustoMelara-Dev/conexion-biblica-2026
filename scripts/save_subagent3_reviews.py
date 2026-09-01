import json, pathlib
ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

packets_data = [
  {
    "blind_batch_id": "blind-209710f8811eb0f3b6a6",
    "cluster_id": "DAN3-C21",
    "reviews": [
      {
        "id": "V14-R2-DAN3-C21-001",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:30 afirma textualmente: «Entonces el rey engrandeció a Sadrac, Mesac y Abed-nego en la provincia de Babilonia», descartando cargos en Media, templos idólatras o retornos a Jerusalén.",
        "source_alignment_reason": "Correspondencia unívoca y exacta con Daniel 3:30 sobre el engrandecimiento administrativo de los tres hebreos en Babilonia."
      },
      {
        "id": "V14-R2-DAN3-C21-002",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:1 registra con precisión métrica y geográfica: «cuya altura era de sesenta codos y la anchura de seis codos; la levantó en el campo de Dura, en la provincia de Babilonia».",
        "source_alignment_reason": "Alineación literal con Daniel 3:1 en cuanto a las medidas (60x6 codos) y ubicación (campo de Dura)."
      },
      {
        "id": "V14-R2-DAN3-C21-003",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:12 expone la triple acusación de los caldeos: no respetar al rey, no servir a sus dioses y no adorar la estatua de oro levantada.",
        "source_alignment_reason": "Reproducción fiel de la denuncia formal registrada en Daniel 3:12."
      },
      {
        "id": "V14-R2-DAN3-C21-004",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:15 documenta el desafío desafiante del monarca: «¿y qué dios será el que os libre de mis manos?».",
        "source_alignment_reason": "Concordancia directa y textual con la pregunta retórica de desafío regio en Daniel 3:15."
      },
      {
        "id": "V14-R2-DAN3-C21-005",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:19 especifica que Nabucodonosor «se llenó de ira, cambió el aspecto de su rostro... y ordenó que el horno se calentara siete veces más de lo acostumbrado».",
        "source_alignment_reason": "Coincidencia exacta con la reacción física y el mandato de aumento séptuplo de temperatura en Daniel 3:19."
      },
      {
        "id": "V14-R2-DAN3-C21-006",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:24 relata que el rey se espantó, se levantó apresuradamente e interrogó a sus consejeros: «¿No echaron a tres hombres atados dentro del fuego?».",
        "source_alignment_reason": "Alineación estricta con la reacción de asombro y la pregunta de verificación formulada a los consejeros en Daniel 3:24."
      },
      {
        "id": "V14-R2-DAN3-C21-007",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:25 declara la visión del rey: «yo veo cuatro hombres sueltos, que se pasean en medio del fuego sin sufrir ningún daño; y el aspecto del cuarto es semejante a un hijo de los dioses».",
        "source_alignment_reason": "Correspondencia total con la declaración presencial de Nabucodonosor en Daniel 3:25."
      },
      {
        "id": "V14-R2-DAN3-C21-008",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:3 enumera taxativamente los ocho cargos oficiales: «sátrapas, magistrados, capitanes, oidores, tesoreros, consejeros, jueces y todos los gobernadores de las provincias».",
        "source_alignment_reason": "Enumeración fidedigna y exhaustiva de las clases burocráticas convocadas según Daniel 3:3."
      },
      {
        "id": "V14-R2-DAN3-C21-009",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:8 detalla que «algunos hombres caldeos vinieron y acusaron maliciosamente a los judíos».",
        "source_alignment_reason": "Coincidencia plena con los actores caldeos y el dolo de la acusación según Daniel 3:8."
      },
      {
        "id": "V14-R2-DAN3-C21-010",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 3:13 describe que el rey «dijo con ira y con enojo que trajeran a Sadrac, Mesac y Abed-nego. Al instante fueron traídos delante del rey».",
        "source_alignment_reason": "Alineación textual completa con los afectos regios y la inmediatez procesal de la comparecencia en Daniel 3:13."
      }
    ]
  },
  {
    "blind_batch_id": "blind-b0caecfab34d7d22543c",
    "cluster_id": "DAN4-C16",
    "reviews": [
      {
        "id": "V14-R2-DAN4-C16-001",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:2 formula literalmente el mandato testimonial: «Conviene que yo declare las señales y milagros que el Dios Altísimo ha hecho conmigo».",
        "source_alignment_reason": "Alineación literal con la declaración testimonial de apertura regia en Daniel 4:2."
      },
      {
        "id": "V14-R2-DAN4-C16-002",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:4 establece la condición previa del monarca: «Yo, Nabucodonosor, estaba tranquilo en mi casa, floreciente en mi palacio».",
        "source_alignment_reason": "Correspondencia exacta con los términos de reposo doméstico y florecimiento palaciego de Daniel 4:4."
      },
      {
        "id": "V14-R2-DAN4-C16-003",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:5 documenta: «Tuve un sueño que me espantó; tendido en la cama, las imaginaciones y visiones de mi cabeza me turbaron».",
        "source_alignment_reason": "Coincidencia precisa con la doble turbación mental e imaginativa descrita en Daniel 4:5."
      },
      {
        "id": "V14-R2-DAN4-C16-004",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:6 señala la orden real: «mandé que vinieran ante mí todos los sabios de Babilonia para que me dieran la interpretación del sueño».",
        "source_alignment_reason": "Concordancia directa con la convocatoria general a la sabiduría babilónica según Daniel 4:6."
      },
      {
        "id": "V14-R2-DAN4-C16-005",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:7 especifica la presencia de «magos, astrólogos, caldeos y adivinos» y su absoluta incapacidad interpretativa ante el relato real.",
        "source_alignment_reason": "Alineación textual con los cuatro gremios de sabios convocados y su fracaso hermenéutico en Daniel 4:7."
      },
      {
        "id": "V14-R2-DAN4-C16-006",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:10 expone la primera imagen del sueño: «Me parecía ver en medio de la tierra un árbol cuya altura era grande».",
        "source_alignment_reason": "Correspondencia directa con la visión onírica central del árbol en medio de la tierra de Daniel 4:10."
      },
      {
        "id": "V14-R2-DAN4-C16-007",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:11 detalla las etapas de magnitud: «Crecía este árbol, y se hacía fuerte, y su copa llegaba hasta el cielo y se le alcanzaba a ver desde todos los confines de la tierra».",
        "source_alignment_reason": "Coincidencia exacta con la descripción del desarrollo y visibilidad cósmica del árbol en Daniel 4:11."
      },
      {
        "id": "V14-R2-DAN4-C16-008",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:13 identifica con precisión al mensajero divino: «un vigilante y santo descendía del cielo».",
        "source_alignment_reason": "Alineación unívoca con la designación angélica de «vigilante y santo» de Daniel 4:13."
      },
      {
        "id": "V14-R2-DAN4-C16-009",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:14 recoge la orden celestial: «Derribad el árbol y cortad sus ramas, quitadle el follaje y dispersad su fruto; váyanse las bestias que están debajo de él, y las aves de sus ramas».",
        "source_alignment_reason": "Concordancia íntegra con las cláusulas de corte, despojo y dispersión animal de Daniel 4:14."
      },
      {
        "id": "V14-R2-DAN4-C16-010",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:16 sentencia la mutación ontológica y el plazo: «Su corazón de hombre sea cambiado y le sea dado corazón de bestia, y pasen sobre él siete tiempos».",
        "source_alignment_reason": "Correspondencia estricta con el cambio de corazón a bestia y el lapso de siete tiempos de Daniel 4:16."
      }
    ]
  },
  {
    "blind_batch_id": "blind-f8dd22b2c772c127ca2c",
    "cluster_id": "DAN4-C21",
    "reviews": [
      {
        "id": "V14-R2-DAN4-C21-001",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:20 reitera las características del árbol: «que crecía y se hacía fuerte, cuya copa llegaba hasta el cielo, que se veía desde todos los confines de la tierra».",
        "source_alignment_reason": "Coincidencia exacta con la recapitulación profética que Daniel hace del árbol en Daniel 4:20."
      },
      {
        "id": "V14-R2-DAN4-C21-002",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:24 declara la autoridad de la sentencia: «ésta es la interpretación, oh rey, y la sentencia del Altísimo, que ha venido sobre mi señor, el rey».",
        "source_alignment_reason": "Alineación directa con el origen soberano de la sentencia divina atribuida al Altísimo en Daniel 4:24."
      },
      {
        "id": "V14-R2-DAN4-C21-003",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:25 detalla las cuatro condiciones de degradación: expulsión humana, morada con bestias, pasto como bueyes y rocío del cielo, durante siete tiempos.",
        "source_alignment_reason": "Correspondencia total y exacta con el contenido de juicio y aprendizaje pedagógico de Daniel 4:25."
      },
      {
        "id": "V14-R2-DAN4-C21-004",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:28 atestigua el cumplimiento histórico: «Todo esto vino sobre el rey Nabucodonosor».",
        "source_alignment_reason": "Concordancia unívoca con el cumplimiento sobre la persona del rey Nabucodonosor en Daniel 4:28."
      },
      {
        "id": "V14-R2-DAN4-C21-005",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:29 establece el tiempo y el lugar: «Al cabo de doce meses, paseando por el palacio real de Babilonia».",
        "source_alignment_reason": "Alineación literal con el lapso de doce meses y el escenario del palacio real de Babilonia en Daniel 4:29."
      },
      {
        "id": "V14-R2-DAN4-C21-006",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:1 abre la carta del rey: «Nabucodonosor, rey, a todos los pueblos, naciones y lenguas que moran en toda la tierra: Paz os sea multiplicada».",
        "source_alignment_reason": "Coincidencia exacta con el encabezado y el saludo universal de paz de la epístola regia en Daniel 4:1."
      },
      {
        "id": "V14-R2-DAN4-C21-007",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:3 registra la doxología: «¡Cuán grandes son sus señales y cuán potentes sus maravillas! Su reino, reino sempiterno; su señorío, de generación en generación».",
        "source_alignment_reason": "Concordancia directa con la alabanza imperial a la soberanía eterna de Dios en Daniel 4:3."
      },
      {
        "id": "V14-R2-DAN4-C21-008",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:7 documenta: «Y vinieron magos, astrólogos, caldeos y adivinos, y les conté el sueño, pero no me pudieron dar su interpretación».",
        "source_alignment_reason": "Alineación fidedigna con la lista de sabios y su fracaso hermenéutico en Daniel 4:7."
      },
      {
        "id": "V14-R2-DAN4-C21-009",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:8 identifica a Daniel: «cuyo nombre es Beltsasar, como el nombre de mi dios, y en quien mora el espíritu de los dioses santos».",
        "source_alignment_reason": "Correspondencia estricta con el testimonio nominal y la investidura espiritual de Daniel en Daniel 4:8."
      },
      {
        "id": "V14-R2-DAN4-C21-010",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 4:12 detalla la frondosidad y provisión: «Su follaje era hermoso, su fruto abundante y había en él alimento para todos. Debajo de él, a su sombra, se ponían las bestias del campo, en sus ramas anidaban las aves del cielo...».",
        "source_alignment_reason": "Coincidencia íntegra con la descripción ecológica del árbol de Daniel 4:12."
      }
    ]
  },
  {
    "blind_batch_id": "blind-ad299049c304cc817777",
    "cluster_id": "DAN5-C17",
    "reviews": [
      {
        "id": "V14-R2-DAN5-C17-001",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:1 afirma: «El rey Belsasar hizo un gran banquete a mil de sus príncipes, y en presencia de los mil bebía vino».",
        "source_alignment_reason": "Correspondencia total con el rey Belsasar, el banquete a mil príncipes y la libación de vino en Daniel 5:1."
      },
      {
        "id": "V14-R2-DAN5-C17-002",
        "adjudicated_option": 1,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:3 registra la profanación: «trajeron los vasos de oro... y bebieron de ellos el rey y sus príncipes, sus mujeres y sus concubinas».",
        "source_alignment_reason": "Coincidencia exacta con los participantes del sacrilegio con los vasos del templo en Daniel 5:3."
      },
      {
        "id": "V14-R2-DAN5-C17-003",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:9 detalla la conmoción cortesana: «Entonces el rey Belsasar se turbó sobremanera y palideció, y sus príncipes estaban perplejos».",
        "source_alignment_reason": "Alineación unívoca con la palidez y turbación del rey y la perplejidad de los príncipes en Daniel 5:9."
      },
      {
        "id": "V14-R2-DAN5-C17-004",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:13 consigna la pregunta del rey: «¿Eres tú aquel Daniel de los hijos de la cautividad de Judá, que mi padre trajo de Judea?».",
        "source_alignment_reason": "Concordancia literal con el interrogatorio de procedencia formulado por Belsasar en Daniel 5:13."
      },
      {
        "id": "V14-R2-DAN5-C17-005",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:17 recoge la digna respuesta del profeta: «Tus dones sean para ti; da tus recompensas a otros. Leeré la escritura al rey y le daré la interpretación».",
        "source_alignment_reason": "Alineación fiel con el rechazo a las dádivas reales y el compromiso profético de interpretación en Daniel 5:17."
      },
      {
        "id": "V14-R2-DAN5-C17-006",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:18 enumera las cuatro prerrogativas otorgadas: «el reino, la grandeza, la gloria y la majestad».",
        "source_alignment_reason": "Coincidencia exacta y cuádruple con los dones concedidos por Dios a Nabucodonosor en Daniel 5:18."
      },
      {
        "id": "V14-R2-DAN5-C17-007",
        "adjudicated_option": 0,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:24 revela el origen de la mano: «Por eso, de su presencia envió él la mano que trazó esta escritura».",
        "source_alignment_reason": "Concordancia directa con la procedencia divina («de su presencia») de la mano enigmática en Daniel 5:24."
      },
      {
        "id": "V14-R2-DAN5-C17-008",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:26 define el significado de la primera palabra: «“Mene”: Contó Dios tu reino y le ha puesto fin».",
        "source_alignment_reason": "Alineación literal con la interpretación profética de MENE en Daniel 5:26."
      },
      {
        "id": "V14-R2-DAN5-C17-009",
        "adjudicated_option": 3,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:27 sentencia el significado de TEKEL: «“Tekel”: Pesado has sido en balanza y hallado falto».",
        "source_alignment_reason": "Coincidencia estricta con la interpretación y juicio de peso moral de TEKEL en Daniel 5:27."
      },
      {
        "id": "V14-R2-DAN5-C17-010",
        "adjudicated_option": 2,
        "second_defensible_option": False,
        "decision": "approved",
        "rationale": "Daniel 5:25 reproduce el texto original en la pared: «“Mene, Mene, Tekel, Uparsin.”».",
        "source_alignment_reason": "Reproducción exacta de la inscripción cuádruple trazada en la pared según Daniel 5:25."
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
            "id": "arbitro-ciego-subagent-3",
            "conversation_id": "cb4f5f86-7161-4127-93e5-ab4fa3f8afe8",
            "model": "gemini-3.7-flash"
        },
        "reviewed_at": "2026-09-01T05:13:50Z",
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
    print(f"Saved review for {p_id} ({p['cluster_id']})")
