from __future__ import annotations
from dataclasses import dataclass, field as dataclass_field
import re
import string
from typing import Any, Dict, List, Optional

from rag.ontology_retrieve import OntologyCandidate

_ALLOWED_MATCH_TYPES = {"exact", "synonym", "jaccard", "none", "fallback"}
_ALLOWED_STATUSES = {
    "MATCHED",
    "NO_MATCH",
    "AMBIGUOUS",
    "LOW_CONFIDENCE",
    "INDEX_UNAVAILABLE",
    "FALLBACK",
}

_PUNCT_TABLE = str.maketrans({char: " " for char in string.punctuation})
_WS_RE = re.compile(r"\s+")
_MAX_ALTERNATES = 5


@dataclass(frozen=True)
class OntologyThresholds:
    min_confidence_to_accept: float = 0.80
    max_delta_for_ambiguity: float = 0.05


@dataclass(frozen=True)
class OntologyMatchAlternate:
    term_id: str
    label: str
    source: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term_id": self.term_id,
            "label": self.label,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class OntologyMatchResult:
    status: str
    best: Optional[OntologyMatchAlternate] = None
    alternates: List[OntologyMatchAlternate] = dataclass_field(default_factory=list)
    match_type: Optional[str] = None
    confidence: Optional[float] = None

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        if self.match_type and self.match_type not in _ALLOWED_MATCH_TYPES:
            raise ValueError(f"Invalid match_type: {self.match_type}")


@dataclass(frozen=True)
class OntologyMatch:
    field: str
    raw_value: str
    ontology: str
    status: str
    matched_term_id: Optional[str]
    matched_label: Optional[str]
    matched_source: Optional[str]
    match_type: Optional[str]
    score: Optional[float]
    alternates: List[Dict[str, Any]] = dataclass_field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        if self.match_type and self.match_type not in _ALLOWED_MATCH_TYPES:
            raise ValueError(f"Invalid match_type: {self.match_type}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "raw_value": self.raw_value,
            "ontology": self.ontology,
            "status": self.status,
            "matched_term_id": self.matched_term_id,
            "matched_label": self.matched_label,
            "matched_source": self.matched_source,
            "match_type": self.match_type,
            "score": self.score,
            "alternates": list(self.alternates),
        }


def thresholds_from_config(config: Optional[Dict[str, Any]]) -> OntologyThresholds:
    cfg = config.get("ontology_thresholds") if isinstance(config, dict) else None
    if not isinstance(cfg, dict):
        return OntologyThresholds()
    try:
        min_conf = float(cfg.get("min_confidence_to_accept", 0.80))
    except (TypeError, ValueError):
        min_conf = 0.80
    try:
        max_delta = float(cfg.get("max_delta_for_ambiguity", 0.05))
    except (TypeError, ValueError):
        max_delta = 0.05
    return OntologyThresholds(
        min_confidence_to_accept=min_conf,
        max_delta_for_ambiguity=max_delta,
    )


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.lower().translate(_PUNCT_TABLE)
    normalized = _WS_RE.sub(" ", normalized).strip()
    return normalized


def _tokenize(normalized_text: str) -> List[str]:
    if not normalized_text:
        return []
    return normalized_text.split()


def _jaccard(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a_set = set(a_tokens)
    b_set = set(b_tokens)
    intersection = a_set.intersection(b_set)
    union = a_set.union(b_set)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def choose_best_ontology_candidate(
    raw_value: str,
    candidates: List[OntologyCandidate],
    thresholds: OntologyThresholds,
) -> OntologyMatchResult:
    if not candidates:
        return OntologyMatchResult(status="NO_MATCH")

    normalized_raw = _normalize_text(raw_value)
    raw_tokens = _tokenize(normalized_raw)

    scored: List[tuple[float, int, str, OntologyCandidate]] = []
    for idx, candidate in enumerate(candidates):
        label = candidate.label or ""
        synonyms = candidate.synonyms or []
        normalized_label = _normalize_text(label)
        normalized_synonyms = [
            _normalize_text(item) for item in synonyms if isinstance(item, str)
        ]

        if normalized_raw and normalized_label == normalized_raw:
            confidence = 1.0
            match_type = "exact"
        elif normalized_raw and normalized_raw in normalized_synonyms:
            confidence = 0.98
            match_type = "synonym"
        else:
            label_score = _jaccard(raw_tokens, _tokenize(normalized_label))
            syn_score = 0.0
            for syn in normalized_synonyms:
                syn_score = max(syn_score, _jaccard(raw_tokens, _tokenize(syn)))
            confidence = max(label_score, syn_score)
            match_type = "jaccard"

        scored.append((confidence, idx, match_type, candidate))

    scored.sort(key=lambda item: (-item[0], item[1]))
    best_confidence, _, best_match_type, best_candidate = scored[0]

    alternates: List[OntologyMatchAlternate] = []
    for confidence, _, _, candidate in scored[:_MAX_ALTERNATES]:
        alternates.append(
            OntologyMatchAlternate(
                term_id=candidate.term_id,
                label=candidate.label,
                source=candidate.source,
                confidence=confidence,
            )
        )

    status = "MATCHED"
    if best_confidence < thresholds.min_confidence_to_accept:
        status = "LOW_CONFIDENCE"
    elif len(scored) > 1:
        second_confidence = scored[1][0]
        if (
            (best_confidence - second_confidence)
            <= thresholds.max_delta_for_ambiguity
            and second_confidence >= thresholds.min_confidence_to_accept
        ):
            status = "AMBIGUOUS"

    best = None
    match_type = None
    confidence = None
    if status == "MATCHED":
        best = OntologyMatchAlternate(
            term_id=best_candidate.term_id,
            label=best_candidate.label,
            source=best_candidate.source,
            confidence=best_confidence,
        )
        match_type = best_match_type
        confidence = best_confidence
    else:
        match_type = best_match_type
        confidence = best_confidence

    return OntologyMatchResult(
        status=status,
        best=best,
        alternates=alternates,
        match_type=match_type,
        confidence=confidence,
    )
