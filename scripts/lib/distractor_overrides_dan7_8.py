"""Audited distractor and contextual-role overrides for Daniel 7--8.

This module is deliberately data-only.  The tuples contain fact IDs from the
current ``public/banks/final-2026/fact_inventory.json``; consumers can resolve
the answer/source_quote from that inventory instead of copying lexical data.
Every tuple is ordered as three replacement distractors and excludes the
correct fact for its slot.
"""

from __future__ import annotations


# fact_id -> three inventory fact_ids.  Each selected answer keeps the target
# slot's broad category/valency (noun, adjective, action, or connector).
DISTRACTOR_FACT_ID_OVERRIDES: dict[str, tuple[str, str, str]] = {
    # DANIEL 7
    "DAN7-V004-F02": ("DAN7-V021-F01", "DAN7-V007-F05", "DAN7-V019-F03"),
    "DAN7-V005-F04": ("DAN7-V021-F01", "DAN7-V007-F05", "DAN7-V019-F03"),
    "DAN7-V005-F09": ("DAN11-V020-F07", "DAN8-V024-F07", "DAN9-V022-F08"),
    "DAN7-V006-F01": ("DAN7-V021-F01", "DAN7-V007-F05", "DAN7-V019-F03"),
    "DAN7-V008-F04": ("DAN7-V022-F03", "DAN10-V003-F03", "DAN10-V017-F05"),
    "DAN7-V008-F05": ("DAN7-V021-F01", "DAN7-V007-F05", "DAN7-V019-F03"),
    "DAN7-V013-F06": ("DAN8-V017-F08", "DAN8-V011-F07", "DAN7-V020-F09"),
    "DAN7-V014-F08": ("DAN8-V024-F07", "DAN9-V022-F08", "DAN8-V004-F12"),
    "DAN7-V019-F05": ("DAN1-V016-F02", "DAN4-V012-F02", "PR39-P028-P002-S001-F01"),
    "DAN7-V020-F04": ("DAN10-V017-F05", "DAN8-V003-F02", "DAN1-V015-F02"),
    "DAN7-V020-F09": ("DAN8-V017-F08", "DAN8-V011-F07", "DAN8-V012-F09"),
    "DAN7-V028-F05": ("DAN9-V005-F05", "DAN2-V028-F01", "DAN8-V027-F08"),
    "DAN7-V028-F07": (
        "DAN7-V015-F04",
        "PR39-P030-P006-S003-F01",
        "PR40-P035-P001-S002-F02",
    ),
    # DANIEL 8
    "DAN8-V002-F09": ("DAN8-V011-F07", "DAN8-V004-F07", "DAN3-V025-F02"),
    "DAN8-V003-F07": ("DAN8-V017-F08", "DAN8-V011-F07", "DAN8-V012-F09"),
    "DAN8-V004-F06": ("DAN8-V009-F03", "PR43-P047-P003-S003-F01", "DAN8-V002-F03"),
    "DAN8-V004-F11": ("DAN8-V009-F03", "PR43-P047-P003-S003-F01", "DAN8-V002-F03"),
    "DAN8-V004-F13": ("DAN8-V009-F03", "PR43-P047-P003-S003-F01", "DAN8-V002-F03"),
    "DAN8-V011-F05": (
        "DAN7-V020-F10",
        "DAN7-V014-F09",
        "PR40-P035-P008-S002-F02",
    ),
    "DAN8-V011-F07": ("DAN8-V002-F09", "DAN8-V004-F07", "DAN3-V025-F02"),
    "DAN8-V012-F09": (
        "PR39-P029-P006-S001-F02",
        "DAN8-V004-F07",
        "DAN6-V004-F04",
    ),
    "DAN8-V013-F08": (
        "DAN11-V031-F06",
        "DAN11-V041-F06",
        "PR42-P043-P003-S001-F03",
    ),
    "DAN8-V015-F08": ("DAN8-V017-F08", "DAN8-V011-F07", "DAN7-V020-F09"),
    "DAN8-V017-F04": (
        "DAN6-V013-F03",
        "PR40-P035-P001-S002-F02",
        "DAN7-V015-F04",
    ),
    "DAN8-V017-F08": ("DAN8-V015-F08", "DAN8-V011-F07", "DAN7-V020-F09"),
    "DAN8-V018-F05": ("DAN10-V019-F05", "DAN8-V027-F09", "DAN8-V017-F08"),
    "DAN8-V018-F08": (
        "DAN6-V013-F03",
        "PR40-P035-P001-S002-F02",
        "DAN7-V015-F04",
    ),
    "DAN8-V022-F02": ("DAN11-V030-F06", "DAN11-V006-F05", "DAN11-V014-F03"),
    "DAN8-V027-F05": ("DAN8-V018-F04", "DAN10-V016-F04", "PR42-P046-P001-S004-F03"),
    "DAN8-V027-F09": ("DAN10-V002-F03", "PR43-P051-P009-S001-F01", "PR43-P052-P004-S003-F01"),
}


# The contextual item is a subject in the masked sentence, not a predicate.
CONTEXTUAL_ROLE_OVERRIDES: dict[str, str] = {
    "DAN7-V006-F07": "subject",
}


# Short audit trail for maintainers and validators.  The source_quote and
# lexical category are intentionally resolved at runtime from fact_inventory.
DISTRACTOR_OVERRIDE_PROVENANCE: dict[str, dict[str, object]] = {
    fact_id: {
        "candidate_fact_ids": candidate_ids,
        "basis": "same slot category/valency; source_quote-backed inventory facts",
    }
    for fact_id, candidate_ids in DISTRACTOR_FACT_ID_OVERRIDES.items()
}


def validate_fact_ids(inventory_fact_ids: set[str]) -> None:
    """Raise if an override points outside the current inventory."""

    missing = sorted(
        {
            candidate
            for candidates in DISTRACTOR_FACT_ID_OVERRIDES.values()
            for candidate in candidates
            if candidate not in inventory_fact_ids
        }
        | {
            fact_id
            for fact_id in CONTEXTUAL_ROLE_OVERRIDES
            if fact_id not in inventory_fact_ids
        }
    )
    if missing:
        raise ValueError(f"Unknown DAN7/DAN8 override fact_id(s): {missing}")
