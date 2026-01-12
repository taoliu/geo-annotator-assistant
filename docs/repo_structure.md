.
├── AGENTS.md
├── config
│   ├── example_config.yaml
│   └── gat-llama3-3b-it_config.yaml
├── docs
│   ├── checkpoints
│   │   ├── 2026-01-02_checkpoint.md
│   │   ├── 2026-01-04_checkpoint.md
│   │   ├── 2026-01-05_checkpoint.md
│   │   ├── 2026-01-06_checkpoint.md
│   │   ├── 2026-01-07_checkpoint.md
│   │   ├── 2026-01-08_checkpoint.md
│   │   └── 2026-01-09_checkpoint.md
│   ├── milestones
│   │   ├── v0.1-llm.md
│   │   ├── v0.2-ontology-grounding.md
│   │   ├── v0.3-real-world-refinement.md
│   │   ├── v0.4-curation-backend.md
│   │   ├── v0.5-curator-ui.md
│   │   └── v0.6-rag-validation.md
│   ├── repo_structure.md
│   ├── RESUME.md
│   ├── tickets
│   │   ├── README.md
│   │   ├── ticket-1.md
│   │   ├── ticket-10.md
│   │   ├── ticket-11.md
│   │   ├── ticket-12.md
│   │   ├── ticket-13.md
│   │   ├── ticket-14.md
│   │   ├── ticket-15.md
│   │   ├── ticket-16.md
│   │   ├── ticket-16b.md
│   │   ├── ticket-17.md
│   │   ├── ticket-17b.md
│   │   ├── ticket-17c.md
│   │   ├── ticket-17d.md
│   │   ├── ticket-18.md
│   │   ├── ticket-19.md
│   │   ├── ticket-2.md
│   │   ├── ticket-20.md
│   │   ├── ticket-20b.md
│   │   ├── ticket-20c.md
│   │   ├── ticket-21.md
│   │   ├── ticket-22.md
│   │   ├── ticket-23.md
│   │   ├── ticket-24.md
│   │   ├── ticket-25.md
│   │   ├── ticket-26.md
│   │   ├── ticket-27.md
│   │   ├── ticket-28.md
│   │   ├── ticket-29.md
│   │   ├── ticket-3.md
│   │   ├── ticket-30.md
│   │   ├── ticket-31.md
│   │   ├── ticket-32.md
│   │   ├── ticket-33.md
│   │   ├── ticket-34.md
│   │   ├── ticket-35.md
│   │   ├── ticket-36.md
│   │   ├── ticket-37.md
│   │   ├── ticket-38.md
│   │   ├── ticket-39.md
│   │   ├── ticket-4.md
│   │   ├── ticket-40.md
│   │   ├── ticket-41.md
│   │   ├── ticket-42.md
│   │   ├── ticket-43.md
│   │   ├── ticket-44.md
│   │   ├── ticket-45.md
│   │   ├── ticket-46.md
│   │   ├── ticket-47.md
│   │   ├── ticket-48.md
│   │   ├── ticket-49.md
│   │   ├── ticket-5.md
│   │   ├── ticket-50.md
│   │   ├── ticket-51.md
│   │   ├── ticket-52.md
│   │   ├── ticket-53.md
│   │   ├── ticket-54.md
│   │   ├── ticket-55.md
│   │   ├── ticket-6.md
│   │   ├── ticket-7.md
│   │   ├── ticket-8.md
│   │   └── ticket-9.md
│   ├── ui.md
│   └── whitepaper.md
├── LICENSE
├── prompts
│   ├── label_v1.txt
│   ├── repair_cell_line_evidence_v1.txt
│   ├── repair_data_type_from_context_v1.txt
│   ├── repair_disease_evidence_v1.txt
│   ├── repair_disease_from_context_v1.txt
│   ├── repair_format_v1.txt
│   ├── repair_ontology_guided_v1.txt
│   └── repair_tissue_anatomy_v1.txt
├── pyproject.toml
├── README.md
├── spec
│   ├── decision_table.yaml
│   └── heuristics.yaml
├── src
│   ├── agent
│   │   ├── __init__.py
│   │   ├── accession.py
│   │   ├── audit.py
│   │   ├── cli.py
│   │   ├── config.py
│   │   ├── gse_postpass.py
│   │   ├── ontology_canonicalization.py
│   │   ├── overrides.py
│   │   ├── prompts.py
│   │   ├── repair_loop.py
│   │   ├── run_batch.py
│   │   ├── run_gse.py
│   │   ├── run_single.py
│   │   ├── state.py
│   │   ├── suggestions.py
│   │   └── writer.py
│   ├── ingest
│   │   ├── construct_prompt.py
│   │   ├── gse_soft_fetcher.py
│   │   ├── gse_soft_parser.py
│   │   ├── read_context_jsonl.py
│   │   ├── soft_to_context_jsonl.py
│   │   └── utils.py
│   ├── llm
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── http_utils.py
│   │   ├── llama_cpp_http.py
│   │   ├── local_transformers.py
│   │   ├── openai_http.py
│   │   └── text_postprocess.py
│   ├── rag
│   │   ├── __init__.py
│   │   ├── candidate.py
│   │   ├── chroma_client.py
│   │   ├── ontology_retrieve.py
│   │   ├── retrieve.py
│   │   └── version.py
│   ├── ui
│   │   ├── __init__.py
│   │   ├── app_streamlit.py
│   │   ├── cli.py
│   │   ├── flags.py
│   │   ├── loaders.py
│   │   ├── overrides.py
│   │   ├── paths.py
│   │   ├── schema.py
│   │   ├── state.py
│   │   └── styling.py
│   └── validator
│       ├── __init__.py
│       ├── cell_line_rules.py
│       ├── consistency_validator.py
│       ├── decision_engine.py
│       ├── failure_codes.py
│       ├── format_validator.py
│       ├── grounders
│       │   ├── __init__.py
│       │   ├── cell_line.py
│       │   ├── data_type.py
│       │   ├── disease.py
│       │   ├── ontology_grounder.py
│       │   └── tissue_type.py
│       ├── heuristics.py
│       ├── ontology_match.py
│       ├── ontology_validator.py
│       ├── semantic_validator.py
│       └── thresholds.py
├── tests
│   ├── README.md
│   ├── test_cell_line_type_guard.py
│   ├── test_chroma_embedding_device_config.py
│   ├── test_cli_and_batch.py
│   ├── test_config_llm_schema.py
│   ├── test_config_postpass_schema.py
│   ├── test_config_rag_schema.py
│   ├── test_consistency_decision_routing.py
│   ├── test_consistency_validator.py
│   ├── test_decision_engine.py
│   ├── test_disease_ncit_trigger_configurable.py
│   ├── test_failure_codes_evidence_first.py
│   ├── test_format_repair_extraction.py
│   ├── test_format_validator.py
│   ├── test_gse_consistency_postpass.py
│   ├── test_gse_jsonl_path.py
│   ├── test_gse_soft_ingest.py
│   ├── test_heuristics_loading.py
│   ├── test_http_retry_policy.py
│   ├── test_llm_interface_stubbed.py
│   ├── test_llm_repair_loops.py
│   ├── test_llm_reuse.py
│   ├── test_llm_stop_trimming.py
│   ├── test_llm_transport_factory.py
│   ├── test_local_transformers_generation_args.py
│   ├── test_ontology_canonicalize_and_lock.py
│   ├── test_ontology_chroma_grounding.py
│   ├── test_ontology_chroma_normalized_metadata_query.py
│   ├── test_ontology_chroma_runtime_query.py
│   ├── test_ontology_clean_raw_value.py
│   ├── test_ontology_exact_label_fallback.py
│   ├── test_ontology_match_scoring_exact_norm.py
│   ├── test_ontology_synonym_matching.py
│   ├── test_ontology_synonym_propagation.py
│   ├── test_openai_http_transport.py
│   ├── test_overrides_apply.py
│   ├── test_overrides_loader.py
│   ├── test_repair_inferred_without_evidence.py
│   ├── test_repair_loop.py
│   ├── test_run_single_stub.py
│   ├── test_semantic_validator.py
│   ├── test_state_and_audit.py
│   ├── test_suggestions.py
│   ├── test_terminal_exact_short_circuit.py
│   ├── test_thresholds_and_ontology_validator.py
│   ├── test_writer.py
│   └── ui
│       ├── test_cli.py
│       ├── test_flags.py
│       ├── test_loaders.py
│       ├── test_overrides.py
│       └── test_state.py
└── uv.lock

18 directories, 210 files
