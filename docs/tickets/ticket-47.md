# Ticket #47: LLM-TRANSPORT-003 — Transport-level retry/timeout policy (deterministic)

## Background

OpenAI-style HTTP transport introduces network failure modes (timeouts, transient 5xx, connection resets). We need a **deterministic** retry/timeout policy that improves robustness **without changing pipeline semantics**. LLMs remain proposal-only; deterministic logic decides.  

This ticket defines a shared HTTP execution helper used by `openai_http` transport.

---

## Scope (STRICT)

### In scope

1. **Introduce a shared deterministic HTTP helper** in `src/llm/http_utils.py` (new file):

   * A single function that executes an HTTP POST with:

     * fixed timeout
     * fixed retry count
     * fixed backoff schedule
     * deterministic retry conditions
   * Returns `(response_json, transport_meta)` or raises a transport exception.

2. **Deterministic retry policy (MANDATORY)**

   * Retry count: fixed integer `max_retries` from config (default 2).
   * Backoff: deterministic sequence (no jitter), e.g. `[0.5, 1.0, 2.0]` seconds truncated to retries used.
   * Retries must **not** modify:

     * prompt/system text
     * model
     * generation params
     * headers (except re-sending identical auth header)
     * payload ordering (serialize JSON with sorted keys for fingerprinting)

3. **Deterministic retry conditions**

   * Retry on:

     * connection errors
     * timeouts
     * HTTP 429
     * HTTP 500, 502, 503, 504
   * Do **not** retry on other 4xx (400/401/403/404/422 etc).

4. **Timeout policy**

   * Single `timeout_s` applied consistently to connect + read.
   * Configurable via `llm.openai_http.timeout_s` (already added in Ticket #46), no new namespace.

5. **Transport metadata**

   * Ensure `LLMResult.transport_meta` includes:

     * `retry_count` (0..max_retries)
     * `backoff_s` (list of floats actually slept)
     * `timeout_s`
     * `last_http_status` (if any)
     * `error_class` and `error_message_short` when failing (short, no response body dumps)

6. **Wire into openai_http**

   * Update `src/llm/openai_http.py` to call the helper.
   * No change to request fingerprint rules (fingerprint must remain based on request content + params, not retries).

### Out of scope

* Any change to prompts, validators, decision engine, repair loop, or output schema.
* Adding a separate llama.cpp adapter.
* Adding streaming support or batching.

---

## Behavioral constraints (MANDATORY)

* Retries must be **deterministic and auditable**.
* Retry behavior must be visible in audit artifacts via `transport_meta`, but must not create free-text rationale. 
* Transport stays “dumb”: no JSON extraction beyond selecting the API’s standard `text` field (already in Ticket #46).

---

## Implementation notes

* Use `time.sleep()` with deterministic backoff values.
* Keep exceptions typed, e.g. `LLMTransportError`, `LLMRetryableError` (or a single error class with fields).
* When raising, include:

  * request_id
  * endpoint
  * last status (if any)
  * retry_count
  * short error message
* Do not log full prompts or full responses in exception messages.

---

## Acceptance Criteria

1. Existing test suite passes.
2. New unit tests demonstrate:

   * retries happen exactly as configured for retryable failures
   * no retry occurs for non-retryable 4xx
   * timeout is applied and counted as retryable
   * `transport_meta.retry_count` and `transport_meta.backoff_s` are correct
3. Fingerprint for a request is identical regardless of transient failures/retries.

---

## Tests Required

Add `tests/test_http_retry_policy.py`:

1. **Retryable status test**

   * mock responses: 502 then 200
   * assert 1 retry, backoff list length 1, final success

2. **429 test**

   * 429 then 200
   * assert retry occurred

3. **Non-retryable 4xx test**

   * 400 once
   * assert no retry and transport error raised

4. **Timeout test**

   * simulate timeout exception then success
   * assert retry occurred and meta includes timeout

5. **Fingerprint invariance**

   * confirm request_fingerprint unchanged across scenarios (may check by calling fingerprint function directly)

---

## Non-Goals (Explicit)

* No “failover” to different models or transports
* No adaptive backoff or jitter
* No caching

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-47.md` and paste this ticket verbatim.

---
