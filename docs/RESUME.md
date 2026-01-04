# How to Resume This Project

1. Read `docs/whitepaper.md` for architecture.
2. Read the latest file in `docs/milestones/`.
3. Read the latest file in `docs/checkpoints/`.
4. Check the latest git tag.
5. Continue from the next planned milestone.

Ontology grounding setup:

1. Place `ontology_chroma_db/` next to the repo (must include `chroma.sqlite3`).
2. Enable `ontology_chroma_enabled: true` in your config.
3. Ensure embeddings match `BAAI/bge-base-en-v1.5` with `ontology_embedding_normalize: true`.

Ontology retrieval uses manual `embed_query` embeddings and `get_collection(name=...)` without passing embedding functions to avoid persisted embedding conflicts (mirrors `rag_ontologies`).
