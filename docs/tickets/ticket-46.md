# Ticket #46: LLM-TRANSPORT-002 — OpenAI-style HTTP transport (single adapter; llama.cpp skipped)

## Background

v0.6 adds an LLM transport abstraction while preserving the architectural invariant: **LLMs propose; deterministic logic decides**. The next concrete step is a single HTTP transport that speaks **OpenAI-style APIs**, which can also be used later with any engine that implements the same protocol (including llama.cpp servers in OpenAI-compat mode).  

This ticket **does not add** a dedicated `llama_cpp_http` adapter.

---

## Scope (STRICT)

### In scope

1. **Implement an OpenAI-style HTTP client** in `src/llm/openai_http.py` implementing the `LLMClient` interface from Ticket #45.
2. **Support at least one endpoint** (choose one, but structure code so the other can be added later without touching call sites):

   * Preferred: `POST {base_url}/v1/chat/completions`
   * Optional (if already easy): `POST {base_url}/v1/responses`
3. **Deterministic generation params by default**:

   * `temperature=0`
   * `top_p=1`
   * fixed `max_tokens` (from config or request)
   * `seed` forwarded when supported by the endpoint (otherwise ignored but included in fingerprint)
4. **Config plumbing** under `llm.openai_http.*` (must not touch `rag.*` namespaces):

   * `base_url`
   * `api_key` (optional if server does not require)
   * `model`
   * `timeout_s`
   * `endpoint` (e.g., `chat_completions` default)
   * `default_max_tokens`
5. **Audit-friendly metadata** returned via `LLMResult.transport_meta`:

   * `provider="openai_http"`
   * `base_url` (or redacted host)
   * `model`
   * `endpoint`
   * `latency_ms`
   * `http_status`
   * `retry_count` (0 for this ticket, unless retry helper already exists)
6. **Request fingerprint** must be computed deterministically from:

   * request prompt/system text
   * generation params (temperature/top_p/max_tokens/stop/seed/model)
   * endpoint + base_url (or normalized base_url host)

### Out of scope

* A separate llama.cpp adapter (`llama_cpp_http.py`) is explicitly **skipped**.
* Retry/backoff policy (do later as a separate ticket unless already trivial).
* Any prompt, parsing, validation, decision routing, or repair logic changes.
* Any change to final 8-field output schema.

---

## Behavioral constraints (MANDATORY)

* Transport layer must be **dumb**:

  * No JSON extraction, no schema validation, no repair logic, no field coercion.
  * It returns raw `text` only.
* Must not introduce hidden state or caching that affects outputs.
* Must not change any pipeline ordering or decision semantics. 

---

## Implementation notes

* Use `httpx` if available; otherwise `requests` is acceptable.
* Build request payload for `/v1/chat/completions`:

  * `messages=[{"role":"system","content":system}, {"role":"user","content":prompt}]` (omit system if None)
  * include deterministic params (above)
  * include `stop` if provided
* Parse response:

  * Extract the primary text field:

    * for chat completions: `choices[0].message.content`
  * If the response schema is unexpected, raise a transport error with a short diagnostic message (no free-text rationale added to audit).
* Add an example block to `config/example_config.yaml` showing how to enable:

  * `llm.transport: openai_http`
  * `llm.openai_http.base_url: ...`
  * `llm.openai_http.model: ...`

---

## Acceptance Criteria

1. Existing tests pass.
2. New unit tests pass with **mocked HTTP responses** (no network dependency):

   * payload contains deterministic params
   * adapter extracts `text` correctly
   * fingerprint is stable
3. Switching from `local_transformers` to `openai_http` requires **config change only** (no code changes in pipeline).

---

## Tests Required

Add `tests/test_openai_http_transport.py`:

1. **Payload test** (mock server):

   * when request has `temperature=None`, client sends `temperature=0`
   * sends `top_p=1`
   * sends configured `model`
2. **Response parse test**:

   * a mocked chat completion returns expected `LLMResult.text`
3. **Fingerprint determinism**:

   * identical `LLMRequest` → identical fingerprint
   * changing any of `prompt/system/model/temperature/top_p/max_tokens/stop/seed` changes fingerprint

---

## Non-Goals (Explicit)

* No llama.cpp-specific code
* No retries/backoff
* No streaming support
* No parallel batching

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-46.md` and paste this ticket verbatim.

---
