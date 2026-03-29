from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "artnet_output_stats.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("artnet_output_stats", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def _audit_record(
    *,
    gse: str,
    gsm: str,
    final_decision: str,
    n_llm_calls: int,
    flags: list[str] | None = None,
    primary_failure: str | None = None,
    repair_history: list[dict] | None = None,
    terminal_fallback_fields: list[str] | None = None,
    canonicalizations: list[dict] | None = None,
    ontology_status_by_field: dict[str, str] | None = None,
    ontology_matches: dict[str, dict] | None = None,
    llm_cache_hits: list[bool] | None = None,
) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "final_decision": final_decision,
        "flags": flags or [],
        "repair_history": repair_history or [],
        "canonicalizations": canonicalizations or [],
        "validation": {
            "ontology_matches": ontology_matches or {},
        },
        "rationale": {
            "final_decision": final_decision,
            "primary_failure": primary_failure,
            "terminal_fallback_fields": terminal_fallback_fields or [],
            "n_llm_calls": n_llm_calls,
            "ontology_status_by_field": ontology_status_by_field or {},
            "flags": flags or [],
        },
        "llm_cache_hits": llm_cache_hits or [],
    }


def _evidence_record(*, gse: str, gsm: str, evidence_by_field: dict) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "evidence_by_field": evidence_by_field,
    }


def test_aggregate_output_dir_counts_requested_metrics(tmp_path: Path) -> None:
    module = _load_module()
    out_dir = tmp_path / "out" / "artnet"

    _write_jsonl(
        out_dir / "GSE100" / "audit.jsonl",
        [
            _audit_record(
                gse="GSE100",
                gsm="GSM1",
                final_decision="ACCEPT",
                n_llm_calls=1,
                canonicalizations=[
                    {
                        "field": "tissue_type",
                        "original_value": "Blood",
                        "canonical_value": "blood",
                        "term_id": "UBERON:0000178",
                        "source": "Uberon Ontology",
                        "match_type": "label_norm_exact",
                    }
                ],
                ontology_status_by_field={"tissue_type": "MATCHED", "disease": "FALLBACK"},
                ontology_matches={
                    "tissue_type": {
                        "status": "MATCHED",
                        "match_type": "label_norm_exact",
                    }
                },
                llm_cache_hits=[False],
            ),
            _audit_record(
                gse="GSE100",
                gsm="GSM2",
                final_decision="FLAGGED",
                n_llm_calls=3,
                flags=["ontology_low_confidence_cell_line", "gse_outlier_cell_line"],
                primary_failure="ontology_low_confidence_cell_line",
                repair_history=[
                    {
                        "failure_code": "ontology_low_confidence_cell_line",
                        "field": "cell_line",
                        "repair_template": "repair_ontology_guided_v1",
                        "output_updated": True,
                    },
                    {
                        "failure_code": "ontology_low_confidence_cell_line",
                        "field": "cell_line",
                        "repair_template": "repair_ontology_guided_v1",
                        "output_updated": True,
                    },
                ],
                canonicalizations=[
                    {
                        "field": "disease",
                        "original_value": "Chronic Myelogenous Leukemia",
                        "canonical_value": "chronic myeloid leukemia",
                        "term_id": "DOID:8552",
                        "source": "Human Disease Ontology",
                        "match_type": "synonym_norm_exact",
                    }
                ],
                ontology_status_by_field={"cell_line": "LOW_CONFIDENCE", "disease": "MATCHED"},
                ontology_matches={
                    "disease": {
                        "status": "MATCHED",
                        "match_type": "synonym_norm_exact",
                    },
                    "cell_line": {
                        "status": "LOW_CONFIDENCE",
                        "match_type": "jaccard",
                    },
                },
                llm_cache_hits=[False, True, False],
            ),
        ],
    )
    _write_jsonl(
        out_dir / "GSE100" / "evidence.jsonl",
        [
            _evidence_record(
                gse="GSE100",
                gsm="GSM1",
                evidence_by_field={
                    "tissue_type": {"flags": [], "attempts": 0, "terminal_fallback": False},
                    "disease": {"flags": [], "attempts": 0, "terminal_fallback": False},
                },
            ),
            _evidence_record(
                gse="GSE100",
                gsm="GSM2",
                evidence_by_field={
                    "cell_line": {
                        "flags": ["ontology_low_confidence_cell_line"],
                        "attempts": 2,
                        "terminal_fallback": False,
                    },
                    "disease": {"flags": [], "attempts": 0, "terminal_fallback": False},
                },
            ),
        ],
    )
    _write_jsonl(
        out_dir / "GSE100" / "suggestions.jsonl",
        [
            {
                "scope": "GSE",
                "gse_accession": "GSE100",
                "gsm_accession": "GSM2",
                "field": "cell_line",
                "reason": "singletons_within_gse",
            }
        ],
    )

    _write_jsonl(
        out_dir / "GSE200" / "audit.jsonl",
        [
            _audit_record(
                gse="GSE200",
                gsm="GSM3",
                final_decision="ACCEPT",
                n_llm_calls=2,
                flags=["treatment_not_an_intervention"],
                repair_history=[
                    {
                        "failure_code": "treatment_identity_leakage",
                        "field": "treatment",
                        "fallback_value": "None",
                    }
                ],
                terminal_fallback_fields=["treatment"],
                ontology_status_by_field={"tissue_type": "FALLBACK", "disease": "FALLBACK"},
                ontology_matches={
                    "data_type": {
                        "status": "MATCHED",
                        "match_type": "jaccard",
                    }
                },
                llm_cache_hits=[False, False],
            )
        ],
    )
    _write_jsonl(
        out_dir / "GSE200" / "evidence.jsonl",
        [
            _evidence_record(
                gse="GSE200",
                gsm="GSM3",
                evidence_by_field={
                    "treatment": {
                        "flags": ["treatment_not_an_intervention"],
                        "attempts": 1,
                        "terminal_fallback": True,
                    }
                },
            )
        ],
    )
    _write_jsonl(
        out_dir / "GSE200" / "suggestions.jsonl",
        [
            {
                "scope": "GSE",
                "gse_accession": "GSE200",
                "gsm_accession": "GSM3",
                "field": "disease",
                "reason": "value_outlier_within_gse",
            }
        ],
    )

    stats = module.aggregate_output_dir(out_dir)

    assert stats["gse_dirs_discovered"] == 2
    assert stats["gse_dirs_processed"] == 2
    assert stats["gse_dirs_skipped"] == 0
    assert stats["gsm_records"] == 3
    assert stats["flagged_gsms"] == 1
    assert stats["final_decisions"] == {"ACCEPT": 2, "FLAGGED": 1}

    assert stats["llm"]["total_calls"] == 6
    assert stats["llm"]["proposal_calls"] == 3
    assert stats["llm"]["repair_calls"] == 3
    assert stats["llm"]["cache_hits"] == 1
    assert stats["llm"]["uncached_calls"] == 5
    assert stats["llm"]["max_calls_for_single_gsm"] == 3

    assert stats["repairs"]["gsms_with_any_repair_activity"] == 2
    assert stats["repairs"]["gsms_with_llm_repair_attempts"] == 1
    assert stats["repairs"]["gsms_with_deterministic_fallbacks"] == 1
    assert stats["repairs"]["repaired_then_accepted"] == 1
    assert stats["repairs"]["repaired_then_flagged"] == 1
    assert stats["repairs"]["llm_repair_then_accepted"] == 0
    assert stats["repairs"]["llm_repair_then_flagged"] == 1
    assert stats["repairs"]["fallback_only_then_accepted"] == 1
    assert stats["repairs"]["fallback_only_then_flagged"] == 0
    assert stats["repairs"]["salvage_only_then_accepted"] == 0
    assert stats["repairs"]["salvage_only_then_flagged"] == 0
    assert stats["repairs"]["repair_history_events"] == 3
    assert stats["repairs"]["llm_repair_events"] == 2
    assert stats["repairs"]["fallback_events"] == 1
    assert stats["repairs"]["events_by_field"] == {"cell_line": 2, "treatment": 1}
    assert stats["repairs"]["fallbacks_by_field"] == {"treatment": 1}

    assert stats["ontology"]["gsms_with_ontology_canonicalization"] == 2
    assert stats["ontology"]["gsms_with_changed_ontology_canonicalization"] == 2
    assert stats["ontology"]["canonicalization_events"] == 2
    assert stats["ontology"]["changed_value_events"] == 2
    assert stats["ontology"]["canonicalizations_by_field"] == {"disease": 1, "tissue_type": 1}
    assert stats["ontology"]["canonicalizations_by_match_type"] == {
        "label_norm_exact": 1,
        "synonym_norm_exact": 1,
    }
    assert stats["ontology"]["matched_routes"] == {
        "exact_label_or_id": 1,
        "exact_synonym": 1,
        "semantic_threshold": 1,
    }
    assert stats["ontology"]["matched_routes_by_field"] == {
        "data_type": {"semantic_threshold": 1},
        "disease": {"exact_synonym": 1},
        "tissue_type": {"exact_label_or_id": 1},
    }
    assert stats["ontology"]["status_by_field"]["disease"] == {"FALLBACK": 2, "MATCHED": 1}

    assert stats["terminal_fallbacks"] == {
        "gsms_with_terminal_fallbacks": 1,
        "events": 1,
        "by_field": {"treatment": 1},
    }

    assert stats["top_level_flags"] == {
        "gse_outlier_cell_line": 1,
        "ontology_low_confidence_cell_line": 1,
        "treatment_not_an_intervention": 1,
    }
    assert stats["primary_failures"] == {"ontology_low_confidence_cell_line": 1}

    assert stats["field_diagnostics"]["gsms_with_any_field_flags"] == 2
    assert stats["field_diagnostics"]["flagged_field_cells"] == 2
    assert stats["field_diagnostics"]["flag_events"] == 2
    assert stats["field_diagnostics"]["flagged_cells_by_field"] == {
        "cell_line": 1,
        "treatment": 1,
    }
    assert stats["field_diagnostics"]["flag_names"] == {
        "ontology_low_confidence_cell_line": 1,
        "treatment_not_an_intervention": 1,
    }

    assert stats["gse_advisory"] == {
        "suggestion_events": 2,
        "suggestions_by_reason": {
            "singletons_within_gse": 1,
            "value_outlier_within_gse": 1,
        },
        "suggestions_by_field": {
            "cell_line": 1,
            "disease": 1,
        },
        "gse_outlier_flags_by_field": {
            "cell_line": 1,
        },
    }


def test_format_text_summary_includes_requested_headline_metrics(tmp_path: Path) -> None:
    module = _load_module()
    out_dir = tmp_path / "out" / "artnet"
    _write_jsonl(
        out_dir / "GSE300" / "audit.jsonl",
        [
            _audit_record(
                gse="GSE300",
                gsm="GSM9",
                final_decision="FLAGGED",
                n_llm_calls=2,
                flags=["ontology_low_confidence_disease"],
                primary_failure="ontology_low_confidence_disease",
                repair_history=[
                    {
                        "failure_code": "ontology_low_confidence_disease",
                        "field": "disease",
                        "repair_template": "repair_ontology_guided_v1",
                    }
                ],
            )
        ],
    )

    summary = module.format_text_summary(module.aggregate_output_dir(out_dir))

    assert "ARTNet Output Statistics" in summary
    assert "flagged_gsms: 1" in summary
    assert "total_calls: 2" in summary
    assert "gsms_with_any_repair_activity: 1" in summary
    assert "repaired_then_flagged: 1" in summary
