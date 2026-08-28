"""Curated, source-backed exceptions found by the semantic AI audit."""

from __future__ import annotations

from scripts.lib.distractor_overrides_dan4_6 import (
    CONTEXTUAL_ROLE_OVERRIDES as DAN4_6_ROLE_OVERRIDES,
    DISTRACTOR_FACT_ID_OVERRIDES as DAN4_6_DISTRACTOR_OVERRIDES,
)
from scripts.lib.distractor_overrides_dan7_8 import (
    CONTEXTUAL_ROLE_OVERRIDES as DAN7_8_ROLE_OVERRIDES,
    DISTRACTOR_FACT_ID_OVERRIDES as DAN7_8_DISTRACTOR_OVERRIDES,
)
from scripts.lib.distractor_overrides_pr41_42 import (
    DISTRACTOR_FACT_ID_OVERRIDES as PR41_42_DISTRACTOR_OVERRIDES,
)


DISTRACTOR_FACT_ID_OVERRIDES = {
    **DAN4_6_DISTRACTOR_OVERRIDES,
    **DAN7_8_DISTRACTOR_OVERRIDES,
    **PR41_42_DISTRACTOR_OVERRIDES,
}
CONTEXTUAL_ROLE_OVERRIDES = {
    **DAN4_6_ROLE_OVERRIDES,
    **DAN7_8_ROLE_OVERRIDES,
}


__all__ = ["DISTRACTOR_FACT_ID_OVERRIDES", "CONTEXTUAL_ROLE_OVERRIDES"]
