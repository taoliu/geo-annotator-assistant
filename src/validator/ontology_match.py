from __future__ import annotations
from dataclasses import dataclass, field as dataclass_field
import re
import string
from typing import Any, Dict, List, Optional

from rag.ontology_retrieve import OntologyCandidate

_ALLOWED_MATCH_TYPES = {
    "exact",
    "synonym",
    "label_exact",
    "synonym_exact",
    "jaccard",
    "none",
    "fallback",
}
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
_EXACT_PUNCT_RE = re.compile(r"[-_/,.:]")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")
_PREFIX_PATTERNS = [
    re.compile(r"^\s*[A-Za-z][A-Za-z0-9 _/\-]{0,40}\s*:\s*(.+)$"),
    re.compile(r"^\s*[A-Za-z][A-Za-z0-9 _/\-]{0,40}\s*=\s*(.+)$"),
    re.compile(r"^\s*[A-Za-z][A-Za-z0-9 _/\-]{0,40}\s+-\s+(.+)$"),
]
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
    matched_via: Optional[str] = None
    matched_synonym: Optional[str] = None

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
    matched_via: Optional[str] = None
    matched_synonym: Optional[str] = None

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
            "matched_via": self.matched_via,
            "matched_synonym": self.matched_synonym,
        }


def thresholds_from_config(config: Optional[Dict[str, Any]]) -> OntologyThresholds:
    cfg = None
    if isinstance(config, dict):
        ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else None
        if isinstance(ontology_cfg, dict):
            cfg = ontology_cfg.get("thresholds")
        if cfg is None:
            cfg = config.get("ontology_thresholds")
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


def clean_raw_value_for_ontology(raw_value: str) -> str:
    cleaned = (raw_value or "").strip()
    if not cleaned:
        return ""
    for pattern in _PREFIX_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            return match.group(1).strip()
    return cleaned


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.lower().translate(_PUNCT_TABLE)
    normalized = _WS_RE.sub(" ", normalized).strip()
    return normalized


def normalize_exact_match_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.strip().lower()
    normalized = _EXACT_PUNCT_RE.sub(" ", normalized)
    normalized = _NON_ALNUM_RE.sub(" ", normalized)
    normalized = _WS_RE.sub(" ", normalized).strip()
    return normalized


def _find_exact_synonym(normalized_raw: str, synonyms: List[str]) -> Optional[str]:
    if not normalized_raw:
        return None
    for synonym in synonyms:
        if not isinstance(synonym, str):
            continue
        if normalize_exact_match_text(synonym) == normalized_raw:
            return synonym
    return None


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

    cleaned_raw = clean_raw_value_for_ontology(raw_value)
    normalized_raw_exact = normalize_exact_match_text(cleaned_raw)
    normalized_raw = _normalize_text(cleaned_raw)
    raw_tokens = _tokenize(normalized_raw)

    scored: List[
        tuple[
            float,
            int,
            int,
            str,
            Optional[str],
            Optional[str],
            OntologyCandidate,
        ]
    ] = []
    for idx, candidate in enumerate(candidates):
        if raw_value == "CLL" and candidate.term_id == "DOID:1040":
            print("[DEBUG synonyms DOID:1040]", candidate.synonyms)

        label = candidate.label or ""
        synonyms = candidate.synonyms or []
        matched_via = None
        matched_synonym = None
        normalized_label_exact = normalize_exact_match_text(label)

        if normalized_raw_exact and normalized_label_exact == normalized_raw_exact:
            confidence = 1.0
            match_type = "label_exact"
            matched_via = "label"
        else:
            matched_synonym = _find_exact_synonym(normalized_raw_exact, synonyms)
            if matched_synonym is not None:
                confidence = 1.0
                match_type = "synonym_exact"
                matched_via = "synonym"
            else:
                normalized_label = _normalize_text(label)
                normalized_synonyms = [
                    _normalize_text(item) for item in synonyms if isinstance(item, str)
                ]
                label_score = _jaccard(raw_tokens, _tokenize(normalized_label))
                syn_score = 0.0
                for syn in normalized_synonyms:
                    syn_score = max(syn_score, _jaccard(raw_tokens, _tokenize(syn)))
                confidence = max(label_score, syn_score)
                match_type = "jaccard"

        match_rank = 2
        if match_type == "label_exact":
            match_rank = 0
        elif match_type == "synonym_exact":
            match_rank = 1
        scored.append(
            (
                confidence,
                match_rank,
                idx,
                match_type,
                matched_via,
                matched_synonym,
                candidate,
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    (
        best_confidence,
        _,
        _,
        best_match_type,
        best_matched_via,
        best_matched_synonym,
        best_candidate,
    ) = scored[0]

    alternates: List[OntologyMatchAlternate] = []
    for confidence, _, _, _, _, _, candidate in scored[:_MAX_ALTERNATES]:
        alternates.append(
            OntologyMatchAlternate(
                term_id=candidate.term_id,
                label=candidate.label,
                source=candidate.source,
                confidence=confidence,
            )
        )

    status = "MATCHED"
    if best_match_type in {"label_exact", "synonym_exact"}:
        if len(scored) > 1:
            second_confidence = scored[1][0]
            if (
                (best_confidence - second_confidence)
                <= thresholds.max_delta_for_ambiguity
                and second_confidence >= thresholds.min_confidence_to_accept
            ):
                status = "AMBIGUOUS"
    else:
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
    matched_via = None
    matched_synonym = None
    if status == "MATCHED":
        best = OntologyMatchAlternate(
            term_id=best_candidate.term_id,
            label=best_candidate.label,
            source=best_candidate.source,
            confidence=best_confidence,
        )
        match_type = best_match_type
        confidence = best_confidence
        matched_via = best_matched_via
        matched_synonym = best_matched_synonym
    else:
        match_type = best_match_type
        confidence = best_confidence

    return OntologyMatchResult(
        status=status,
        best=best,
        alternates=alternates,
        match_type=match_type,
        confidence=confidence,
        matched_via=matched_via,
        matched_synonym=matched_synonym,
    )
