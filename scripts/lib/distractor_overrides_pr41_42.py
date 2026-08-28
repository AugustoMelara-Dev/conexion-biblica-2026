"""Audited distractor fact overrides for the residual PR41--PR42 defects.

The mapping is data-only: consumers resolve each candidate through the current
``fact_inventory.json`` so every replacement remains source-traceable.  Each
tuple has three distinct existing fact IDs and excludes the target fact.
"""

from __future__ import annotations


# Target fact_id -> three replacement fact_ids.
DISTRACTOR_FACT_ID_OVERRIDES: dict[str, tuple[str, str, str]] = {
    # «Mirando con ________ el horno»: singular nouns that can follow «con»
    # naturally (confianza, claridad, reverencia), all source-backed terms.
    "PR41-P040-P003-S004-F02": (
        "PR41-P040-P008-S002-F02",
        "PR41-P041-P001-S001-F02",
        "PR41-P041-P005-S002-F01",
    ),
    # «¿Qué ________?»: second-person singular present-indicative verbs, so
    # the distractors do not expose the answer by mood/person morphology.
    "PR42-P046-P001-S005-F02": (
        "DAN6-V020-F02",
        "DAN9-V004-F03",
        "DAN9-V015-F05",
    ),
}


__all__ = ["DISTRACTOR_FACT_ID_OVERRIDES"]
