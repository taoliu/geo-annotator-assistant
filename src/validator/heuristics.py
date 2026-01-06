from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_HEURISTICS: Dict[str, Dict[str, Any]] = {
    "semantic": {
        "tissue_cell_keywords": [
            "cell",
            "cells",
            "fibroblast",
            "fibroblasts",
            "macrophage",
            "epithelial",
            "lymphocyte",
            "t cell",
            "b cell",
        ],
        "tissue_cell_suffixes": [
            "cells",
            "cell",
            "fibroblast",
            "fibroblasts",
            "macrophage",
            "epithelial",
            "lymphocyte",
            "neuron",
        ],
        "treatment_identity_keywords": ["cell", "cells"],
        "treatment_genotype_keywords": [
            "ko",
            "knockout",
            "transgenic",
            "+/+",
            "+/-",
            "-/-",
            "cre",
        ],
        "treatment_tissue_keywords": ["liver", "brain", "blood", "intestine"],
        "disease_cues": [
            "disease",
            "tumor",
            "cancer",
            "carcinoma",
            "leukemia",
            "lymphoma",
            "infection",
            "patient",
            "diagnos",
        ],
    },
    "consistency": {
        "single_cell_data_types": ["scRNA-seq", "snRNA-seq", "scATAC-seq", "snATAC-seq"],
        "single_cell_keywords": [
            "single cell",
            "single-cell",
            "single nucleus",
            "single-nucleus",
            "10x",
            "chromium",
            "drop-seq",
            "smart-seq",
        ],
        "microarray_data_type": "Microarray",
        "sequencing_keywords": [
            "rna-seq",
            "atac-seq",
            "chip-seq",
            "nextseq",
            "novaseq",
            "hiseq",
            "miseq",
            "sequencing",
        ],
        "healthy_value": "Healthy",
        "disease_keywords": [
            "tumor",
            "cancer",
            "carcinoma",
            "leukemia",
            "lymphoma",
            "disease:",
        ],
        "organism_conflicts": [
            ["Mus musculus", "Homo sapiens"],
        ],
    },
}

_HEURISTICS_CACHE: Dict[str, Dict[str, Any]] = {}


def _ensure_list_of_strings(value: Any, label: str, path: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Heuristics at {path} expects '{label}' to be a list of strings.")


def _validate_organism_conflicts(value: Any, path: str) -> None:
    if not isinstance(value, list):
        raise ValueError(
            f"Heuristics at {path} expects 'organism_conflicts' to be a list of pairs."
        )
    for pair in value:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or not all(isinstance(item, str) for item in pair)
        ):
            raise ValueError(
                f"Heuristics at {path} expects 'organism_conflicts' pairs of two strings."
            )


def _validate_heuristics(data: Any, path: str) -> Dict[str, Dict[str, Any]]:
    if not isinstance(data, dict):
        raise ValueError(f"Heuristics at {path} must be a mapping.")

    semantic = data.get("semantic")
    if not isinstance(semantic, dict):
        raise ValueError(f"Heuristics at {path} missing 'semantic' section.")
    _ensure_list_of_strings(semantic.get("tissue_cell_keywords"), "tissue_cell_keywords", path)
    _ensure_list_of_strings(semantic.get("tissue_cell_suffixes"), "tissue_cell_suffixes", path)
    _ensure_list_of_strings(
        semantic.get("treatment_identity_keywords"), "treatment_identity_keywords", path
    )
    _ensure_list_of_strings(
        semantic.get("treatment_genotype_keywords"), "treatment_genotype_keywords", path
    )
    _ensure_list_of_strings(
        semantic.get("treatment_tissue_keywords"), "treatment_tissue_keywords", path
    )
    _ensure_list_of_strings(semantic.get("disease_cues"), "disease_cues", path)

    consistency = data.get("consistency")
    if not isinstance(consistency, dict):
        raise ValueError(f"Heuristics at {path} missing 'consistency' section.")
    _ensure_list_of_strings(
        consistency.get("single_cell_data_types"), "single_cell_data_types", path
    )
    _ensure_list_of_strings(
        consistency.get("single_cell_keywords"), "single_cell_keywords", path
    )
    if not isinstance(consistency.get("microarray_data_type"), str):
        raise ValueError(f"Heuristics at {path} expects 'microarray_data_type' to be a string.")
    _ensure_list_of_strings(
        consistency.get("sequencing_keywords"), "sequencing_keywords", path
    )
    if not isinstance(consistency.get("healthy_value"), str):
        raise ValueError(f"Heuristics at {path} expects 'healthy_value' to be a string.")
    _ensure_list_of_strings(consistency.get("disease_keywords"), "disease_keywords", path)
    _validate_organism_conflicts(consistency.get("organism_conflicts"), path)

    return data


def load_heuristics(path: str = "spec/heuristics.yaml") -> Dict[str, Dict[str, Any]]:
    """Load heuristics from a YAML file, raising ValueError on missing/invalid data."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"Heuristics file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid heuristics YAML: {path}") from exc
    if data is None:
        raise ValueError(f"Heuristics file is empty: {path}")
    return _validate_heuristics(data, path)


def get_heuristics(path: str = "spec/heuristics.yaml") -> Dict[str, Dict[str, Any]]:
    """Return cached heuristics, falling back to DEFAULT_HEURISTICS if the file is missing."""
    cache_key = str(Path(path))
    cached = _HEURISTICS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        heuristics = load_heuristics(path)
    except ValueError as exc:
        if isinstance(exc.__cause__, FileNotFoundError):
            heuristics = DEFAULT_HEURISTICS
        else:
            raise
    _HEURISTICS_CACHE[cache_key] = heuristics
    return heuristics
