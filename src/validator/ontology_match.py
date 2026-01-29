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
    "label_norm_exact",
    "synonym_exact",
    "term_id_exact",
    "jaccard",
    "token_equiv_similarity",
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
TERMINAL_EXACT_TYPES = {
    "label_exact",
    "label_norm_exact",
    "synonym_exact",
    "term_id_exact",
}


def is_terminal_exact(status: str, score: float, match_type: str) -> bool:
    return status == "MATCHED" and score == 1.0 and match_type in TERMINAL_EXACT_TYPES

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
    original_confidence: Optional[float] = None
    token_equiv_confidence: Optional[float] = None
    token_equiv_class: Optional[List[str]] = None
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
    original_score: Optional[float] = None
    token_equiv_score: Optional[float] = None
    token_equiv_class: Optional[List[str]] = None
    alternates: List[Dict[str, Any]] = dataclass_field(default_factory=list)
    matched_via: Optional[str] = None
    matched_synonym: Optional[str] = None
    vector_fallback_skipped: Optional[bool] = None
    query_used: Optional[str] = None
    ncit_fallback_enabled: Optional[bool] = None
    ncit_triggered: Optional[bool] = None
    ncit_trigger_terms_used: Optional[List[str]] = None
    attempted_sources: Optional[List[str]] = None
    selected_source: Optional[str] = None
    selection_rule: Optional[str] = None

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
            "original_score": self.original_score,
            "token_equiv_score": self.token_equiv_score,
            "token_equiv_class": (
                list(self.token_equiv_class) if self.token_equiv_class is not None else None
            ),
            "alternates": list(self.alternates),
            "matched_via": self.matched_via,
            "matched_synonym": self.matched_synonym,
            "vector_fallback_skipped": self.vector_fallback_skipped,
            "query_used": self.query_used,
            "ncit_fallback_enabled": self.ncit_fallback_enabled,
            "ncit_triggered": self.ncit_triggered,
            "ncit_trigger_terms_used": (
                list(self.ncit_trigger_terms_used)
                if self.ncit_trigger_terms_used is not None
                else None
            ),
            "attempted_sources": (
                list(self.attempted_sources) if self.attempted_sources is not None else None
            ),
            "selected_source": self.selected_source,
            "selection_rule": self.selection_rule,
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


def _singularize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 3:
        return f"{token[:-3]}y"
    if token.endswith("es") and len(token) > 2:
        return token[:-2]
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def _pluralize_token(token: str) -> str:
    if not token:
        return token
    if token.endswith("y") and len(token) > 2 and token[-2] not in "aeiou":
        return f"{token[:-1]}ies"
    if token.endswith(("s", "x", "z", "ch", "sh")):
        return f"{token}es"
    return f"{token}s"


def _expand_exact_variants(normalized_raw: str) -> set[str]:
    variants: set[str] = set()
    if not normalized_raw:
        return variants
    variants.add(normalized_raw)
    tokens = _tokenize(normalized_raw)
    if not tokens:
        return variants
    last = tokens[-1]
    singular = _singularize_token(last)
    plural = _pluralize_token(last)
    for variant in {singular, plural}:
        if variant and variant != last:
            variants.add(" ".join(tokens[:-1] + [variant]))
    return variants


def _find_exact_synonym(
    normalized_raw_variants: set[str],
    synonyms: List[str],
) -> Optional[str]:
    if not normalized_raw_variants:
        return None
    for synonym in synonyms:
        if not isinstance(synonym, str):
            continue
        if normalize_exact_match_text(synonym) in normalized_raw_variants:
            return synonym
    return None


def _tokenize(normalized_text: str) -> List[str]:
    if not normalized_text:
        return []
    return normalized_text.split()


def _apply_token_equivalence(
    tokens: List[str],
    equivalence_map: Optional[Dict[str, str]],
) -> tuple[List[str], set[str]]:
    if not tokens or not equivalence_map:
        return tokens, set()
    normalized_tokens: List[str] = []
    used: set[str] = set()
    for token in tokens:
        mapped = equivalence_map.get(token, token)
        normalized_tokens.append(mapped)
        if token in equivalence_map:
            used.add(mapped)
    return normalized_tokens, used


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
    *,
    token_equivalence: Optional[Dict[str, str]] = None,
) -> OntologyMatchResult:
    if not candidates:
        return OntologyMatchResult(status="NO_MATCH")

    cleaned_raw = clean_raw_value_for_ontology(raw_value)
    normalized_raw_exact = normalize_exact_match_text(cleaned_raw)
    normalized_raw_variants = _expand_exact_variants(normalized_raw_exact)
    normalized_raw = _normalize_text(cleaned_raw)
    raw_tokens = _tokenize(normalized_raw)
    equiv_raw_tokens, raw_equiv_used = _apply_token_equivalence(raw_tokens, token_equivalence)

    scored: List[
        tuple[
            float,
            int,
            int,
            str,
            Optional[str],
            Optional[str],
            Optional[float],
            Optional[float],
            Optional[List[str]],
            OntologyCandidate,
        ]
    ] = []
    for idx, candidate in enumerate(candidates):
        label = candidate.label or ""
        synonyms = candidate.synonyms or []
        matched_via = None
        matched_synonym = None
        normalized_label_exact = normalize_exact_match_text(label)

        original_confidence = None
        token_equiv_confidence = None
        token_equiv_class = None
        if candidate.retrieval_mode == "meta_exact":
            confidence = 1.0
            match_type = "label_norm_exact"
            matched_via = "label_norm"
        elif normalized_label_exact and normalized_label_exact in normalized_raw_variants:
            confidence = 1.0
            match_type = "label_exact"
            matched_via = "label"
        else:
            matched_synonym = _find_exact_synonym(normalized_raw_variants, synonyms)
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
                original_confidence = confidence

                if token_equivalence:
                    label_tokens = _tokenize(normalized_label)
                    equiv_label_tokens, label_equiv_used = _apply_token_equivalence(
                        label_tokens,
                        token_equivalence,
                    )
                    label_equiv_score = _jaccard(equiv_raw_tokens, equiv_label_tokens)
                    syn_equiv_score = 0.0
                    syn_equiv_used: set[str] = set()
                    for syn in normalized_synonyms:
                        syn_tokens = _tokenize(syn)
                        equiv_syn_tokens, syn_used = _apply_token_equivalence(
                            syn_tokens,
                            token_equivalence,
                        )
                        score = _jaccard(equiv_raw_tokens, equiv_syn_tokens)
                        if score > syn_equiv_score:
                            syn_equiv_score = score
                            syn_equiv_used = syn_used
                    token_equiv_score = max(label_equiv_score, syn_equiv_score)
                    equiv_used = set(raw_equiv_used)
                    if token_equiv_score == label_equiv_score:
                        equiv_used |= label_equiv_used
                    else:
                        equiv_used |= syn_equiv_used
                    if equiv_used:
                        token_equiv_confidence = token_equiv_score
                        token_equiv_class = sorted(equiv_used)
                    if token_equiv_score > confidence:
                        confidence = token_equiv_score
                        match_type = "token_equiv_similarity"

        match_rank = 2
        if match_type in {"label_exact", "label_norm_exact"}:
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
                original_confidence,
                token_equiv_confidence,
                token_equiv_class,
                candidate,
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    exact_tie_resolved = False
    best_confidence, best_match_rank = scored[0][0], scored[0][1]
    if (
        best_confidence == 1.0
        and scored[0][3] in {"label_exact", "label_norm_exact", "synonym_exact"}
    ):
        tied = [
            item
            for item in scored
            if item[0] == 1.0 and item[1] == best_match_rank
        ]
        if len(tied) > 1:
            def _specificity_key(item) -> tuple[int, int, int]:
                label_text = item[9].label or ""
                normalized_label = normalize_exact_match_text(label_text)
                tokens = _tokenize(normalized_label)
                return (len(tokens), len(normalized_label), -item[2])

            tied_sorted = sorted(
                tied,
                key=_specificity_key,
                reverse=True,
            )
            others = [item for item in scored if item not in tied]
            scored = tied_sorted + others
            exact_tie_resolved = True
    (
        best_confidence,
        _,
        _,
        best_match_type,
        best_matched_via,
        best_matched_synonym,
        best_original_confidence,
        best_token_equiv_confidence,
        best_token_equiv_class,
        best_candidate,
    ) = scored[0]

    alternates: List[OntologyMatchAlternate] = []
    for confidence, _, _, _, _, _, _, _, _, candidate in scored[:_MAX_ALTERNATES]:
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
        if len(scored) > 1 and not exact_tie_resolved:
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
        original_confidence=best_original_confidence,
        token_equiv_confidence=best_token_equiv_confidence,
        token_equiv_class=best_token_equiv_class,
        matched_via=matched_via,
        matched_synonym=matched_synonym,
    )
