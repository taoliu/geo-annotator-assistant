Ticket #15: AGENT-WS-015 — Local LLM integration via Transformers (in-process) with chat template by default

You are working in repo `geo-gsm-annotator-agent`.

Ticket: AGENT-WS-015 — Local LLM integration via Transformers (in-process) with chat template by default

Goal:
Replace stub LLM with a real local in-process LLM backend using HuggingFace Transformers.
By default, apply the tokenizer chat template if available (apply_chat_template=true).

Constraints:
- No HTTP server required.
- Model is stored as a local HF directory (config.json, model.safetensors, tokenizer.json, etc.).
- Keep the rest of the agent pipeline unchanged (validators, decision loop, writer).
- Make it optional: support llm.mode=stub and llm.mode=local_transformers.

Files to add:
- `src/llm/base.py`
- `src/llm/local_transformers.py`
- `src/llm/factory.py`
- `src/llm/__init__.py`

Files to update:
- `src/agent/run_single.py` (use LLM client rather than stub inline)
- `config/example_config.yaml` (add llm.backend/mode fields)
- Add tests: `tests/test_llm_interface_stubbed.py` (no real model loading)

Design:

A) LLM Interface (llm/base.py)
Define a Protocol or ABC:
- `generate(prompt: str) -> str`

Also define a small dataclass `LLMResult` OPTIONAL (not required) if you want metadata.
But keep pipeline expecting raw string output.

B) Factory (llm/factory.py)
Implement:
- `create_llm_client(cfg: dict)`
Supported:
- if cfg["mode"] == "stub": return StubClient
- if cfg["mode"] in {"local_transformers", "transformers"}: return LocalTransformersClient

Put stub client inside factory or separate file.

C) LocalTransformersClient (llm/local_transformers.py)
Requirements:
- config fields:
  - model_path (local directory)
  - device: "auto"|"cpu"|"mps" (default "auto")
  - dtype: "auto"|"float16"|"bfloat16"|"float32" (default "auto")
  - max_new_tokens (default 256)
  - temperature (default 0.0)
  - top_p (default 1.0)
  - do_sample (default derived from temperature>0)
  - apply_chat_template (default true)
  - system_prompt (optional; default empty)
  - stop (optional list of stop strings; implement naive stop truncation)
- Load:
  - tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
  - model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=..., device_map=... as appropriate)
- Device handling:
  - If device == "mps": send model to mps.
  - If device == "cpu": cpu.
  - If device == "auto": prefer mps if available else cpu.
  (Do NOT attempt CUDA.)
- Generation:
  - If apply_chat_template and tokenizer has chat template:
    - build messages:
      - optional system message if system_prompt non-empty
      - user message content = prompt
    - input_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
  - Else:
    - input_ids = tokenizer(prompt, return_tensors="pt").input_ids
  - Move input_ids to model device
  - Call model.generate with:
    max_new_tokens, temperature, top_p, do_sample, eos_token_id, pad_token_id
  - Decode only newly generated tokens (exclude prompt tokens)
  - Apply stop-string truncation if stop list provided.
Return raw text string.

Important:
- Set tokenizer.pad_token if missing to eos_token to avoid warnings.
- Keep memory minimal.

D) Update agent/run_single.py
Replace stub LLM creation with:
- client = create_llm_client(cfg["llm"])
- raw_output = client.generate(final_prompt)
Store raw_output in state.llm_raw_outputs.

Keep stub mode behavior identical to before (valid JSON).

E) Update config/example_config.yaml
Add fields:
llm:
  mode: stub
  apply_chat_template: true
  max_new_tokens: 256
  temperature: 0.0
  top_p: 1.0
  device: auto
  dtype: auto
  model_path: ./llama-3.2-1b-it
  stop: []

Do NOT require model_path when mode=stub.

F) Tests (no real model loading)
Create `tests/test_llm_interface_stubbed.py`:
- Ensure factory returns stub client when mode=stub
- Ensure stub client generate returns valid JSON with required keys when given prompt+context
- Ensure run_single_from_context_record works with stub mode (already tested elsewhere, but keep a minimal smoke test)

Do NOT add tests requiring transformers model download.

G) Dependency note
Assume `transformers` and `torch` are available in environment.
If they are not, implement graceful error:
- if mode=local_transformers and import fails, raise RuntimeError with clear message.

Acceptance criteria:
- All existing tests pass.
- New tests pass.
- Stub behavior unchanged.
- LocalTransformersClient code exists and can be used by setting llm.mode=local_transformers.

Deliverables:
- src/llm/* new modules
- updated src/agent/run_single.py
- updated config/example_config.yaml
- tests/test_llm_interface_stubbed.py
