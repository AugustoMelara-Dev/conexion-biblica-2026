"""Manual overrides for the real DAN4--DAN6 distractor/role defects.

The keys are target ``fact_id`` values.  Each distractor tuple contains three
existing inventory fact IDs whose answers preserve the local slot's usable
grammar (person/number, mood/tense, nominal/adjectival class, or valency).
The source facts remain auditable through ``fact_inventory.json``; this module
does not mutate the bank or the generator.
"""

from __future__ import annotations


# Target fact -> three inventory facts for replacement distractors.
# The tuple answers are intentionally distinct from one another and from the
# target answer.  Cross-chapter facts are used only where DAN4--DAN6 do not
# contain three independently extracted forms with the required slot shape.
DISTRACTOR_FACT_ID_OVERRIDES: dict[str, tuple[str, str, str]] = {
    # Daniel 4:4, "estaba ___": masculine singular predicatives.
    "DAN4-V004-F02": ("DAN4-V016-F03", "DAN5-V005-F03", "DAN6-V004-F04"),
    # Daniel 4:7, "les ___ el sueño": first-person preterites with object valency.
    "DAN4-V007-F02": ("DAN2-V005-F01", "DAN7-V028-F04", "DAN4-V030-F02"),
    # Daniel 4:17, "sobre él ___ al más humilde": finite third-person actions.
    "DAN4-V017-F02": (
        "PR40-P037-P003-S001-F01",
        "PR42-P045-P001-S002-F02",
        "PR44-P057-P008-S002-F01",
    ),
    # Daniel 4:21, "había ___ para todos": singular nouns.
    "DAN4-V021-F02": ("DAN4-V024-F03", "DAN5-V011-F02", "DAN6-V003-F04"),
    # Daniel 4:21, "cuyo ___ era hermoso": masculine singular nouns.
    "DAN4-V021-F03": ("DAN4-V026-F03", "DAN5-V011-F02", "DAN5-V021-F03"),
    # Daniel 4:23, "Cortad ... y ___": plural imperatives plus a compatible
    # second-person plural future coordination.
    "DAN4-V023-F02": ("DAN4-V014-F01", "DAN2-V006-F02", "DAN2-V006-F01"),
    # Daniel 4:37, "puede ___ a los que": infinitives with human-object valency.
    "DAN4-V037-F01": ("DAN11-V044-F04", "DAN6-V004-F03", "DAN11-V039-F03"),
    # Daniel 4:37, "alabo, engrandezco y ___": first-person finite actions.
    "DAN4-V037-F02": (
        "PR39-P029-P005-S003-F02",
        "DAN11-V002-F04",
        "DAN10-V021-F02",
    ),
    # Daniel 5:1, "hizo un gran ___": masculine singular nouns.
    "DAN5-V001-F03": ("DAN4-V004-F03", "DAN5-V021-F03", "DAN5-V026-F03"),
    # Daniel 5:4, "___ vino": third-person plural preterites with transitive use.
    "DAN5-V004-F01": ("DAN1-V019-F02", "DAN10-V008-F01", "DAN10-V008-F02"),
    # Daniel 5:7, "que ___ venir": past subjunctives that license infinitive venir.
    "DAN5-V007-F02": (
        "PR39-P027-P004-S002-F02",
        "PR42-P044-P006-S002-F02",
        "PR44-P057-P002-S002-F01",
    ),
    # Daniel 5:15, "sabios y ___": plural human/group nouns.
    "DAN5-V015-F03": ("DAN4-V007-F03", "DAN4-V009-F03", "DAN6-V006-F03"),
    # Daniel 5:16, coordinated second-person singular future verbs.
    "DAN5-V016-F01": (
        "PR41-P041-P007-S004-F01",
        "PR43-P051-P008-S001-F01",
        "DAN12-V013-F02",
    ),
    # Daniel 5:20, "fue ... y ___ de su gloria": masculine participles with de.
    "DAN5-V020-F02": ("DAN9-V005-F02", "DAN9-V007-F06", "DAN7-V012-F01"),
    # Daniel 5:20, "fue ___ del trono": masculine passive participles.
    "DAN5-V020-F03": ("DAN12-V011-F08", "DAN11-V008-F06", "PR43-P047-P002-S004-F02"),
    # Daniel 6:2, "para que ... no ___ perjudicado": subjunctive forms with
    # a grammatical copular/resultative reading.
    "DAN6-V002-F03": ("DAN1-V004-F02", "DAN2-V035-F01", "PR44-P056-P003-S005-F02"),
    # Daniel 6:6, "gobernadores y ___": plural nouns.
    "DAN6-V006-F03": ("DAN4-V007-F03", "DAN4-V009-F03", "DAN5-V015-F03"),
    # Daniel 6:6, "se juntaron ___ del rey": locative adverbs/preposition-like
    # terms, rather than manner/degree words.
    "DAN6-V006-F04": ("DAN8-V017-F08", "DAN8-V007-F12", "DAN11-V010-F08"),
    # Daniel 6:14, "en gran ___": feminine singular nouns.
    "DAN6-V014-F02": ("DAN4-V010-F03", "DAN5-V018-F03", "DAN4-V022-F03"),
    # Daniel 6:23, "en gran ___": singular nouns.
    "DAN6-V023-F02": ("DAN4-V010-F03", "DAN5-V018-F03", "DAN5-V021-F03"),
    # Daniel 6:27, "Él ___ y libra": third-person present actions.
    "DAN6-V027-F03": ("DAN10-V021-F03", "DAN7-V005-F03", "DAN9-V018-F04"),
}


# Target contextual fact -> role required by the local blank syntax.
CONTEXTUAL_ROLE_OVERRIDES: dict[str, str] = {
    "DAN4-V036-F02": "state",
    "DAN4-V037-F02": "action",
    "DAN5-V014-F03": "modifier",
    "DAN5-V020-F02": "state",
    "DAN5-V024-F03": "object",
    "DAN5-V027-F03": "state",
    "DAN6-V002-F04": "state",
    "DAN6-V006-F04": "location",
    "DAN6-V015-F03": "state",
    "DAN6-V026-F03": "subject",
}


__all__ = ["DISTRACTOR_FACT_ID_OVERRIDES", "CONTEXTUAL_ROLE_OVERRIDES"]
