import json
import os

# Load dossier batch 2
with open('.work/competitive-v16/piloto-r3-v2/dossiers/pilot2_batch_2.json', 'r', encoding='utf-8') as f:
    dossier_data = json.load(f)

dossiers = dossier_data['dossiers']
print(f"Loaded {len(dossiers)} dossiers.")

# Define the 30 crafted items
items_data = [
    # Item 1: Index 31 (V16-R3-PILOT2-PR39-031) - PR39, p. 28, p. 3 - cross_passage_fact_pairing - HARD - noise=False - target pos: 0
    {
        "pilot_index": 31,
        "id": "V16-R3-PILOT2-PR39-031",
        "question_id": "V16-R3-PILOT2-PR39-031",
        "fact_id": "PR39-P028-P003-S005-F02",
        "primary_fact_id": "PR39-P028-P003-S005-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P003-S005",
        "source_ref": "PR39, p. 28, párrafo 3",
        "primary_source_ref": "PR39, p. 28, párrafo 3",
        "source_quote": "Ningún poder ni influencia podía apartarlos de los principios que habían aprendido temprano en la vida por un estudio de la palabra y de las obras de Dios.",
        "primary_source_quote": "Ningún poder ni influencia podía apartarlos de los principios que habían aprendido temprano en la vida por un estudio de la palabra y de las obras de Dios.",
        "cognitive_operation": "cross_passage_fact_pairing",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "¿A qué atribuye Elena G. de White en Profetas y Reyes la inquebrantable firmeza de los jóvenes hebreos, que impidió que ningún poder o influencia los apartara de sus principios en Babilonia?",
        "correct_option": 0,
        "options": [
            "A la formación adquirida temprano en la vida mediante el estudio constante de la palabra y de las obras de Dios.",
            "A la exhibición formal de los vasos sagrados del templo que demostraba la supremacía del culto sobre los caldeos.",
            "Al rechazo de todo contacto con las naciones paganas para impedir la difusión del conocimiento divino en el exilio.",
            "Al temor provocado por las humillaciones del cautiverio al presenciar la caída de Jerusalén ante los babilónicos."
        ],
        "explanation": "Profetas y Reyes (p. 28, párr. 3) declara explícitamente que «ningún poder ni influencia podía apartarlos de los principios que habían aprendido temprano en la vida por un estudio de la palabra y de las obras de Dios».",
        "why_distractors_fail": {
            "A la exhibición formal de los vasos sagrados del templo que demostraba la supremacía del culto sobre los caldeos.": "La exhibición de los vasos del templo en Babilonia era usada jactanciosamente por los captores caldeos como supuesta prueba de su superioridad (PR39 p. 27), no como causa de la firmeza hebrea.",
            "Al rechazo de todo contacto con las naciones paganas para impedir la difusión del conocimiento divino en el exilio.": "El propósito divino era precisamente que los fieles cautivos dieran a las naciones paganas las bendiciones del conocimiento de Jehová como sus representantes (PR39 p. 27).",
            "Al temor provocado por las humillaciones del cautiverio al presenciar la caída de Jerusalén ante los babilónicos.": "Elena White no atribuye su fidelidad al temor o al trauma del asedio, sino a principios firmes como el acero cultivados en su juventud mediante el estudio sagrado."
        },
        "distractor_provenance": {
            "A la exhibición formal de los vasos sagrados del templo que demostraba la supremacía del culto sobre los caldeos.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Al rechazo de todo contacto con las naciones paganas para impedir la difusión del conocimiento divino en el exilio.": "PR39-P027-P001-S002-F02 (PR39, p. 27, párrafo 1)",
            "Al temor provocado por las humillaciones del cautiverio al presenciar la caída de Jerusalén ante los babilónicos.": "PR39-P027-P002-S002-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 2: Index 32 (V16-R3-PILOT2-PR39-032) - PR39, p. 28, p. 4 - chronological_event_sequence - EXPERT - noise=True - target pos: 1
    {
        "pilot_index": 32,
        "id": "V16-R3-PILOT2-PR39-032",
        "question_id": "V16-R3-PILOT2-PR39-032",
        "fact_id": "PR39-P028-P004-S001-F02",
        "primary_fact_id": "PR39-P028-P004-S001-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P004-S001",
        "source_ref": "PR39, p. 28, párrafo 4",
        "primary_source_ref": "PR39, p. 28, párrafo 4",
        "source_quote": "Si Daniel lo hubiese deseado, podría haber hallado en las circunstancias que le rodeaban una excusa plausible por apartarse de hábitos estrictamente temperantes.",
        "primary_source_quote": "Si Daniel lo hubiese deseado, podría haber hallado en las circunstancias que le rodeaban una excusa plausible por apartarse de hábitos estrictamente temperantes.",
        "cognitive_operation": "chronological_event_sequence",
        "translation_noise": True,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "En la secuencia de acontecimientos afrontados por Daniel al principiar el cautiverio en Babilonia, ¿cuál progresión describe con exactitud el dilema moral registrado en Profetas y Reyes?",
        "correct_option": 1,
        "options": [
            "Traslado inicial a la corte, aceptación provisional de la comida del rey y posterior arrepentimiento al ver los vasos sagrados.",
            "Deportación en el inicio del cautiverio, confrontación con excusas plausibles para transigir y resolución de mantenerse fiel.",
            "Asignación del vino real, claudicación temporal ante las presiones del monarca y retorno tardío al estudio de la palabra divina.",
            "Llegada al palacio caldeo, adopción de hábitos babilónicos y súbita renuncia a los manjares tras ser amenazado con la muerte."
        ],
        "explanation": "Profetas y Reyes (p. 27-28) establece la secuencia: los jóvenes fueron llevados a Babilonia al principio del cautiverio, donde Daniel halló circunstancias que ofrecían excusas plausibles para apartarse de la temperancia, pero resolvió permanecer incondicionalmente fiel.",
        "why_distractors_fail": {
            "Traslado inicial a la corte, aceptación provisional de la comida del rey y posterior arrepentimiento al ver los vasos sagrados.": "Daniel nunca aceptó provisionalmente la comida del rey ni requirió un arrepentimiento posterior; rehusó contaminarse desde el principio.",
            "Asignación del vino real, claudicación temporal ante las presiones del monarca y retorno tardío al estudio de la palabra divina.": "No hubo claudicación temporal; Daniel no vaciló ni cedió a la presión de las circunstancias en ningún instante (PR39 p. 28).",
            "Llegada al palacio caldeo, adopción de hábitos babilónicos y súbita renuncia a los manjares tras ser amenazado con la muerte.": "Daniel no adoptó los hábitos babilónicos ni su resolución fue provocada por amenazas de muerte, sino por su fidelidad previa a Dios."
        },
        "distractor_provenance": {
            "Traslado inicial a la corte, aceptación provisional de la comida del rey y posterior arrepentimiento al ver los vasos sagrados.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Asignación del vino real, claudicación temporal ante las presiones del monarca y retorno tardío al estudio de la palabra divina.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "Llegada al palacio caldeo, adopción de hábitos babilónicos y súbita renuncia a los manjares tras ser amenazado con la muerte.": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 3: Index 33 (V16-R3-PILOT2-PR39-033) - PR39, p. 28, p. 4 - speaker_recipient_intermediary_attribution - HARD - noise=False - target pos: 2
    {
        "pilot_index": 33,
        "id": "V16-R3-PILOT2-PR39-033",
        "question_id": "V16-R3-PILOT2-PR39-033",
        "fact_id": "PR39-P028-P004-S002-F01",
        "primary_fact_id": "PR39-P028-P004-S002-F01",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P004-S002",
        "source_ref": "PR39, p. 28, párrafo 4",
        "primary_source_ref": "PR39, p. 28, párrafo 4",
        "source_quote": "Podría haber argüído que, en vista de que dependía del favor del rey y estaba sometido a su poder, no le quedaba otro remedio que comer de la comida del rey y beber de su vino; porque si seguía la enseñanza divina no podía menos que ofender al rey y probablemente perdería su puesto y la vida, mientras que si despreciaba el mandamiento del Señor, conservaría el favor del rey y se aseguraría ventajas intelectuales y perspectivas halagüeñas en este mundo.",
        "primary_source_quote": "Podría haber argüído que, en vista de que dependía del favor del rey y estaba sometido a su poder, no le quedaba otro remedio que comer de la comida del rey y beber de su vino; porque si seguía la enseñanza divina no podía menos que ofender al rey y probablemente perdería su puesto y la vida, mientras que si despreciaba el mandamiento del Señor, conservaría el favor del rey y se aseguraría ventajas intelectuales y perspectivas halagüeñas en este mundo.",
        "cognitive_operation": "speaker_recipient_intermediary_attribution",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "Al analizar las tentaciones de Daniel en Babilonia, ¿qué razonamiento egoísta señala Elena G. de White (PR39) que el joven hebreo podría haber argüido para justificar el consumo de la comida y el vino reales?",
        "correct_option": 2,
        "options": [
            "Que debía transigir con los idólatras para proteger los vasos del santuario que se hallaban en el templo pagano de Babilonia.",
            "Que su deber como representante divino le exigía adoptar las costumbres de los vencedores para obtener puestos de autoridad.",
            "Que ofendería al monarca y arriesgaría la vida si seguía la enseñanza divina, mientras que ceder le aseguraba ventajas mundanas.",
            "Que la humillación del pueblo de Israel demostraba la supremacía de los dioses caldeos y anulaba los mandamientos de Jehová."
        ],
        "explanation": "PR39 (p. 28, párr. 4) expone que Daniel podría haber argüido que al depender del rey perdería su puesto y la vida si seguía la enseñanza divina, mientras que al despreciar el mandamiento conservaría el favor del rey y ventajas mundanas.",
        "why_distractors_fail": {
            "Que debía transigir con los idólatras para proteger los vasos del santuario que se hallaban en el templo pagano de Babilonia.": "Elena White no menciona una justificación basada en proteger los vasos sagrados, los cuales estaban bajo control babilónico (PR39 p. 27).",
            "Que su deber como representante divino le exigía adoptar las costumbres de los vencedores para obtener puestos de autoridad.": "El llamado de Dios era no transigir en caso alguno con los idólatras, no adoptar sus costumbres mundanas (PR39 p. 27).",
            "Que la humillación del pueblo de Israel demostraba la supremacía de los dioses caldeos y anulaba los mandamientos de Jehová.": "Esa era la jactancia de los caldeos vencedores (PR39 p. 27), no un argumento que Daniel hubiese considerado como excusa plausible."
        },
        "distractor_provenance": {
            "Que debía transigir con los idólatras para proteger los vasos del santuario que se hallaban en el templo pagano de Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Que su deber como representante divino le exigía adoptar las costumbres de los vencedores para obtener puestos de autoridad.": "PR39-P027-P001-S003-F01 (PR39, p. 27, párrafo 1)",
            "Que la humillación del pueblo de Israel demostraba la supremacía de los dioses caldeos y anulaba los mandamientos de Jehová.": "PR39-P027-P002-S002-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 4: Index 34 (V16-R3-PILOT2-PR39-034) - PR39, p. 28, p. 5 - vision_year_monarch_river_correlation - HARD - noise=False - target pos: 3
    {
        "pilot_index": 34,
        "id": "V16-R3-PILOT2-PR39-034",
        "question_id": "V16-R3-PILOT2-PR39-034",
        "fact_id": "PR39-P028-P005-S001-F02",
        "primary_fact_id": "PR39-P028-P005-S001-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P005-S001",
        "source_ref": "PR39, p. 28, párrafo 5",
        "primary_source_ref": "PR39, p. 28, párrafo 5",
        "source_quote": "Pero Daniel no vaciló.",
        "primary_source_quote": "Pero Daniel no vaciló.",
        "cognitive_operation": "vision_year_monarch_river_correlation",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En el marco histórico del inicio de los setenta años de cautiverio en Babilonia, ¿cómo contrasta Elena G. de White la actitud de Daniel frente a la imposición de los manjares reales?",
        "correct_option": 3,
        "options": [
            "Aceptó transigir inicialmente con la corte pagana para salvaguardar los vasos sagrados depositados en el templo de Babilonia.",
            "Postergó su decisión hasta consultar con los sacerdotes caldeos sobre la compatibilidad de los alimentos ofrecidos a dioses.",
            "Decidió someterse al régimen alimentario del monarca caldeo a fin de garantizar la preservación del remanente judío cautivo.",
            "Rehusó vacilar ante el poder caldeo y priorizó la aprobación divina por encima de su propia vida o del favor de Nabucodonosor."
        ],
        "explanation": "PR39 (p. 28, párr. 5) enfatiza contundentemente: «Pero Daniel no vaciló», prefiriendo la aprobación divina por encima de todo poder terrenal o de la vida misma.",
        "why_distractors_fail": {
            "Aceptó transigir inicialmente con la corte pagana para salvaguardar los vasos sagrados depositados en el templo de Babilonia.": "Daniel nunca transigió ni su conducta dependía de la suerte de los vasos sagrados en el templo babilónico (PR39 p. 27-28).",
            "Postergó su decisión hasta consultar con los sacerdotes caldeos sobre la compatibilidad de los alimentos ofrecidos a dioses.": "Daniel no vaciló ni buscó componendas con los sacerdotes caldeos; actuó guiado por principios inmutables ya asimilados.",
            "Decidió someterse al régimen alimentario del monarca caldeo a fin de garantizar la preservación del remanente judío cautivo.": "Daniel no se sometió al régimen real, sino que propuso firmemente en su corazón no contaminarse con la ración del rey."
        },
        "distractor_provenance": {
            "Aceptó transigir inicialmente con la corte pagana para salvaguardar los vasos sagrados depositados en el templo de Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Postergó su decisión hasta consultar con los sacerdotes caldeos sobre la compatibilidad de los alimentos ofrecidos a dioses.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "Decidió someterse al régimen alimentario del monarca caldeo a fin de garantizar la preservación del remanente judío cautivo.": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 5: Index 35 (V16-R3-PILOT2-PR39-035) - PR39, p. 28, p. 5 - biblical_text_vs_prophets_and_kings_contrast - EXPERT - noise=False - target pos: 0
    {
        "pilot_index": 35,
        "id": "V16-R3-PILOT2-PR39-035",
        "question_id": "V16-R3-PILOT2-PR39-035",
        "fact_id": "PR39-P028-P005-S002-F02",
        "primary_fact_id": "PR39-P028-P005-S002-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P005-S002",
        "source_ref": "PR39, p. 28, párrafo 5",
        "primary_source_ref": "PR39, p. 28, párrafo 5",
        "source_quote": "Apreciaba más la aprobación de Dios que el favor del mayor potentado de la tierra, aun más que la vida misma.",
        "primary_source_quote": "Apreciaba más la aprobación de Dios que el favor del mayor potentado de la tierra, aun más que la vida misma.",
        "cognitive_operation": "biblical_text_vs_prophets_and_kings_contrast",
        "translation_noise": False,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "A diferencia de la sobria descripción de Daniel 1:8, ¿qué revelación espiritual añade Elena G. de White en Profetas y Reyes respecto a la escala de valores que motivó la resolución de Daniel?",
        "correct_option": 0,
        "options": [
            "Subraya que el joven valoraba la aprobación de Dios por encima del favor del mayor potentado de la tierra y de la vida misma.",
            "Destaca que su móvil primordial era exhibir la superioridad física de los hebreos sobre los vencedores en la corte de Babilonia.",
            "Indica que procuraba evitar el castigo civil caldeo adaptándose exteriormente a las normas del palacio real de Nabucodonosor.",
            "Afirma que buscaba asegurar una posición encumbrada en el imperio para recuperar los vasos sagrados del templo de Jerusalén."
        ],
        "explanation": "Elena White amplía el relato bíblico explicando la motivación interior: Daniel «apreciaba más la aprobación de Dios que el favor del mayor potentado de la tierra, aun más que la vida misma» (PR39 p. 28, párr. 5).",
        "why_distractors_fail": {
            "Destaca que su móvil primordial era exhibir la superioridad física de los hebreos sobre los vencedores en la corte de Babilonia.": "La motivación no fue la vanidad ni una competencia física con los captores caldeos, sino la lealtad pura a Dios (PR39 p. 27-28).",
            "Indica que procuraba evitar el castigo civil caldeo adaptándose exteriormente a las normas del palacio real de Nabucodonosor.": "Elena White refuta expresamente cualquier conformidad externa hipócrita; los jóvenes no debían transigir en ningún caso (PR39 p. 27).",
            "Afirma que buscaba asegurar una posición encumbrada en el imperio para recuperar los vasos sagrados del templo de Jerusalén.": "Daniel no actuó por ambición política ni por planes humanos para recuperar los vasos del templo."
        },
        "distractor_provenance": {
            "Destaca que su móvil primordial era exhibir la superioridad física de los hebreos sobre los vencedores en la corte de Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Indica que procuraba evitar el castigo civil caldeo adaptándose exteriormente a las normas del palacio real de Nabucodonosor.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "Afirma que buscaba asegurar una posición encumbrada en el imperio para recuperar los vasos sagrados del templo de Jerusalén.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 6: Index 36 (V16-R3-PILOT2-PR39-036) - PR39, p. 28, p. 5 - cause_condition_consequence_chain - HARD - noise=False - target pos: 1
    {
        "pilot_index": 36,
        "id": "V16-R3-PILOT2-PR39-036",
        "question_id": "V16-R3-PILOT2-PR39-036",
        "fact_id": "PR39-P028-P005-S003-F01",
        "primary_fact_id": "PR39-P028-P005-S003-F01",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P005-S003",
        "source_ref": "PR39, p. 28, párrafo 5",
        "primary_source_ref": "PR39, p. 28, párrafo 5",
        "source_quote": "Resolvió permanecer firme en su integridad, cualesquiera fuesen los resultados.",
        "primary_source_quote": "Resolvió permanecer firme en su integridad, cualesquiera fuesen los resultados.",
        "cognitive_operation": "cause_condition_consequence_chain",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "Al describir la postura de Daniel frente a los requerimientos caldeos, ¿qué relación de causa, condición y consecuencia establece Elena G. de White en Profetas y Reyes (p. 28)?",
        "correct_option": 1,
        "options": [
            "La aflicción del cautiverio (causa) le condujo, siempre que el monarca lo exigiera (condición), a contemporizar con los usos de la corte (consecuencia).",
            "Su lealtad a Dios (causa) le impulsó, prescindiendo de los riesgos o resultados (condición), a mantenerse inquebrantable en su integridad (consecuencia).",
            "El anhelo de ventajas (causa) le motivó, bajo la promesa de altos cargos reales (condición), a postergar su fidelidad ante los vencedores (consecuencia).",
            "El temor a la muerte (causa) le indujo, si los vasos del templo peligraban (condición), a disimular sus principios en el palacio caldeo (consecuencia)."
        ],
        "explanation": "En PR39 (p. 28, párr. 5), la devoción a Dios llevó a Daniel a resolver permanecer inquebrantable en su integridad moral, prescindiendo de cuáles fuesen los resultados o consecuencias temporales.",
        "why_distractors_fail": {
            "La aflicción del cautiverio (causa) le condujo, siempre que el monarca lo exigiera (condición), a contemporizar con los usos de la corte (consecuencia).": "Daniel rehusó enérgicamente contemporizar con los usos idolátricos de la corte bajo cualquier circunstancia (PR39 p. 27).",
            "El anhelo de ventajas (causa) le motivó, bajo la promesa de altos cargos reales (condición), a postergar su fidelidad ante los vencedores (consecuencia).": "Elena White resalta que los patriotas hebreos eran hombres no corrompidos por el egoísmo y que no posponían su deber (PR39 p. 27).",
            "El temor a la muerte (causa) le indujo, si los vasos del templo peligraban (condición), a disimular sus principios en el palacio caldeo (consecuencia).": "Daniel consideraba un alto honor confesar el nombre del Dios viviente y honrar a Dios aun perdiéndolo todo (PR39 p. 27)."
        },
        "distractor_provenance": {
            "La aflicción del cautiverio (causa) le condujo, siempre que el monarca lo exigiera (condición), a contemporizar con los usos de la corte (consecuencia).": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "El anhelo de ventajas (causa) le motivó, bajo la promesa de altos cargos reales (condición), a postergar su fidelidad ante los vencedores (consecuencia).": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)",
            "El temor a la muerte (causa) le indujo, si los vasos del templo peligraban (condición), a disimular sus principios en el palacio caldeo (consecuencia).": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 7: Index 37 (V16-R3-PILOT2-PR39-037) - PR39, p. 28, p. 5 - cross_passage_fact_pairing - HARD - noise=False - target pos: 2
    {
        "pilot_index": 37,
        "id": "V16-R3-PILOT2-PR39-037",
        "question_id": "V16-R3-PILOT2-PR39-037",
        "fact_id": "PR39-P028-P005-S004-F01",
        "primary_fact_id": "PR39-P028-P005-S004-F01",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P005-S004",
        "source_ref": "PR39, p. 28, párrafo 5",
        "primary_source_ref": "PR39, p. 28, párrafo 5",
        "source_quote": "“Propuso en su corazón de no contaminarse en la ración de la comida del rey, ni en el vino de su beber.",
        "primary_source_quote": "“Propuso en su corazón de no contaminarse en la ración de la comida del rey, ni en el vino de su beber.",
        "cognitive_operation": "cross_passage_fact_pairing",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En la narración de Profetas y Reyes (p. 28), ¿con qué principio rector del carácter de los patriotas hebreos en el cautiverio se empareja la decisión de Daniel de no contaminarse con la ración ni el vino del rey?",
        "correct_option": 2,
        "options": [
            "Con el afán de demostrar a los vencedores que la ciencia hebrea era superior a los cultos rendidos a los dioses paganos de Babilonia.",
            "Con la exigencia sacerdotal de custodiar los vasos de la casa de Dios que yacían cautivos en el templo de las divinidades caldeas.",
            "Con la determinación inquebrantable de no transigir en caso alguno con los idólatras, honrando a Dios por encima del egoísmo personal.",
            "Con la estrategia diplomática de acatar externamente las normas del palacio imperial para asegurar la pronta liberación de Judá."
        ],
        "explanation": "Elena White empareja la resolución de Daniel con el carácter de los patriotas cristianos cautivos en Babilonia, quienes no debían en caso alguno transigir con los idólatras ni dejarse corromper por el egoísmo (PR39 p. 27-28).",
        "why_distractors_fail": {
            "Con el afán de demostrar a los vencedores que la ciencia hebrea era superior a los cultos rendidos a los dioses paganos de Babilonia.": "Su propósito no era competir por prestigio intelectual o religioso con los caldeos, sino obedecer estrictamente los requerimientos divinos (PR39 p. 27).",
            "Con la exigencia sacerdotal de custodiar los vasos de la casa de Dios que yacían cautivos en el templo de las divinidades caldeas.": "Los jóvenes no tenían a su cargo el rescate o custodia de los vasos sagrados capturados (PR39 p. 27).",
            "Con la estrategia diplomática de acatar externamente las normas del palacio imperial para asegurar la pronta liberación de Judá.": "Elena White condena la transigencia externa y exalta la confesión íntegra de la fe como alto honor (PR39 p. 27)."
        },
        "distractor_provenance": {
            "Con el afán de demostrar a los vencedores que la ciencia hebrea era superior a los cultos rendidos a los dioses paganos de Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Con la exigencia sacerdotal de custodiar los vasos de la casa de Dios que yacían cautivos en el templo de las divinidades caldeas.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Con la estrategia diplomática de acatar externamente las normas del palacio imperial para asegurar la pronta liberación de Judá.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 8: Index 38 (V16-R3-PILOT2-PR39-038) - PR39, p. 28, p. 5 - chronological_event_sequence - HARD - noise=False - target pos: 3
    {
        "pilot_index": 38,
        "id": "V16-R3-PILOT2-PR39-038",
        "question_id": "V16-R3-PILOT2-PR39-038",
        "fact_id": "PR39-P028-P005-S005-F01",
        "primary_fact_id": "PR39-P028-P005-S005-F01",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P005-S005",
        "source_ref": "PR39, p. 28, párrafo 5",
        "primary_source_ref": "PR39, p. 28, párrafo 5",
        "source_quote": "Esta resolución fué apoyada por sus tres compañeros.",
        "primary_source_quote": "Esta resolución fué apoyada por sus tres compañeros.",
        "cognitive_operation": "chronological_event_sequence",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "¿Cuál es el orden cronológico exacto en que se consolidó la decisión de fidelidad alimentaria entre los jóvenes hebreos, según Profetas y Reyes?",
        "correct_option": 3,
        "options": [
            "Los cuatro jóvenes deliberaron con los caldeos, Aspenaz aprobó el plan de prueba y Daniel formalizó después la promesa de no contaminarse en palacio.",
            "Los tres compañeros propusieron la abstinencia, Daniel asumió la vocería del grupo y el jefe de eunucos rechazó de inmediato la solicitud hebrea.",
            "Daniel obtuvo el consentimiento de Aspenaz, persuadió después a sus tres compañeros y selló finalmente su voto de fidelidad ante la corte pagana.",
            "Daniel concibió la resolución en su corazón, sus tres compañeros la respaldaron unánimemente y luego presentaron la petición ante el oficial caldeo."
        ],
        "explanation": "PR39 (p. 28, párr. 5-7) presenta la secuencia: Daniel primero propuso en su corazón no contaminarse, esta resolución fue luego apoyada por sus tres compañeros, y posteriormente presentaron la petición respetuosa ante el oficial.",
        "why_distractors_fail": {
            "Los cuatro jóvenes deliberaron con los caldeos, Aspenaz aprobó el plan de prueba y Daniel formalizó después la promesa de no contaminarse en palacio.": "La resolución no nació de un debate con los caldeos, sino de una convicción interior previa de Daniel respaldada por sus compañeros.",
            "Los tres compañeros propusieron la abstinencia, Daniel asumió la vocería del grupo y el jefe de eunucos rechazó de inmediato la solicitud hebrea.": "Fue Daniel quien tomó la iniciativa original de proponer en su corazón la abstinencia, apoyado luego por los otros tres jóvenes.",
            "Daniel obtuvo el consentimiento de Aspenaz, persuadió después a sus tres compañeros y selló finalmente su voto de fidelidad ante la corte pagana.": "Daniel no buscó primero la anuencia del funcionario pagano; la convicción espiritual precedió a cualquier gestión formal."
        },
        "distractor_provenance": {
            "Los cuatro jóvenes deliberaron con los caldeos, Aspenaz aprobó el plan de prueba y Daniel formalizó después la promesa de no contaminarse en palacio.": "PR39-P027-P001-S002-F02 (PR39, p. 27, párrafo 1)",
            "Los tres compañeros propusieron la abstinencia, Daniel asumió la vocería del grupo y el jefe de eunucos rechazó de inmediato la solicitud hebrea.": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)",
            "Daniel obtuvo el consentimiento de Aspenaz, persuadió después a sus tres compañeros y selló finalmente su voto de fidelidad ante la corte pagana.": "PR39-P027-P002-S003-F02 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 9: Index 39 (V16-R3-PILOT2-PR39-039) - PR39, p. 28, p. 6 - speaker_recipient_intermediary_attribution - EXPERT - noise=True - target pos: 0
    {
        "pilot_index": 39,
        "id": "V16-R3-PILOT2-PR39-039",
        "question_id": "V16-R3-PILOT2-PR39-039",
        "fact_id": "PR39-P028-P006-S001-F02",
        "primary_fact_id": "PR39-P028-P006-S001-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P006-S001",
        "source_ref": "PR39, p. 28, párrafo 6",
        "primary_source_ref": "PR39, p. 28, párrafo 6",
        "source_quote": "Al llegar a esta decisión, los jóvenes hebreos no obraron presuntuosamente, sino confiando firmemente en Dios.",
        "primary_source_quote": "Al llegar a esta decisión, los jóvenes hebreos no obraron presuntuosamente, sino confiando firmemente en Dios.",
        "cognitive_operation": "speaker_recipient_intermediary_attribution",
        "translation_noise": True,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "Al caracterizar el ánimo con que los jóvenes hebreos asumieron su abstención de los manjares reales, ¿a qué disposición interna atribuye Elena G. de White su proceder ante las autoridades caldeas?",
        "correct_option": 0,
        "options": [
            "No obraron con presunción ni arrogancia desafiante, mas descansó su resolución en una firme e inquebrantable confianza en Dios.",
            "Guiólos un afán de superioridad intelectual, procurando humillar a los caldeos que custodiaban los vasos sagrados en Babilonia.",
            "Pretendieron singularizarse ante la corte pagana, desafiando abiertamente los decretos reales para apresurar su repatriación.",
            "Procedieron movidos por la rebeldía política, buscando quebrantar la disciplina impuesta por el rey caldeo en el cautiverio."
        ],
        "explanation": "Elena White destaca explícitamente que «al llegar a esta decisión, los jóvenes hebreos no obraron presuntuosamente, sino confiando firmemente en Dios» (PR39 p. 28, párr. 6).",
        "why_distractors_fail": {
            "Guiólos un afán de superioridad intelectual, procurando humillar a los caldeos que custodiaban los vasos sagrados en Babilonia.": "Elena White aclara que no actuaron por orgullo ni para humillar a los captores caldeos (PR39 p. 27-28).",
            "Pretendieron singularizarse ante la corte pagana, desafiando abiertamente los decretos reales para apresurar su repatriación.": "PR39 (p. 28, párr. 6) refuta textualmente que buscaran singularizarse por capricho o rebeldía.",
            "Procedieron movidos por la rebeldía política, buscando quebrantar la disciplina impuesta por el rey caldeo en el cautiverio.": "Eran patriotas cristianos respetuosos y leales, cuyo móvil era honrar a Dios y no promover sedición política (PR39 p. 27)."
        },
        "distractor_provenance": {
            "Guiólos un afán de superioridad intelectual, procurando humillar a los caldeos que custodiaban los vasos sagrados en Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Pretendieron singularizarse ante la corte pagana, desafiando abiertamente los decretos reales para apresurar su repatriación.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "Procedieron movidos por la rebeldía política, buscando quebrantar la disciplina impuesta por el rey caldeo en el cautiverio.": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 10: Index 40 (V16-R3-PILOT2-PR39-040) - PR39, p. 28, p. 6 - vision_year_monarch_river_correlation - HARD - noise=False - target pos: 1
    {
        "pilot_index": 40,
        "id": "V16-R3-PILOT2-PR39-040",
        "question_id": "V16-R3-PILOT2-PR39-040",
        "fact_id": "PR39-P028-P006-S002-F02",
        "primary_fact_id": "PR39-P028-P006-S002-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P006-S002",
        "source_ref": "PR39, p. 28, párrafo 6",
        "primary_source_ref": "PR39, p. 28, párrafo 6",
        "source_quote": "No decidieron singularizarse, aunque preferirían eso antes que deshonrar a Dios.",
        "primary_source_quote": "No decidieron singularizarse, aunque preferirían eso antes que deshonrar a Dios.",
        "cognitive_operation": "vision_year_monarch_river_correlation",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "Dentro del ambiente cortesano de Babilonia, ¿cómo define Elena G. de White en Profetas y Reyes la actitud de los jóvenes hebreos frente al riesgo de singularizarse?",
        "correct_option": 1,
        "options": [
            "Procuraron distinguirse intencionalmente para exhibir ante los sacerdotes caldeos la pureza exclusiva del linaje de Judá.",
            "No buscaron singularizarse por capricho o vanagloria, aunque estaban dispuestos a ser diferentes antes que deshonrar a Dios.",
            "Decidieron disimular sus convicciones para no llamar la atención ni poner en riesgo los vasos sagrados del templo hebreo.",
            "Intentaron aislarse de la corte imperial con el fin de evitar cualquier interacción con los consejeros del monarca pagano."
        ],
        "explanation": "PR39 (p. 28, párr. 6) afirma con precisión: «No decidieron singularizarse, aunque preferirían eso antes que deshonrar a Dios». Su meta era honrar al Señor sin buscar notoriedad artificial.",
        "why_distractors_fail": {
            "Procuraron distinguirse intencionalmente para exhibir ante los sacerdotes caldeos la pureza exclusiva del linaje de Judá.": "Elena White niega que buscaran distinguirse o hacer ostentación de su linaje frente a los caldeos (PR39 p. 27-28).",
            "Decidieron disimular sus convicciones para no llamar la atención ni poner en riesgo los vasos sagrados del templo hebreo.": "No disimularon sus convicciones; consideraban un alto honor el nombre de adoradores del Dios viviente y no transigieron (PR39 p. 27).",
            "Intentaron aislarse de la corte imperial con el fin de evitar cualquier interacción con los consejeros del monarca pagano.": "Fueron preparados para servir en el palacio real como representantes de Dios entre las naciones paganas (PR39 p. 27)."
        },
        "distractor_provenance": {
            "Procuraron distinguirse intencionalmente para exhibir ante los sacerdotes caldeos la pureza exclusiva del linaje de Judá.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Decidieron disimular sus convicciones para no llamar la atención ni poner en riesgo los vasos sagrados del templo hebreo.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "Intentaron aislarse de la corte imperial con el fin de evitar cualquier interacción con los consejeros del monarca pagano.": "PR39-P027-P001-S002-F02 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 11: Index 41 (V16-R3-PILOT2-PR39-041) - PR39, p. 28, p. 6 - biblical_text_vs_prophets_and_kings_contrast - EXPERT - noise=False - target pos: 2
    {
        "pilot_index": 41,
        "id": "V16-R3-PILOT2-PR39-041",
        "question_id": "V16-R3-PILOT2-PR39-041",
        "fact_id": "PR39-P028-P006-S003-F02",
        "primary_fact_id": "PR39-P028-P006-S003-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P006-S003",
        "source_ref": "PR39, p. 28, párrafo 6",
        "primary_source_ref": "PR39, p. 28, párrafo 6",
        "source_quote": "Si hubiesen transigido con el mal en este caso al ceder a la presión de las circunstancias, su desvío de los buenos principios habría debilitado su sentido de lo recto y su aborrecimiento por lo malo.",
        "primary_source_quote": "Si hubiesen transigido con el mal en este caso al ceder a la presión de las circunstancias, su desvío de los buenos principios habría debilitado su sentido de lo recto y su aborrecimiento por lo malo.",
        "cognitive_operation": "biblical_text_vs_prophets_and_kings_contrast",
        "translation_noise": False,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "¿Qué análisis ético-espiritual exclusivo aporta Elena G. de White en Profetas y Reyes (p. 28) sobre el impacto que una sola transigencia habría causado en el carácter de los jóvenes hebreos?",
        "correct_option": 2,
        "options": [
            "Sostiene que transigir con los manjares reales les habría impedido asimilar la literatura y los conocimientos de los caldeos.",
            "Afirma que su capitulación alimentaria habría provocado la profanación definitiva de los vasos del templo puestos en Babilonia.",
            "Advierte que ceder a la presión de las circunstancias habría debilitado su sentido de lo recto y su aborrecimiento por el mal.",
            "Señala que el monarca imperial los habría destituido de inmediato por considerarlos indignos del servicio en la corte real."
        ],
        "explanation": "Elena White profundiza en la psicología moral de la tentación: «Si hubiesen transigido con el mal en este caso al ceder a la presión de las circunstancias, su desvío de los buenos principios habría debilitado su sentido de lo recto y su aborrecimiento por lo malo» (PR39 p. 28, párr. 6).",
        "why_distractors_fail": {
            "Sostiene que transigir con los manjares reales les habría impedido asimilar la literatura y los conocimientos de los caldeos.": "El texto no enfoca la asimilación académica secular, sino el debilitamiento moral y la pérdida de sensibilidad espiritual.",
            "Afirma que su capitulación alimentaria habría provocado la profanación definitiva de los vasos del templo puestos en Babilonia.": "La suerte de los vasos sagrados no dependía de la dieta de los jóvenes; estos ya estaban en el templo babilónico (PR39 p. 27).",
            "Señala que el monarca imperial los habría destituido de inmediato por considerarlos indignos del servicio en la corte real.": "Por el contrario, el rey les ofrecía honores y ventajas si comían de su mesa (PR39 p. 28)."
        },
        "distractor_provenance": {
            "Sostiene que transigir con los manjares reales les habría impedido asimilar la literatura y los conocimientos de los caldeos.": "PR39-P027-P001-S002-F02 (PR39, p. 27, párrafo 1)",
            "Afirma que su capitulación alimentaria habría provocado la profanación definitiva de los vasos del templo puestos en Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Señala que el monarca imperial los habría destituido de inmediato por considerarlos indignos del servicio en la corte real.": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 12: Index 42 (V16-R3-PILOT2-PR39-042) - PR39, p. 28, p. 6 - cause_condition_consequence_chain - HARD - noise=False - target pos: 3
    {
        "pilot_index": 42,
        "id": "V16-R3-PILOT2-PR39-042",
        "question_id": "V16-R3-PILOT2-PR39-042",
        "fact_id": "PR39-P028-P006-S004-F01",
        "primary_fact_id": "PR39-P028-P006-S004-F01",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P006-S004",
        "source_ref": "PR39, p. 28, párrafo 6",
        "primary_source_ref": "PR39, p. 28, párrafo 6",
        "source_quote": "El primer paso en la dirección errónea habría conducido a otros pasos tales, hasta que, cortada su relación con el Cielo, se vieran arrastrados por la tentación.",
        "primary_source_quote": "El primer paso en la dirección errónea habría conducido a otros pasos tales, hasta que, cortada su relación con el Cielo, se vieran arrastrados por la tentación.",
        "cognitive_operation": "cause_condition_consequence_chain",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "¿Qué cadena de causa, condición y consecuencia describe Elena G. de White en Profetas y Reyes si los jóvenes hebreos hubiesen dado un primer paso en la dirección errónea?",
        "correct_option": 3,
        "options": [
            "Rechazar la comida real (causa) provocaría el enojo del príncipe de los eunucos (condición), acarreando la inmediata ejecución de todos los cautivos hebreos en la corte (consecuencia).",
            "Desobedecer al rey caldeo (causa) anularía la influencia del conocimiento de Dios (condición), provocando la entrega de los vasos sagrados a los sacerdotes de los ídolos (consecuencia).",
            "Aceptar el vino pagano (causa) despertaría la jactancia de los vencedores caldeos (condición), forzando a los jóvenes a renunciar públicamente a su fe en el Dios viviente (consecuencia).",
            "Dar un primer paso erróneo (causa) desencadenaría sucesivas claudicaciones hasta cortar la comunión con el Cielo (condición), siendo arrastrados por la tentación (consecuencia)."
        ],
        "explanation": "PR39 (p. 28, párr. 6) describe esta cadena: «El primer paso en la dirección errónea habría conducido a otros pasos tales, hasta que, cortada su relación con el Cielo, se vieran arrastrados por la tentación».",
        "why_distractors_fail": {
            "Rechazar la comida real (causa) provocaría el enojo del príncipe de los eunucos (condición), acarreando la inmediata ejecución de todos los cautivos hebreos en la corte (consecuencia).": "El rechazo respetuoso no produjo la ejecución de los cautivos, sino que abrió paso a la prueba supervisada por Melsar.",
            "Desobedecer al rey caldeo (causa) anularía la influencia del conocimiento de Dios (condición), provocando la entrega de los vasos sagrados a los sacerdotes de los ídolos (consecuencia).": "La obediencia fiel fue el medio exacto por el cual Dios dio testimonio de su supremacía a Babilonia (PR39 p. 27).",
            "Aceptar el vino pagano (causa) despertaría la jactancia de los vencedores caldeos (condición), forzando a los jóvenes a renunciar públicamente a su fe en el Dios viviente (consecuencia).": "El texto enfoca el proceso interno acumulativo de degradación moral y ruptura de la comunión con Dios."
        },
        "distractor_provenance": {
            "Rechazar la comida real (causa) provocaría el enojo del príncipe de los eunucos (condición), acarreando la inmediata ejecución de todos los cautivos hebreos en la corte (consecuencia).": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)",
            "Desobedecer al rey caldeo (causa) anularía la influencia del conocimiento de Dios (condición), provocando la entrega de los vasos sagrados a los sacerdotes de los ídolos (consecuencia).": "PR39-P027-P002-S002-F01 (PR39, p. 27, párrafo 2)",
            "Aceptar el vino pagano (causa) despertaría la jactancia de los vencedores caldeos (condición), forzando a los jóvenes a renunciar públicamente a su fe en el Dios viviente (consecuencia).": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 13: Index 43 (V16-R3-PILOT2-PR39-043) - PR39, p. 28, p. 7 - cross_passage_fact_pairing - HARD - noise=False - target pos: 0
    {
        "pilot_index": 43,
        "id": "V16-R3-PILOT2-PR39-043",
        "question_id": "V16-R3-PILOT2-PR39-043",
        "fact_id": "PR39-P028-P007-S001-F02",
        "primary_fact_id": "PR39-P028-P007-S001-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P007-S001",
        "source_ref": "PR39, p. 28, párrafo 7",
        "primary_source_ref": "PR39, p. 28, párrafo 7",
        "source_quote": "“Puso Dios a Daniel en gracia y en buena voluntad con el príncipe de los eunucos,” y la petición de que se le permitiera no contaminarse fué recibida con respeto.",
        "primary_source_quote": "“Puso Dios a Daniel en gracia y en buena voluntad con el príncipe de los eunucos,” y la petición de que se le permitiera no contaminarse fué recibida con respeto.",
        "cognitive_operation": "cross_passage_fact_pairing",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En la narrativa de Profetas y Reyes (p. 28), ¿cómo se empareja la intervención de Dios en favor de Daniel con la respuesta del príncipe de los eunucos ante la solicitud del profeta?",
        "correct_option": 0,
        "options": [
            "Dios concedió a Daniel gracia y benevolencia ante el jefe de los eunucos, logrando que su petición de no contaminarse fuera recibida con respeto.",
            "Dios intimidó al príncipe de los eunucos con señales sobrenaturales, forzándolo a ocultar ante Nabucodonosor la dieta abstinente de los hebreos.",
            "El oficial caldeo rechazó con desprecio la solicitud de Daniel, pero Dios intervino retirando los vasos sagrados del templo pagano de Babilonia.",
            "El príncipe de los eunucos aceptó la petición por conveniencia política, pues buscaba granjearse el favor de los patriotas fieles del cautiverio."
        ],
        "explanation": "PR39 (p. 28, párr. 7) cita Daniel 1:9 y añade que, como resultado directo de la gracia divina, «la petición de que se le permitiera no contaminarse fué recibida con respeto».",
        "why_distractors_fail": {
            "Dios intimidó al príncipe de los eunucos con señales sobrenaturales, forzándolo a ocultar ante Nabucodonosor la dieta abstinente de los hebreos.": "Dios no empleó intimidación ni señales de juicio contra el oficial, sino que dispuso su corazón con gracia y buena voluntad.",
            "El oficial caldeo rechazó con desprecio la solicitud de Daniel, pero Dios intervino retirando los vasos sagrados del templo pagano de Babilonia.": "La petición no fue rechazada con desprecio sino acogida con respeto, y los vasos permanecieron en Babilonia (PR39 p. 27).",
            "El príncipe de los eunucos aceptó la petición por conveniencia política, pues buscaba granjearse el favor de los patriotas fieles del cautiverio.": "El texto sagrado e inspirado atribuye la receptividad del príncipe a la gracia divina y no a cálculo político humano."
        },
        "distractor_provenance": {
            "Dios intimidó al príncipe de los eunucos con señales sobrenaturales, forzándolo a ocultar ante Nabucodonosor la dieta abstinente de los hebreos.": "PR39-P027-P002-S002-F01 (PR39, p. 27, párrafo 2)",
            "El oficial caldeo rechazó con desprecio la solicitud de Daniel, pero Dios intervino retirando los vasos sagrados del templo pagano de Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "El príncipe de los eunucos aceptó la petición por conveniencia política, pues buscaba granjearse el favor de los patriotas fieles del cautiverio.": "PR39-P027-P001-S001-F01 (PR39, p. 27, párrafo 1)"
        }
    },

    # Item 14: Index 44 (V16-R3-PILOT2-PR39-044) - PR39, p. 28, p. 7 - chronological_event_sequence - HARD - noise=False - target pos: 1
    {
        "pilot_index": 44,
        "id": "V16-R3-PILOT2-PR39-044",
        "question_id": "V16-R3-PILOT2-PR39-044",
        "fact_id": "PR39-P028-P007-S002-F01",
        "primary_fact_id": "PR39-P028-P007-S002-F01",
        "chapter": "PR39",
        "source_unit_id": "PR39-P028-P007-S002",
        "source_ref": "PR39, p. 28, párrafo 7",
        "primary_source_ref": "PR39, p. 28, párrafo 7",
        "source_quote": "Sin embargo, el príncipe vacilaba antes de acceder.",
        "primary_source_quote": "Sin embargo, el príncipe vacilaba antes de acceder.",
        "cognitive_operation": "chronological_event_sequence",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "De acuerdo con Profetas y Reyes, ¿en qué momento cronológico de las negociaciones alimentarias se produjo la vacilación del príncipe de los eunucos?",
        "correct_option": 1,
        "options": [
            "Al concluir los diez días de prueba vegetal, vaciló antes de examinar el rostro de los hebreos frente a los otros muchachos.",
            "Tras recibir con respeto la petición de Daniel, vaciló antes de acceder por temer las represalias del monarca sobre su cabeza.",
            "Al iniciarse los setenta años de cautiverio, vaciló antes de permitir que los vasos sagrados entraran al templo babilónico.",
            "Tras la comparecencia final ante Nabucodonosor, vaciló antes de proclamar a los jóvenes diez veces superiores a los sabios."
        ],
        "explanation": "PR39 (p. 28, párr. 7) y Daniel 1:9-10 muestran que inmediatamente después de recibir la petición con respeto, el príncipe vaciló antes de otorgar el permiso debido al temor a que el rey castigara su cabeza.",
        "why_distractors_fail": {
            "Al concluir los diez días de prueba vegetal, vaciló antes de examinar el rostro de los hebreos frente a los otros muchachos.": "Al cabo de los diez días no hubo vacilación; los resultados fueron evidentes de inmediato y Melsar continuó dándoles legumbres (Dan 1:15-16).",
            "Al iniciarse los setenta años de cautiverio, vaciló antes de permitir que los vasos sagrados entraran al templo babilónico.": "El príncipe de los eunucos no tuvo relación con la entrada de los vasos sagrados al templo de los ídolos caldeos (PR39 p. 27).",
            "Tras la comparecencia final ante Nabucodonosor, vaciló antes de proclamar a los jóvenes diez veces superiores a los sabios.": "La proclamación de superioridad fue hecha por el propio rey Nabucodonosor al término de los tres años de educación."
        },
        "distractor_provenance": {
            "Al concluir los diez días de prueba vegetal, vaciló antes de examinar el rostro de los hebreos frente a los otros muchachos.": "PR39-P027-P001-S006-F01 (PR39, p. 27, párrafo 1)",
            "Al iniciarse los setenta años de cautiverio, vaciló antes de permitir que los vasos sagrados entraran al templo babilónico.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)",
            "Tras la comparecencia final ante Nabucodonosor, vaciló antes de proclamar a los jóvenes diez veces superiores a los sabios.": "PR39-P027-P002-S002-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 15: Index 45 (V16-R3-PILOT2-PR39-045) - PR39, p. 29, p. 1 - speaker_recipient_intermediary_attribution - EXPERT - noise=True - target pos: 2
    {
        "pilot_index": 45,
        "id": "V16-R3-PILOT2-PR39-045",
        "question_id": "V16-R3-PILOT2-PR39-045",
        "fact_id": "PR39-P029-P001-S001-F02",
        "primary_fact_id": "PR39-P029-P001-S001-F02",
        "chapter": "PR39",
        "source_unit_id": "PR39-P029-P001-S001",
        "source_ref": "PR39, p. 29, párrafo 1",
        "primary_source_ref": "PR39, p. 29, párrafo 1",
        "source_quote": "Explicó a Daniel: “Tengo temor de mi señor el rey, que señaló vuestra comida y vuestra bebida; pues luego que él habrá visto vuestros rostros más tristes que los de los muchachos que son semejantes a vosotros, condenaréis para con el rey mi cabeza.”",
        "primary_source_quote": "Explicó a Daniel: “Tengo temor de mi señor el rey, que señaló vuestra comida y vuestra bebida; pues luego que él habrá visto vuestros rostros más tristes que los de los muchachos que son semejantes a vosotros, condenaréis para con el rey mi cabeza.”",
        "cognitive_operation": "speaker_recipient_intermediary_attribution",
        "translation_noise": True,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "En la interlocución sostenida en la corte caldea, ¿quién expone a Daniel el temor de que rostros demudados acarreen la pena capital sobre su propia persona, y cuál es la razón esgrimida para tal recelo?",
        "correct_option": 2,
        "options": [
            "El mayordomo Melsar a Daniel, temiendo que el monarca notara el desacato al culto oficial y ejecutara a los cuatro hebreos.",
            "El rey Nabucodonosor a Aspenaz, temiendo que los jóvenes enfermaran y deshonraran el entrenamiento impartido en la corte.",
            "El jefe de los eunucos a Daniel, temiendo que el rey viera sus rostros más tristes que los de sus pares y condenara su cabeza.",
            "El sacerdote caldeo a los príncipes, temiendo que la abstinencia hebrea desafiara la supremacía de los dioses de Babilonia."
        ],
        "explanation": "PR39 (p. 29, párr. 1) cita las palabras textuales del príncipe de los eunucos a Daniel, expresando su temor a que el rey viera sus rostros más tristes que los de los otros muchachos y condenara su cabeza.",
        "why_distractors_fail": {
            "El mayordomo Melsar a Daniel, temiendo que el monarca notara el desacato al culto oficial y ejecutara a los cuatro hebreos.": "Fue el príncipe de los eunucos (Aspenaz) quien pronunció esta advertencia inicial a Daniel, no el mayordomo Melsar.",
            "El rey Nabucodonosor a Aspenaz, temiendo que los jóvenes enfermaran y deshonraran el entrenamiento impartido en la corte.": "El rey fijó la porción, pero el diálogo de temor hacia Daniel provino del jefe de los eunucos que temía la ira real.",
            "El sacerdote caldeo a los príncipes, temiendo que la abstinencia hebrea desafiara la supremacía de los dioses de Babilonia.": "No hubo intervención de un sacerdote caldeo en este diálogo sobre la porción y la preservación de la vida del oficial."
        },
        "distractor_provenance": {
            "El mayordomo Melsar a Daniel, temiendo que el monarca notara el desacato al culto oficial y ejecutara a los cuatro hebreos.": "PR39-P027-P001-S004-F01 (PR39, p. 27, párrafo 1)",
            "El rey Nabucodonosor a Aspenaz, temiendo que los jóvenes enfermaran y deshonraran el entrenamiento impartido en la corte.": "PR39-P027-P001-S002-F02 (PR39, p. 27, párrafo 1)",
            "El sacerdote caldeo a los príncipes, temiendo que la abstinencia hebrea desafiara la supremacía de los dioses de Babilonia.": "PR39-P027-P002-S001-F01 (PR39, p. 27, párrafo 2)"
        }
    },

    # Item 16: Index 46 (V16-R3-PILOT2-DAN1-046) - Daniel 1:13 - vision_year_monarch_river_correlation - HARD - noise=False - target pos: 3
    {
        "pilot_index": 46,
        "id": "V16-R3-PILOT2-DAN1-046",
        "question_id": "V16-R3-PILOT2-DAN1-046",
        "fact_id": "DAN1-V013-F01",
        "primary_fact_id": "DAN1-V013-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V013",
        "source_ref": "Daniel 1:13",
        "primary_source_ref": "Daniel 1:13",
        "source_quote": "Compara luego nuestros rostros con los rostros de los muchachos que comen de la porción de la comida del rey, y haz después con tus siervos según veas.",
        "primary_source_quote": "Compara luego nuestros rostros con los rostros de los muchachos que comen de la porción de la comida del rey, y haz después con tus siervos según veas.",
        "cognitive_operation": "vision_year_monarch_river_correlation",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En el contexto de la corte de Babilonia bajo el reinado de Nabucodonosor, ¿qué criterio de evaluación propuso Daniel a su guardián para resolver el dilema de la alimentación real?",
        "correct_option": 3,
        "options": [
            "Consultar a los sabios y astrólogos caldeos para que juzgaran si la abstinencia respetaba los tres años fijados para su educación.",
            "Solicitar una audiencia directa ante Nabucodonosor para justificar su negativa con base en las leyes sagradas de Judá en Sinar.",
            "Someterse a un examen de ciencias babilónicas antes de decidir si continuaban consumiendo las legumbres y el agua en el palacio.",
            "Comparar sus rostros con los de los muchachos que comían de la porción del rey, y actuar luego según lo observado tras diez días."
        ],
        "explanation": "Daniel 1:13 registra la propuesta empírica y respetuosa de Daniel: «Compara luego nuestros rostros con los rostros de los muchachos que comen de la porción de la comida del rey, y haz después con tus siervos según veas».",
        "why_distractors_fail": {
            "Consultar a los sabios y astrólogos caldeos para que juzgaran si la abstinencia respetaba los tres años fijados para su educación.": "Daniel no propuso someter la decisión al arbitrio de los sabios caldeos ni alterar el plazo general de tres años (Dan 1:4-5).",
            "Solicitar una audiencia directa ante Nabucodonosor para justificar su negativa con base en las leyes sagradas de Judá en Sinar.": "Daniel trató la prueba de manera discreta y práctica directamente con el guardián Melsar (Dan 1:11-13).",
            "Someterse a un examen de ciencias babilónicas antes de decidir si continuaban consumiendo las legumbres y el agua en el palacio.": "El criterio propuesto fue una comparación visual directa del semblante y vigor físico tras diez días, no un examen académico."
        },
        "distractor_provenance": {
            "Consultar a los sabios y astrólogos caldeos para que juzgaran si la abstinencia respetaba los tres años fijados para su educación.": "DAN1-V005-F01 (Daniel 1:5)",
            "Solicitar una audiencia directa ante Nabucodonosor para justificar su negativa con base en las leyes sagradas de Judá en Sinar.": "DAN1-V002-F01 (Daniel 1:2)",
            "Someterse a un examen de ciencias babilónicas antes de decidir si continuaban consumiendo las legumbres y el agua en el palacio.": "DAN1-V004-F01 (Daniel 1:4)"
        }
    },

    # Item 17: Index 47 (V16-R3-PILOT2-DAN1-047) - Daniel 1:1 - biblical_text_vs_prophets_and_kings_contrast - EXPERT - noise=False - target pos: 0
    {
        "pilot_index": 47,
        "id": "V16-R3-PILOT2-DAN1-047",
        "question_id": "V16-R3-PILOT2-DAN1-047",
        "fact_id": "DAN1-V001-F04",
        "primary_fact_id": "DAN1-V001-F04",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V001",
        "source_ref": "Daniel 1:1",
        "primary_source_ref": "Daniel 1:1",
        "source_quote": "En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió.",
        "primary_source_quote": "En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió.",
        "cognitive_operation": "biblical_text_vs_prophets_and_kings_contrast",
        "translation_noise": False,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "¿Qué sincronismo monárquico e histórico exacto establece el texto bíblico de Daniel 1:1 para el asedio de Jerusalén por parte de Nabucodonosor?",
        "correct_option": 0,
        "options": [
            "Ocurrió en el tercer año del reinado de Joacim, rey de Judá, cuando el monarca de Babilonia marchó hacia Jerusalén y la sitió.",
            "Tuvo lugar en el primer año del reinado de Ciro de Persia, al decretar la repatriación de los cautivos y de los vasos divinos.",
            "Aconteció en el undécimo año de Sedequías de Judá, cuando las tropas caldeas quemaron el santuario e incendiaron la ciudad.",
            "Se produjo al cabo de los tres años de instrucción palaciega señalados para los jóvenes de la nobleza hebrea en Babilonia."
        ],
        "explanation": "Daniel 1:1 data el evento con precisión bíblica: «En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió».",
        "why_distractors_fail": {
            "Tuvo lugar en el primer año del reinado de Ciro de Persia, al decretar la repatriación de los cautivos y de los vasos divinos.": "El decreto de Ciro corresponde al fin del cautiverio babilónico (Esdras 1), no al asedio inicial de Daniel 1:1.",
            "Aconteció en el undécimo año de Sedequías de Judá, cuando las tropas caldeas quemaron el santuario e incendiaron la ciudad.": "El undécimo año de Sedequías marca la destrucción final de Jerusalén en la tercera deportación (2 Reyes 25), no el asedio del tercer año de Joacim.",
            "Se produjo al cabo de los tres años de instrucción palaciega señalados para los jóvenes de la nobleza hebrea en Babilonia.": "Los tres años de instrucción (Dan 1:5) ocurrieron con posterioridad al asedio y deportación."
        },
        "distractor_provenance": {
            "Tuvo lugar en el primer año del reinado de Ciro de Persia, al decretar la repatriación de los cautivos y de los vasos divinos.": "DAN1-V002-F01 (Daniel 1:2)",
            "Aconteció en el undécimo año de Sedequías de Judá, cuando las tropas caldeas quemaron el santuario e incendiaron la ciudad.": "DAN1-V001-F04 (Daniel 1:1)",
            "Se produjo al cabo de los tres años de instrucción palaciega señalados para los jóvenes de la nobleza hebrea en Babilonia.": "DAN1-V005-F01 (Daniel 1:5)"
        }
    },

    # Item 18: Index 48 (V16-R3-PILOT2-DAN1-048) - Daniel 1:2 - cause_condition_consequence_chain - HARD - noise=False - target pos: 1
    {
        "pilot_index": 48,
        "id": "V16-R3-PILOT2-DAN1-048",
        "question_id": "V16-R3-PILOT2-DAN1-048",
        "fact_id": "DAN1-V002-F01",
        "primary_fact_id": "DAN1-V002-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V002",
        "source_ref": "Daniel 1:2",
        "primary_source_ref": "Daniel 1:2",
        "source_quote": "El Señor entregó en sus manos a Joacim, rey de Judá, y parte de los utensilios de la casa de Dios; los trajo a tierra de Sinar, a la casa de su dios, y colocó los utensilios en la casa del tesoro de su dios.",
        "primary_source_quote": "El Señor entregó en sus manos a Joacim, rey de Judá, y parte de los utensilios de la casa de Dios; los trajo a tierra de Sinar, a la casa de su dios, y colocó los utensilios en la casa del tesoro de su dios.",
        "cognitive_operation": "cause_condition_consequence_chain",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "Según Daniel 1:2, ¿cuál es la relación de causa divina y consecuencia histórica respecto a la caída de Judá y el destino de los utensilios del templo?",
        "correct_option": 1,
        "options": [
            "La superioridad militar de Nabucodonosor (causa) forzó a Aspenaz a reclutar jóvenes del linaje real para educarlos tres años en la corte de Babilonia (consecuencia).",
            "La soberana entrega de Joacim por parte del Señor (causa) resultó en el traslado de parte de los vasos sagrados al tesoro del dios caldeo en Sinar (consecuencia).",
            "La rebelión de los príncipes de Judá (causa) provocó que el jefe de los eunucos cambiara los nombres hebreos por apelativos dedicados a dioses paganos (consecuencia).",
            "La orden alimentaria del rey caldeo (causa) obligó a Daniel y a sus compañeros a solicitar una prueba de diez días a base de legumbres y de agua pura (consecuencia)."
        ],
        "explanation": "Daniel 1:2 enfatiza la soberanía de Dios: «El Señor entregó en sus manos a Joacim, rey de Judá, y parte de los utensilios de la casa de Dios», los cuales Nabucodonosor llevó a tierra de Sinar y colocó en la casa del tesoro de su dios.",
        "why_distractors_fail": {
            "La superioridad militar de Nabucodonosor (causa) forzó a Aspenaz a reclutar jóvenes del linaje real para educarlos tres años en la corte de Babilonia (consecuencia).": "El texto sagrado no atribuye la victoria a la fuerza militar caldea, sino a que el Señor soberanamente entregó a Joacim en sus manos.",
            "La rebelión de los príncipes de Judá (causa) provocó que el jefe de los eunucos cambiara los nombres hebreos por apelativos dedicados a dioses paganos (consecuencia).": "El cambio de nombres (Dan 1:7) fue parte de la aculturación imperial y no la consecuencia directa declarada en Daniel 1:2.",
            "La orden alimentaria del rey caldeo (causa) obligó a Daniel y a sus compañeros a solicitar una prueba de diez días a base de legumbres y de agua pura (consecuencia).": "La prueba de diez días (Dan 1:12) corresponde al dilema de fidelidad personal posterior."
        },
        "distractor_provenance": {
            "La superioridad militar de Nabucodonosor (causa) forzó a Aspenaz a reclutar jóvenes del linaje real para educarlos tres años en la corte de Babilonia (consecuencia).": "DAN1-V003-F01 (Daniel 1:3)",
            "La rebelión de los príncipes de Judá (causa) provocó que el jefe de los eunucos cambiara los nombres hebreos por apelativos dedicados a dioses paganos (consecuencia).": "DAN1-V007-F01 (Daniel 1:7)",
            "La orden alimentaria del rey caldeo (causa) obligó a Daniel y a sus compañeros a solicitar una prueba de diez días a base de legumbres y de agua pura (consecuencia).": "DAN1-V008-F02 (Daniel 1:8)"
        }
    },

    # Item 19: Index 49 (V16-R3-PILOT2-DAN1-049) - Daniel 1:3 - cross_passage_fact_pairing - HARD - noise=False - target pos: 2
    {
        "pilot_index": 49,
        "id": "V16-R3-PILOT2-DAN1-049",
        "question_id": "V16-R3-PILOT2-DAN1-049",
        "fact_id": "DAN1-V003-F01",
        "primary_fact_id": "DAN1-V003-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V003",
        "source_ref": "Daniel 1:3",
        "primary_source_ref": "Daniel 1:3",
        "source_quote": "Y dijo el rey a Aspenaz, jefe de sus eunucos, que trajera de los hijos de Israel, del linaje real de los príncipes,",
        "primary_source_quote": "Y dijo el rey a Aspenaz, jefe de sus eunucos, que trajera de los hijos de Israel, del linaje real de los príncipes,",
        "cognitive_operation": "cross_passage_fact_pairing",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En Daniel 1:3, ¿qué encargo específico dio Nabucodonosor a Aspenaz respecto al origen de los cautivos que debían ser traídos al palacio real?",
        "correct_option": 2,
        "options": [
            "Escoger a los sacerdotes y levitas que custodiaban los vasos sagrados depositados en el templo pagano de Sinar.",
            "Reclutar a los sabios más ancianos de Judá para que enseñaran las letras caldeas en la casa del tesoro del dios.",
            "Seleccionar de entre los hijos de Israel a jóvenes procedentes del linaje real y de la nobleza de los príncipes.",
            "Trasladar a los capitanes del ejército de Joacim para instruirlos tres años como consejeros de la corte babilónica."
        ],
        "explanation": "Daniel 1:3 precisa el mandato real dado a Aspenaz: «que trajera de los hijos de Israel, del linaje real de los príncipes».",
        "why_distractors_fail": {
            "Escoger a los sacerdotes y levitas que custodiaban los vasos sagrados depositados en el templo pagano de Sinar.": "La orden no especificaba sacerdotes o levitas, sino muchachos del linaje real y de la nobleza de los príncipes de Israel.",
            "Reclutar a los sabios más ancianos de Judá para que enseñaran las letras caldeas en la casa del tesoro del dios.": "El rey mandó traer «muchachos» para ser instruidos en las letras caldeas (Dan 1:4), no ancianos sabios para enseñar.",
            "Trasladar a los capitanes del ejército de Joacim para instruirlos tres años como consejeros de la corte babilónica.": "No se ordenó reclutar capitanes militares, sino jóvenes idóneos para estar en el palacio real."
        },
        "distractor_provenance": {
            "Escoger a los sacerdotes y levitas que custodiaban los vasos sagrados depositados en el templo pagano de Sinar.": "DAN1-V002-F01 (Daniel 1:2)",
            "Reclutar a los sabios más ancianos de Judá para que enseñaran las letras caldeas en la casa del tesoro del dios.": "DAN1-V004-F01 (Daniel 1:4)",
            "Trasladar a los capitanes del ejército de Joacim para instruirlos tres años como consejeros de la corte babilónica.": "DAN1-V005-F01 (Daniel 1:5)"
        }
    },

    # Item 20: Index 50 (V16-R3-PILOT2-DAN1-050) - Daniel 1:4 - chronological_event_sequence - HARD - noise=False - target pos: 3
    {
        "pilot_index": 50,
        "id": "V16-R3-PILOT2-DAN1-050",
        "question_id": "V16-R3-PILOT2-DAN1-050",
        "fact_id": "DAN1-V004-F01",
        "primary_fact_id": "DAN1-V004-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V004",
        "source_ref": "Daniel 1:4",
        "primary_source_ref": "Daniel 1:4",
        "source_quote": "muchachos en quienes no hubiera tacha alguna, de buen parecer, instruidos en toda sabiduría, sabios en ciencia, de buen entendimiento e idóneos para estar en el palacio del rey; y que les enseñara las letras y la lengua de los caldeos.",
        "primary_source_quote": "muchachos en quienes no hubiera tacha alguna, de buen parecer, instruidos en toda sabiduría, sabios en ciencia, de buen entendimiento e idóneos para estar en el palacio del rey; y que les enseñara las letras y la lengua de los caldeos.",
        "cognitive_operation": "chronological_event_sequence",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "¿Cuál es la secuencia completa de requisitos y propósitos formativos prescritos en Daniel 1:4 para los jóvenes hebreos seleccionados?",
        "correct_option": 3,
        "options": [
            "Ingerir la porción alimentaria real por tres años, presentarse ante Nabucodonosor y ser asignados al cuidado de los vasos sagrados en Sinar.",
            "Recibir nombres paganos del jefe de eunucos, superar la prueba vegetal de diez días y ser nombrados consejeros del imperio babilónico.",
            "Someterse a la dieta del rey, aprender la astronomía babilónica y asumir la mayordomía de los tesoros imperiales tras el largo asedio.",
            "Contar con intachable presencia y sabiduría previa, poseer idoneidad para estar en palacio y ser enseñados en las letras y lengua caldeas."
        ],
        "explanation": "Daniel 1:4 define primero los requisitos previos (sin tacha, buen parecer, sabios, entendidos e idóneos para el palacio) y luego el objetivo pedagógico inmediato: «y que les enseñara las letras y la lengua de los caldeos».",
        "why_distractors_fail": {
            "Ingerir la porción alimentaria real por tres años, presentarse ante Nabucodonosor y ser asignados al cuidado de los vasos sagrados en Sinar.": "La dieta real y el plazo de tres años corresponden a Daniel 1:5, no a los requisitos y objetivo formativo de Daniel 1:4.",
            "Recibir nombres paganos del jefe de eunucos, superar la prueba vegetal de diez días y ser nombrados consejeros del imperio babilónico.": "La imposición de nombres (Dan 1:7) y la prueba de diez días (Dan 1:12) son hechos posteriores.",
            "Someterse a la dieta del rey, aprender la astronomía babilónica y asumir la mayordomía de los tesoros imperiales tras el largo asedio.": "El texto especifica la enseñanza de las «letras y la lengua de los caldeos», no la mayordomía del tesoro idolátrico."
        },
        "distractor_provenance": {
            "Ingerir la porción alimentaria real por tres años, presentarse ante Nabucodonosor y ser asignados al cuidado de los vasos sagrados en Sinar.": "DAN1-V005-F01 (Daniel 1:5)",
            "Recibir nombres paganos del jefe de eunucos, superar la prueba vegetal de diez días y ser nombrados consejeros del imperio babilónico.": "DAN1-V007-F01 (Daniel 1:7)",
            "Someterse a la dieta del rey, aprender la astronomía babilónica y asumir la mayordomía de los tesoros imperiales tras el largo asedio.": "DAN1-V002-F01 (Daniel 1:2)"
        }
    },

    # Item 21: Index 51 (V16-R3-PILOT2-DAN1-051) - Daniel 1:5 - speaker_recipient_intermediary_attribution - HARD - noise=False - target pos: 0
    {
        "pilot_index": 51,
        "id": "V16-R3-PILOT2-DAN1-051",
        "question_id": "V16-R3-PILOT2-DAN1-051",
        "fact_id": "DAN1-V005-F01",
        "primary_fact_id": "DAN1-V005-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V005",
        "source_ref": "Daniel 1:5",
        "primary_source_ref": "Daniel 1:5",
        "source_quote": "Y les señaló el rey una porción diaria de la comida del rey y del vino que él bebía; y que los educara durante tres años, para que al fin de ellos se presentaran delante del rey.",
        "primary_source_quote": "Y les señaló el rey una porción diaria de la comida del rey y del vino que él bebía; y que los educara durante tres años, para que al fin de ellos se presentaran delante del rey.",
        "cognitive_operation": "speaker_recipient_intermediary_attribution",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En Daniel 1:5, ¿qué disposiciones decretó el rey Nabucodonosor respecto al sustento, período de instrucción y objetivo final para los jóvenes seleccionados?",
        "correct_option": 0,
        "options": [
            "Asignóles una porción diaria de su comida y vino, ordenó educarlos durante tres años y dispuso que al final se presentaran delante del rey.",
            "Concedióles una ración exclusiva de legumbres y agua, fijó una prueba de diez días y ordenó que comparecieran de inmediato ante Aspenaz.",
            "Mandó que sirvieran en la casa del tesoro de su dios en Sinar, los capacitó por siete años y los nombró inspectores de los vasos sagrados.",
            "Permitió que conservaran sus costumbres religiosas, redujo su educación a un año y los designó embajadores ante los príncipes de Judá."
        ],
        "explanation": "Daniel 1:5 especifica tres elementos del mandato de Nabucodonosor: porción diaria de comida y vino del rey, educación de tres años y comparecencia final delante del rey.",
        "why_distractors_fail": {
            "Concedióles una ración exclusiva de legumbres y agua, fijó una prueba de diez días y ordenó que comparecieran de inmediato ante Aspenaz.": "La dieta de legumbres y agua durante diez días fue solicitada por Daniel a Melsar (Dan 1:12), no prescrita por Nabucodonosor.",
            "Mandó que sirvieran en la casa del tesoro de su dios en Sinar, los capacitó por siete años y los nombró inspectores de los vasos sagrados.": "El rey fijó tres años de educación y no siete, y su propósito era que sirvieran en el palacio real.",
            "Permitió que conservaran sus costumbres religiosas, redujo su educación a un año y los designó embajadores ante los príncipes de Judá.": "El rey les impuso la comida y bebida de su mesa y una aculturación rigurosa de tres años."
        },
        "distractor_provenance": {
            "Concedióles una ración exclusiva de legumbres y agua, fijó una prueba de diez días y ordenó que comparecieran de inmediato ante Aspenaz.": "DAN1-V008-F02 (Daniel 1:8)",
            "Mandó que sirvieran en la casa del tesoro de su dios en Sinar, los capacitó por siete años y los nombró inspectores de los vasos sagrados.": "DAN1-V002-F01 (Daniel 1:2)",
            "Permitió que conservaran sus costumbres religiosas, redujo su educación a un año y los designó embajadores ante los príncipes de Judá.": "DAN1-V003-F01 (Daniel 1:3)"
        }
    },

    # Item 22: Index 52 (V16-R3-PILOT2-DAN1-052) - Daniel 1:6 - vision_year_monarch_river_correlation - EXPERT - noise=True - target pos: 1
    {
        "pilot_index": 52,
        "id": "V16-R3-PILOT2-DAN1-052",
        "question_id": "V16-R3-PILOT2-DAN1-052",
        "fact_id": "DAN1-V006-F01",
        "primary_fact_id": "DAN1-V006-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V006",
        "source_ref": "Daniel 1:6",
        "primary_source_ref": "Daniel 1:6",
        "source_quote": "Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá.",
        "primary_source_quote": "Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá.",
        "cognitive_operation": "vision_year_monarch_river_correlation",
        "translation_noise": True,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "De entre los hijos de Israel traídos cautivos a Babilonia tras el asedio de Joacim, ¿cuál grupo identifica expresamente Daniel 1:6 como perteneciente a la tribu de Judá?",
        "correct_option": 1,
        "options": [
            "A Aspenaz, Melsar y los sabios caldeos, designados para educar a los cautivos procedentes de Jerusalén.",
            "A Daniel, Ananías, Misael y Azarías, quienes procedían específicamente de los hijos de la tribu de Judá.",
            "A Beltsasar, Sadrac, Mesac y Abed-nego como apelativos nativos de los jóvenes antes de ser deportados.",
            "A Joacim y los sacerdotes del templo, llevados cautivos a Sinar para custodiar los vasos sagrados."
        ],
        "explanation": "Daniel 1:6 declara taxativamente: «Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá».",
        "why_distractors_fail": {
            "A Aspenaz, Melsar y los sabios caldeos, designados para educar a los cautivos procedentes de Jerusalén.": "Aspenaz y Melsar eran oficiales de la corte caldea y no cautivos de la tribu de Judá (Dan 1:3, 11).",
            "A Beltsasar, Sadrac, Mesac y Abed-nego como apelativos nativos de los jóvenes antes de ser deportados.": "Esos fueron los nombres caldeos paganos asignados posteriormente por el jefe de los eunucos (Dan 1:7), no sus nombres nativos de Judá.",
            "A Joacim y los sacerdotes del templo, llevados cautivos a Sinar para custodiar los vasos sagrados.": "Joacim fue entregado como rey vencido y no figura en la lista de muchachos educados en la corte (Dan 1:2, 6)."
        },
        "distractor_provenance": {
            "A Aspenaz, Melsar y los sabios caldeos, designados para educar a los cautivos procedentes de Jerusalén.": "DAN1-V003-F01 (Daniel 1:3)",
            "A Beltsasar, Sadrac, Mesac y Abed-nego como apelativos nativos de los jóvenes antes de ser deportados.": "DAN1-V007-F01 (Daniel 1:7)",
            "A Joacim y los sacerdotes del templo, llevados cautivos a Sinar para custodiar los vasos sagrados.": "DAN1-V002-F01 (Daniel 1:2)"
        }
    },

    # Item 23: Index 53 (V16-R3-PILOT2-DAN1-053) - Daniel 1:12 - biblical_text_vs_prophets_and_kings_contrast - EXPERT - noise=False - target pos: 2
    {
        "pilot_index": 53,
        "id": "V16-R3-PILOT2-DAN1-053",
        "question_id": "V16-R3-PILOT2-DAN1-053",
        "fact_id": "DAN1-V012-F01",
        "primary_fact_id": "DAN1-V012-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V012",
        "source_ref": "Daniel 1:12",
        "primary_source_ref": "Daniel 1:12",
        "source_quote": "—Te ruego que hagas la prueba con tus siervos durante diez días: que nos den legumbres para comer y agua para beber.",
        "primary_source_quote": "—Te ruego que hagas la prueba con tus siervos durante diez días: que nos den legumbres para comer y agua para beber.",
        "cognitive_operation": "biblical_text_vs_prophets_and_kings_contrast",
        "translation_noise": False,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "En la petición formulada por Daniel en Daniel 1:12, ¿cuáles son los términos exactos y específicos de la propuesta presentada al mayordomo?",
        "correct_option": 2,
        "options": [
            "Un período de tres años en el que consumirían solo los alimentos no sacrificados en el templo de Babilonia.",
            "Una abstinencia temporal de vino caldeo mientras conservaban la porción ordinaria de la carne de la corte.",
            "Una prueba de diez días en la que se les suministrara exclusivamente legumbres para comer y agua para beber.",
            "Un ayuno total durante diez jornadas para demostrar la preservación sobrenatural del Dios de Jerusalén."
        ],
        "explanation": "Daniel 1:12 registra las palabras literales: «Te ruego que hagas la prueba con tus siervos durante diez días: que nos den legumbres para comer y agua para beber».",
        "why_distractors_fail": {
            "Un período de tres años en el que consumirían solo los alimentos no sacrificados en el templo de Babilonia.": "La prueba solicitada a Melsar era de diez días y no de tres años (los tres años correspondían al plan educativo general de Daniel 1:5).",
            "Una abstinencia temporal de vino caldeo mientras conservaban la porción ordinaria de la carne de la corte.": "Daniel pidió abstenerse tanto de la comida como del vino real, solicitando legumbres y agua exclusivamente (Dan 1:8, 12).",
            "Un ayuno total durante diez jornadas para demostrar la preservación sobrenatural del Dios de Jerusalén.": "No solicitaron un ayuno total, sino una dieta definida y nutritiva consistente en legumbres y agua."
        },
        "distractor_provenance": {
            "Un período de tres años en el que consumirían solo los alimentos no sacrificados en el templo de Babilonia.": "DAN1-V005-F01 (Daniel 1:5)",
            "Una abstinencia temporal de vino caldeo mientras conservaban la porción ordinaria de la carne de la corte.": "DAN1-V008-F02 (Daniel 1:8)",
            "Un ayuno total durante diez jornadas para demostrar la preservación sobrenatural del Dios de Jerusalén.": "DAN1-V002-F01 (Daniel 1:2)"
        }
    },

    # Item 24: Index 54 (V16-R3-PILOT2-DAN1-054) - Daniel 1:17 - cause_condition_consequence_chain - HARD - noise=False - target pos: 3
    {
        "pilot_index": 54,
        "id": "V16-R3-PILOT2-DAN1-054",
        "question_id": "V16-R3-PILOT2-DAN1-054",
        "fact_id": "DAN1-V017-F01",
        "primary_fact_id": "DAN1-V017-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V017",
        "source_ref": "Daniel 1:17",
        "primary_source_ref": "Daniel 1:17",
        "source_quote": "A estos cuatro muchachos, Dios les dio conocimiento e inteligencia en todas las letras y ciencias; y Daniel tuvo entendimiento en toda visión y sueños.",
        "primary_source_quote": "A estos cuatro muchachos, Dios les dio conocimiento e inteligencia en todas las letras y ciencias; y Daniel tuvo entendimiento en toda visión y sueños.",
        "cognitive_operation": "cause_condition_consequence_chain",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "Según Daniel 1:17, ¿qué bendición divina específica recibieron los cuatro jóvenes en común y qué don distintivo le fue concedido a Daniel como consecuencia de su fidelidad?",
        "correct_option": 3,
        "options": [
            "Dios otorgó a los cuatro la custodia de los vasos sagrados en Sinar, confiriendo a Daniel la revelación del tiempo del cautiverio.",
            "Dios confirió a los cuatro inmunidad ante las leyes caldeas, concediendo a Daniel la jefatura inmediata sobre todos los sabios.",
            "Dios otorgó a los cuatro la gracia de hablar la lengua caldea sin estudio, dando a Daniel el gobierno secular de la corte real.",
            "Dios concedió a los cuatro conocimiento e inteligencia en letras y ciencias, otorgando a Daniel entendimiento en visiones y sueños."
        ],
        "explanation": "Daniel 1:17 precisa que Dios dio a los cuatro muchachos conocimiento e inteligencia en todas las letras y ciencias, mientras que Daniel recibió además entendimiento en toda visión y sueños.",
        "why_distractors_fail": {
            "Dios otorgó a los cuatro la custodia de los vasos sagrados en Sinar, confiriendo a Daniel la revelación del tiempo del cautiverio.": "Los vasos sagrados estaban en la casa del dios pagano en Sinar (Dan 1:2); no fueron puestos bajo la custodia de los cuatro muchachos.",
            "Dios confirió a los cuatro inmunidad ante las leyes caldeas, concediendo a Daniel la jefatura inmediata sobre todos los sabios.": "El texto sagrado no menciona inmunidad jurídica ni nombramiento de jefatura en este versículo (ello ocurre en Daniel 2).",
            "Dios otorgó a los cuatro la gracia de hablar la lengua caldea sin estudio, dando a Daniel el gobierno secular de la corte real.": "Los muchachos estudiaron diligentemente las letras y la lengua (Dan 1:4), y Dios bendijo su esfuerzo con inteligencia superior."
        },
        "distractor_provenance": {
            "Dios otorgó a los cuatro la custodia de los vasos sagrados en Sinar, confiriendo a Daniel la revelación del tiempo del cautiverio.": "DAN1-V002-F01 (Daniel 1:2)",
            "Dios confirió a los cuatro inmunidad ante las leyes caldeas, concediendo a Daniel la jefatura inmediata sobre todos los sabios.": "DAN1-V004-F01 (Daniel 1:4)",
            "Dios otorgó a los cuatro la gracia de hablar la lengua caldea sin estudio, dando a Daniel el gobierno secular de la corte real.": "DAN1-V005-F01 (Daniel 1:5)"
        }
    },

    # Item 25: Index 55 (V16-R3-PILOT2-DAN1-055) - Daniel 1:6 - cross_passage_fact_pairing - HARD - noise=False - target pos: 0
    {
        "pilot_index": 55,
        "id": "V16-R3-PILOT2-DAN1-055",
        "question_id": "V16-R3-PILOT2-DAN1-055",
        "fact_id": "DAN1-V006-F01",
        "primary_fact_id": "DAN1-V006-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V006",
        "source_ref": "Daniel 1:6",
        "primary_source_ref": "Daniel 1:6",
        "source_quote": "Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá.",
        "primary_source_quote": "Entre ellos estaban Daniel, Ananías, Misael y Azarías, de los hijos de Judá.",
        "cognitive_operation": "cross_passage_fact_pairing",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "Al contrastar Daniel 1:6 con Daniel 1:7, ¿cómo se empareja correctamente la identidad tribal hebrea de estos cuatro jóvenes con la imposición nominal del jefe de los eunucos?",
        "correct_option": 0,
        "options": [
            "Eran de los hijos de Judá: a Daniel puso Beltsasar; a Ananías, Sadrac; a Misael, Mesac; y a Azarías, Abed-nego.",
            "Eran del linaje de Leví: a Daniel puso Aspenaz; a Ananías, Melsar; a Misael, Sinar; y a Azarías, Nabucodonosor.",
            "Eran príncipes de Benjamín: a Daniel puso Sadrac; a Ananías, Beltsasar; a Misael, Abed-nego; y a Azarías, Mesac.",
            "Eran jefes de Efraín: a Daniel puso Melsar; a Ananías, Abed-nego; a Misael, Beltsasar; y a Azarías, Sadrac."
        ],
        "explanation": "Daniel 1:6-7 establece que los cuatro eran de los hijos de Judá y registra la correspondencia exacta: Daniel/Beltsasar, Ananías/Sadrac, Misael/Mesac, Azarías/Abed-nego.",
        "why_distractors_fail": {
            "Eran del linaje de Leví: a Daniel puso Aspenaz; a Ananías, Melsar; a Misael, Sinar; y a Azarías, Nabucodonosor.": "No eran de la tribu de Leví sino de Judá, y los nombres Aspenaz, Melsar y Sinar corresponden a oficiales caldeos y lugares geográficos (Dan 1:2, 3, 11).",
            "Eran príncipes de Benjamín: a Daniel puso Sadrac; a Ananías, Beltsasar; a Misael, Abed-nego; y a Azarías, Mesac.": "Eran de Judá y no de Benjamín, y los nombres babilónicos están intercambiados erróneamente.",
            "Eran jefes de Efraín: a Daniel puso Melsar; a Ananías, Abed-nego; a Misael, Beltsasar; y a Azarías, Sadrac.": "Eran de Judá y no de Efraín, y se introducen nombres de funcionarios como Melsar en lugar de los nombres caldeos dados."
        },
        "distractor_provenance": {
            "Eran del linaje de Leví: a Daniel puso Aspenaz; a Ananías, Melsar; a Misael, Sinar; y a Azarías, Nabucodonosor.": "DAN1-V003-F01 (Daniel 1:3)",
            "Eran príncipes de Benjamín: a Daniel puso Sadrac; a Ananías, Beltsasar; a Misael, Abed-nego; y a Azarías, Mesac.": "DAN1-V007-F01 (Daniel 1:7)",
            "Eran jefes de Efraín: a Daniel puso Melsar; a Ananías, Abed-nego; a Misael, Beltsasar; y a Azarías, Sadrac.": "DAN1-V007-F01 (Daniel 1:7)"
        }
    },

    # Item 26: Index 56 (V16-R3-PILOT2-DAN1-056) - Daniel 1:9 - chronological_event_sequence - HARD - noise=False - target pos: 1
    {
        "pilot_index": 56,
        "id": "V16-R3-PILOT2-DAN1-056",
        "question_id": "V16-R3-PILOT2-DAN1-056",
        "fact_id": "DAN1-V009-F01",
        "primary_fact_id": "DAN1-V009-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V009",
        "source_ref": "Daniel 1:9",
        "primary_source_ref": "Daniel 1:9",
        "source_quote": "Puso Dios a Daniel en gracia y en buena voluntad con el jefe de los eunucos;",
        "primary_source_quote": "Puso Dios a Daniel en gracia y en buena voluntad con el jefe de los eunucos;",
        "cognitive_operation": "chronological_event_sequence",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "¿En qué punto cronológico de los acontecimientos de Daniel 1 se sitúa la intervención divina que otorgó a Daniel gracia y buena voluntad ante el jefe de los eunucos?",
        "correct_option": 1,
        "options": [
            "Después de que concluyeron los diez días de prueba y antes de que los jóvenes fueran examinados por Nabucodonosor.",
            "Después de que Daniel propuso no contaminarse y antes de que Aspenaz expresara su temor por el castigo del rey.",
            "Antes del asedio de Jerusalén en el tercer año de Joacim y antes del traslado de los vasos a la tierra de Sinar.",
            "Luego de que los cuatro jóvenes fueran hallados diez veces superiores a todos los magos y astrólogos de Babilonia."
        ],
        "explanation": "En Daniel 1:8-10, la secuencia es clara: primero Daniel propuso en su corazón no contaminarse (v. 8), inmediatamente Dios puso a Daniel en gracia con Aspenaz (v. 9), y seguidamente Aspenaz le explicó su temor al rey (v. 10).",
        "why_distractors_fail": {
            "Después de que concluyeron los diez días de prueba y antes de que los jóvenes fueran examinados por Nabucodonosor.": "La gracia ante Aspenaz ocurrió antes de acordar la prueba de diez días con Melsar (Dan 1:9-12).",
            "Antes del asedio de Jerusalén en el tercer año de Joacim y antes del traslado de los vasos a la tierra de Sinar.": "Este hecho ocurrió en Babilonia durante la educación de los cautivos, mucho después del asedio inicial de Jerusalén (Dan 1:1-2).",
            "Luego de que los cuatro jóvenes fueran hallados diez veces superiores a todos los magos y astrólogos de Babilonia.": "La comparecencia final y proclamación de sabiduría superior tuvo lugar al fin de los tres años (Dan 1:18-20)."
        },
        "distractor_provenance": {
            "Después de que concluyeron los diez días de prueba y antes de que los jóvenes fueran examinados por Nabucodonosor.": "DAN1-V015-F01 (Daniel 1:15)",
            "Antes del asedio de Jerusalén en el tercer año de Joacim y antes del traslado de los vasos a la tierra de Sinar.": "DAN1-V001-F04 (Daniel 1:1)",
            "Luego de que los cuatro jóvenes fueran hallados diez veces superiores a todos los magos y astrólogos de Babilonia.": "DAN1-V005-F01 (Daniel 1:5)"
        }
    },

    # Item 27: Index 57 (V16-R3-PILOT2-DAN1-057) - Daniel 1:11 - speaker_recipient_intermediary_attribution - HARD - noise=False - target pos: 2
    {
        "pilot_index": 57,
        "id": "V16-R3-PILOT2-DAN1-057",
        "question_id": "V16-R3-PILOT2-DAN1-057",
        "fact_id": "DAN1-V011-F01",
        "primary_fact_id": "DAN1-V011-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V011",
        "source_ref": "Daniel 1:11",
        "primary_source_ref": "Daniel 1:11",
        "source_quote": "Entonces dijo Daniel a Melsar, a quien el jefe de los eunucos había puesto sobre Daniel, Ananías, Misael y Azarías:",
        "primary_source_quote": "Entonces dijo Daniel a Melsar, a quien el jefe de los eunucos había puesto sobre Daniel, Ananías, Misael y Azarías:",
        "cognitive_operation": "speaker_recipient_intermediary_attribution",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En Daniel 1:11, ¿a qué funcionario intermediario se dirigió Daniel tras la vacilación inicial de Aspenaz, y qué rol desempeñaba dicho oficial respecto a los cuatro jóvenes hebreos?",
        "correct_option": 2,
        "options": [
            "A Nabucodonosor, el monarca que había decretado la porción diaria de comida y vino para los jóvenes durante sus tres años.",
            "A Aspenaz, el principal eunuco de palacio encargado de cambiar los nombres hebreos e instruirlos en las letras caldeas.",
            "A Melsar, el mayordomo asignado por el jefe de los eunucos para la supervisión directa de Daniel, Ananías, Misael y Azarías.",
            "Al sumo sacerdote de Sinar, el custodio pagano designado para almacenar los utensilios sagrados en el templo de su dios."
        ],
        "explanation": "Daniel 1:11 especifica que Daniel habló «a Melsar, a quien el jefe de los eunucos había puesto sobre Daniel, Ananías, Misael y Azarías».",
        "why_distractors_fail": {
            "A Nabucodonosor, el monarca que había decretado la porción diaria de comida y vino para los jóvenes durante sus tres años.": "Daniel no se dirigió a Nabucodonosor, sino al mayordomo subalterno Melsar para evitar comprometer a Aspenaz.",
            "A Aspenaz, el principal eunuco de palacio encargado de cambiar los nombres hebreos e instruirlos en las letras caldeas.": "Aspenaz ya había manifestado su vacilación y temor en el versículo 10; Daniel recurrió entonces a Melsar (v. 11).",
            "Al sumo sacerdote de Sinar, el custodio pagano designado para almacenar los utensilios sagrados en el templo de su dios.": "El relato no menciona a ningún sacerdote pagano como supervisor de la dieta de los cautivos hebreos."
        },
        "distractor_provenance": {
            "A Nabucodonosor, el monarca que había decretado la porción diaria de comida y vino para los jóvenes durante sus tres años.": "DAN1-V005-F01 (Daniel 1:5)",
            "A Aspenaz, el principal eunuco de palacio encargado de cambiar los nombres hebreos e instruirlos en las letras caldeas.": "DAN1-V003-F01 (Daniel 1:3)",
            "Al sumo sacerdote de Sinar, el custodio pagano designado para almacenar los utensilios sagrados en el templo de su dios.": "DAN1-V002-F01 (Daniel 1:2)"
        }
    },

    # Item 28: Index 58 (V16-R3-PILOT2-DAN1-058) - Daniel 1:12 - vision_year_monarch_river_correlation - HARD - noise=False - target pos: 3
    {
        "pilot_index": 58,
        "id": "V16-R3-PILOT2-DAN1-058",
        "question_id": "V16-R3-PILOT2-DAN1-058",
        "fact_id": "DAN1-V012-F01",
        "primary_fact_id": "DAN1-V012-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V012",
        "source_ref": "Daniel 1:12",
        "primary_source_ref": "Daniel 1:12",
        "source_quote": "—Te ruego que hagas la prueba con tus siervos durante diez días: que nos den legumbres para comer y agua para beber.",
        "primary_source_quote": "—Te ruego que hagas la prueba con tus siervos durante diez días: que nos den legumbres para comer y agua para beber.",
        "cognitive_operation": "vision_year_monarch_river_correlation",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "¿Qué parámetros precisos de duración, alimento y bebida estableció Daniel al proponer formalmente la prueba alimentaria a Melsar en Daniel 1:12?",
        "correct_option": 3,
        "options": [
            "Un lapso formativo de tres años, requiriendo ingerir la ración diaria de vino y manjares provista por el rey.",
            "Un período de setenta días, demandando pan sin levadura y vino no consagrado a los dioses de Babilonia en Sinar.",
            "Una prueba de treinta días, pidiendo frutos secos y agua traída exclusivamente de los manantiales de Jerusalén.",
            "Un plazo exacto de diez días, solicitando recibir únicamente legumbres como alimento y agua pura para beber."
        ],
        "explanation": "Daniel 1:12 delimita con exactitud los términos: duración de diez días, legumbres para comer y agua para beber.",
        "why_distractors_fail": {
            "Un lapso formativo de tres años, requiriendo ingerir la ración diaria de vino y manjares provista por el rey.": "Tres años era el plazo general de educación caldea decretado por Nabucodonosor (Dan 1:5), no el plazo de la prueba vegetal.",
            "Un período de setenta días, demandando pan sin levadura y vino no consagrado a los dioses de Babilonia en Sinar.": "Daniel no pidió setenta días ni vino de ningún tipo; solicitó diez días y agua pura (Dan 1:8, 12).",
            "Una prueba de treinta días, pidiendo frutos secos y agua traída exclusivamente de los manantiales de Jerusalén.": "El texto no menciona treinta días ni frutos secos traídos de Jerusalén, sino diez días con legumbres y agua."
        },
        "distractor_provenance": {
            "Un lapso formativo de tres años, requiriendo ingerir la ración diaria de vino y manjares provista por el rey.": "DAN1-V005-F01 (Daniel 1:5)",
            "Un período de setenta días, demandando pan sin levadura y vino no consagrado a los dioses de Babilonia en Sinar.": "DAN1-V001-F04 (Daniel 1:1)",
            "Una prueba de treinta días, pidiendo frutos secos y agua traída exclusivamente de los manantiales de Jerusalén.": "DAN1-V002-F01 (Daniel 1:2)"
        }
    },

    # Item 29: Index 59 (V16-R3-PILOT2-DAN1-059) - Daniel 1:15 - biblical_text_vs_prophets_and_kings_contrast - EXPERT - noise=True - target pos: 0
    {
        "pilot_index": 59,
        "id": "V16-R3-PILOT2-DAN1-059",
        "question_id": "V16-R3-PILOT2-DAN1-059",
        "fact_id": "DAN1-V015-F01",
        "primary_fact_id": "DAN1-V015-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V015",
        "source_ref": "Daniel 1:15",
        "primary_source_ref": "Daniel 1:15",
        "source_quote": "Y al cabo de los diez días pareció el rostro de ellos mejor y más robusto que el de los otros muchachos que comían de la porción de la comida del rey.",
        "primary_source_quote": "Y al cabo de los diez días pareció el rostro de ellos mejor y más robusto que el de los otros muchachos que comían de la porción de la comida del rey.",
        "cognitive_operation": "biblical_text_vs_prophets_and_kings_contrast",
        "translation_noise": True,
        "target_difficulty": "EXPERT",
        "difficulty": "expert",
        "family": "single_choice_contextual",
        "question": "Cumplido el término de los diez días fijados para la prueba en Daniel 1:15, ¿cómo describe el texto sagrado el semblante físico de los jóvenes hebreos en comparación con quienes consumían la ración real?",
        "correct_option": 0,
        "options": [
            "Pareció el rostro de ellos visiblemente mejor y más robusto que el de todos los muchachos que comían de la porción del rey.",
            "Mostróse su semblante demudado y débil por el rigor de la abstinencia, forzando a Melsar a ocultarlos del monarca caldeo.",
            "Manifestóse su fisonomía idéntica a la de los sabios de Babilonia, sin observarse diferencia física tras la prueba vegetal.",
            "Presentóse su porte pálido y austero como señal exclusiva de penitencia por los pecados y el cautiverio del pueblo de Judá."
        ],
        "explanation": "Daniel 1:15 declara taxativamente: «Y al cabo de los diez días pareció el rostro de ellos mejor y más robusto que el de los otros muchachos que comían de la porción de la comida del rey».",
        "why_distractors_fail": {
            "Mostróse su semblante demudado y débil por el rigor de la abstinencia, forzando a Melsar a ocultarlos del monarca caldeo.": "Ese era el temor inicial de Aspenaz (Dan 1:10), pero el resultado real fue un rostro visiblemente mejor y más robusto.",
            "Manifestóse su fisonomía idéntica a la de los sabios de Babilonia, sin observarse diferencia física tras la prueba vegetal.": "El texto resalta una clara y notoria superioridad física en favor de los jóvenes que consumieron legumbres y agua.",
            "Presentóse su porte pálido y austero como señal exclusiva de penitencia por los pecados y el cautiverio del pueblo de Judá.": "Su apariencia no fue de palidez o demacración penitencial, sino de vigor, salud y robustez física."
        },
        "distractor_provenance": {
            "Mostróse su semblante demudado y débil por el rigor de la abstinencia, forzando a Melsar a ocultarlos del monarca caldeo.": "DAN1-V005-F01 (Daniel 1:5)",
            "Manifestóse su fisonomía idéntica a la de los sabios de Babilonia, sin observarse diferencia física tras la prueba vegetal.": "DAN1-V004-F01 (Daniel 1:4)",
            "Presentóse su porte pálido y austero como señal exclusiva de penitencia por los pecados y el cautiverio del pueblo de Judá.": "DAN1-V001-F04 (Daniel 1:1)"
        }
    },

    # Item 30: Index 60 (V16-R3-PILOT2-DAN1-060) - Daniel 1:17 - cause_condition_consequence_chain - HARD - noise=False - target pos: 1
    {
        "pilot_index": 60,
        "id": "V16-R3-PILOT2-DAN1-060",
        "question_id": "V16-R3-PILOT2-DAN1-060",
        "fact_id": "DAN1-V017-F01",
        "primary_fact_id": "DAN1-V017-F01",
        "chapter": "DAN1",
        "source_unit_id": "DAN1-V017",
        "source_ref": "Daniel 1:17",
        "primary_source_ref": "Daniel 1:17",
        "source_quote": "A estos cuatro muchachos, Dios les dio conocimiento e inteligencia en todas las letras y ciencias; y Daniel tuvo entendimiento en toda visión y sueños.",
        "primary_source_quote": "A estos cuatro muchachos, Dios les dio conocimiento e inteligencia en todas las letras y ciencias; y Daniel tuvo entendimiento en toda visión y sueños.",
        "cognitive_operation": "cause_condition_consequence_chain",
        "translation_noise": False,
        "target_difficulty": "HARD",
        "difficulty": "hard",
        "family": "single_choice_contextual",
        "question": "En la estructura teológica de Daniel 1:17, ¿cuál es la relación de causa, condición y consecuencia que explica el extraordinario saber alcanzado por los jóvenes hebreos en Babilonia?",
        "correct_option": 1,
        "options": [
            "La asimilación de la cultura caldea (causa) condujo a que, tras comer los manjares reales (condición), Nabucodonosor los nombrara gobernantes sobre los sabios de Babilonia (consecuencia).",
            "La fidelidad a los preceptos de Dios (causa) permitió que, con el favor celestial (condición), recibieran inteligencia en letras y ciencias, y Daniel en visiones y sueños (consecuencia).",
            "El temor al enojo de Aspenaz (causa) motivó que, al recibir nombres babilónicos (condición), memorizaran la literatura pagana para evitar la muerte en la corte imperial (consecuencia).",
            "El traslado de los vasos de Dios (causa) hizo posible que, tras tres años de estudio (condición), los magos caldeos les enseñasen los misterios de la astrología de Sinar (consecuencia)."
        ],
        "explanation": "Daniel 1:17 revela que Dios recompensó la fidelidad de los jóvenes otorgándoles conocimiento, inteligencia en todas las letras y ciencias, y a Daniel entendimiento en toda visión y sueños.",
        "why_distractors_fail": {
            "La asimilación de la cultura caldea (causa) condujo a que, tras comer los manjares reales (condición), Nabucodonosor los nombrara gobernantes sobre los sabios de Babilonia (consecuencia).": "No comieron de los manjares reales sino que se abstuvieron, y su sabiduría provino de Dios y no de la asimilación pagana.",
            "El temor al enojo de Aspenaz (causa) motivó que, al recibir nombres babilónicos (condición), memorizaran la literatura pagana para evitar la muerte en la corte imperial (consecuencia).": "No actuaron por temor a Aspenaz ni para evitar castigos, sino por devoción reverente y fidelidad a los principios divinos.",
            "El traslado de los vasos de Dios (causa) hizo posible que, tras tres años de estudio (condición), los magos caldeos les enseñasen los misterios de la astrología de Sinar (consecuencia).": "Su ciencia no dependía de la astrología idólatra de los caldeos ni del traslado de los vasos, sino del don directo de Dios (Dan 1:17, 20)."
        },
        "distractor_provenance": {
            "La asimilación de la cultura caldea (causa) condujo a que, tras comer los manjares reales (condición), Nabucodonosor los nombrara gobernantes sobre los sabios de Babilonia (consecuencia).": "DAN1-V005-F01 (Daniel 1:5)",
            "El temor al enojo de Aspenaz (causa) motivó que, al recibir nombres babilónicos (condición), memorizaran la literatura pagana para evitar la muerte en la corte imperial (consecuencia).": "DAN1-V007-F01 (Daniel 1:7)",
            "El traslado de los vasos de Dios (causa) hizo posible que, tras tres años de estudio (condición), los magos caldeos les enseñasen los misterios de la astrología de Sinar (consecuencia).": "DAN1-V002-F01 (Daniel 1:2)"
        }
    }
]

# Validation logic
print(f"Total items created: {len(items_data)}")
assert len(items_data) == 30, f"Expected 30 items, got {len(items_data)}"

# Check distribution of correct_option
option_counts = {0: 0, 1: 0, 2: 0, 3: 0}
for i, it in enumerate(items_data):
    # Verify ID matches dossier
    d = dossiers[i]
    assert it['id'] == d['id'], f"ID mismatch at {i}: {it['id']} vs {d['id']}"
    assert it['pilot_index'] == d['pilot_index'], f"Pilot index mismatch at {i}: {it['pilot_index']} vs {d['pilot_index']}"
    assert it['cognitive_operation'] == d['cognitive_operation'], f"Cognitive op mismatch at {i}"
    assert it['translation_noise'] == d['translation_noise'], f"Noise mismatch at {i}"
    assert it['target_difficulty'] == d['target_difficulty'], f"Target diff mismatch at {i}"
    
    # Options length symmetry
    lens = [len(opt) for opt in it['options']]
    ratio = max(lens) / min(lens)
    assert ratio < 1.15, f"Symmetry ratio exceeded at item {i+1} ({it['id']}): {ratio:.4f} (lens: {lens})"
    
    # Correct answer alignment
    c_opt = it['correct_option']
    assert 0 <= c_opt <= 3, f"Invalid correct_option {c_opt} at item {i+1}"
    it['correct_answer'] = it['options'][c_opt]
    it['accepted_answers'] = [it['options'][c_opt]]
    option_counts[c_opt] += 1
    
    # Why distractors fail validation
    incorrect_options = [opt for j, opt in enumerate(it['options']) if j != c_opt]
    assert len(incorrect_options) == 3
    for inc in incorrect_options:
        assert inc in it['why_distractors_fail'], f"Missing why_distractors_fail for '{inc}' in item {i+1}"
        assert len(it['why_distractors_fail'][inc]) > 10, f"Why distractor fail too short for '{inc}' in item {i+1}"
        assert inc in it['distractor_provenance'], f"Missing distractor_provenance for '{inc}' in item {i+1}"

print(f"Distribution of correct_option: {option_counts}")
print("ALL VALIDATION CHECKS PASSED PERFECTLY!")

# Ensure output directory exists
os.makedirs('.work/competitive-v16/piloto-r3-v2/authors/author_2', exist_ok=True)

# Write output file
out_path = '.work/competitive-v16/piloto-r3-v2/authors/author_2/batch_2.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(items_data, f, indent=2, ensure_ascii=False)

print(f"Successfully saved {len(items_data)} items to {out_path}")
