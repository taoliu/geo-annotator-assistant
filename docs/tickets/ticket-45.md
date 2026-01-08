# Ticket #45: LLM-TRANSPORT-001 — Define transport interface and factory wiring

## Background

v0.6 introduces an LLM transport abstraction so we can support OpenAI-style HTTP APIs and llama.cpp servers without changing pipeline semantics. This must preserve the core invariant: **LLMs propose; deterministic logic decides**. 

---

## Scope (STRICT)

### In scope

1. **Define a stable LLM transport interface** in `src/llm/`:

   * A minimal `LLMClient` protocol / abstract base class
   * A structured `LLMRequest` input object
   * A structured `LLMResult` output object

2. **Factory wiring**:

   * Extend `src/llm/factory.py` to select a transport implementation via config key `llm.transport`.
   * Keep `local_transformers` working unchanged.
   * Add placeholder registrations (stubs) for:

     * `openai_http`
     * `llama_cpp_http`

3. **No behavior changes**:

   * No changes to validators, decision engine, repair loop semantics, or prompts.
   * No changes to final 8-field schema or audit semantics.

### Out of scope

* Implementing the HTTP transports (next tickets)
* Adding retry logic, timeouts, or batching (later tickets)
* Any config namespace changes involving `rag.*` / `rag.ontology.*`

---

## Interface requirements (MANDATORY)

### `LLMRequest`

Must include at least:

* `prompt: str`
* `system: str | None`
* `model: str | None`
* `max_tokens: int | None`
* `temperature: float | None`
* `top_p: float | None`
* `stop: list[str] | None`
* `seed: int | None` (optional if unused by some transports)
* `request_id: str` (caller-provided; must round-trip)
* `tags: dict[str, str]` (for stage labels like `stage=label|repair_format|repair_field|repair_ontology_guided`)

### `LLMResult`

Must include at least:

* `text: str` (raw model text)
* `request_id: str` (must match request)
* `usage: dict | None` (provider-dependent)
* `transport_meta: dict` (provider name, model id, latency_ms, retry_count, etc.)
* `request_fingerprint: str` (deterministic hash of request payload + generation params)

### `LLMClient`

A single call method, for example:

* `generate(request: LLMRequest) -> LLMResult`

No JSON parsing and no schema validation inside the transport.

---

## Implementation notes

* There is already `src/llm/base.py`, `src/llm/factory.py`, and `src/llm/local_transformers.py` in the repo structure. Prefer **extending** rather than replacing. 
* Keep all current call sites working.
* Add stubs (`NotImplementedError`) for the two new transports, but they must be instantiable via the factory so later tickets can implement them without touching core code again.
* Fingerprint should be stable across runs given identical request content and params (use a canonical JSON serialization with sorted keys).

---

## Acceptance Criteria

1. Existing test suite passes.
2. New tests confirm:

   * Factory selects `local_transformers` when configured.
   * Factory can instantiate the `openai_http` and `llama_cpp_http` classes (even if `generate()` raises `NotImplementedError`).
   * Fingerprint is stable for identical `LLMRequest` objects.
3. No changes to decision routing outputs or validator behavior.

---

## Tests Required

Add a focused unit test file, e.g. `tests/test_llm_transport_factory.py`, covering:

1. `llm.transport=local_transformers` creates the existing implementation.
2. `llm.transport=openai_http` and `llm.transport=llama_cpp_http` create stub classes and raise `NotImplementedError` on `generate()`.
3. Fingerprint determinism:

   * two identical `LLMRequest` objects yield identical `request_fingerprint`.

---

## Non-Goals (Explicit)

* No HTTP calls
* No retry/backoff
* No prompt changes
* No audit format changes beyond adding `request_fingerprint` to the LLM result object returned to existing audit paths (do not restructure audit records)

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-45.md` and paste this ticket verbatim.
