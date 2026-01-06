"""Local in-process Transformers LLM client."""

from __future__ import annotations

from typing import Any, Dict, Optional


class LocalTransformersClient:
    """Use HuggingFace Transformers to generate text locally."""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        self._cfg = cfg or {}
        self._model_path = self._cfg.get("model_path")
        if not self._model_path:
            raise ValueError("llm.model_path is required for local_transformers mode")

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "transformers and torch are required for llm.mode=local_transformers"
            ) from exc

        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_path,
            use_fast=True,
            fix_mistral_regex=True,
        )
        if self._tokenizer.pad_token_id is None and self._tokenizer.eos_token_id is not None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        self._device = self._resolve_device(self._cfg.get("device", "auto"))
        torch_dtype = self._resolve_dtype(self._cfg.get("dtype", "auto"), torch)

        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_path,
            torch_dtype=torch_dtype,
        ).to(self._device)
        self._model.eval()

        self._apply_chat_template = self._cfg.get("apply_chat_template", True)
        self._system_prompt = self._cfg.get("system_prompt") or ""
        self._max_new_tokens = int(self._cfg.get("max_new_tokens", 256))
        self._temperature = float(self._cfg.get("temperature", 0.0))
        self._top_p = float(self._cfg.get("top_p", 1.0))
        if "do_sample" in self._cfg:
            self._do_sample = bool(self._cfg["do_sample"])
        else:
            self._do_sample = self._temperature > 0.0
        
        # If not sampling, force neutral defaults to avoid HF warning
        if not self._do_sample:
            self._temperature = 1.0
            self._top_p = 1.0

        # Also sync model.generation_config (if present)
        gen_cfg = getattr(self._model, "generation_config", None)
        if gen_cfg is not None:
            gen_cfg.do_sample = self._do_sample
            gen_cfg.temperature = self._temperature
            gen_cfg.top_p = self._top_p

        stop = self._cfg.get("stop") or []
        if isinstance(stop, str):
            stop = [stop]
        self._stop = [str(item) for item in stop if str(item)]

    def _resolve_device(self, device: Optional[str]) -> str:
        device = (device or "auto").lower()
        if device == "auto":
            if self._torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        if device == "mps":
            if not self._torch.backends.mps.is_available():
                raise RuntimeError("llm.device is mps but MPS is not available")
            return "mps"
        if device == "cpu":
            return "cpu"
        raise ValueError(f"Unsupported device: {device}")

    @staticmethod
    def _resolve_dtype(dtype: Optional[str], torch: Any) -> Optional[Any]:
        if not dtype:
            return None
        dtype = dtype.lower()
        if dtype == "auto":
            return None
        mapping = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        if dtype not in mapping:
            raise ValueError(f"Unsupported dtype: {dtype}")
        return mapping[dtype]

    def _build_inputs(self, prompt: str):
        if self._apply_chat_template and getattr(self._tokenizer, "chat_template", None):
            messages = []
            if self._system_prompt:
                messages.append({"role": "system", "content": self._system_prompt})
            messages.append({"role": "user", "content": prompt})
            rendered = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            encoded = self._tokenizer(rendered, return_tensors="pt")
        else:
            encoded = self._tokenizer(prompt, return_tensors="pt")

        input_ids = encoded["input_ids"]
        attention_mask = encoded.get("attention_mask")
        if attention_mask is None:
            attention_mask = self._torch.ones_like(input_ids)
        return input_ids, attention_mask

    @staticmethod
    def _apply_stop(text: str, stop_list: list[str]) -> str:
        earliest = None
        for stop in stop_list:
            idx = text.find(stop)
            if idx != -1 and (earliest is None or idx < earliest):
                earliest = idx
        if earliest is None:
            return text
        return text[:earliest]

    def generate(self, prompt: str) -> str:
        input_ids, attention_mask = self._build_inputs(prompt)
        input_ids = input_ids.to(self._model.device)
        attention_mask = attention_mask.to(self._model.device)

        # Build EOS ids (standard EOS + Llama 3 <|eot_id|> if present)
        eos_ids = []
        if self._tokenizer.eos_token_id is not None:
            eos_ids.append(self._tokenizer.eos_token_id)

        # Llama 3 end-of-turn token
        eot_id = self._tokenizer.convert_tokens_to_ids("<|eot_id|>")
        if isinstance(eot_id, int) and eot_id >= 0 and eot_id not in eos_ids:
            eos_ids.append(eot_id)
        # Gemma end-of-turn token
        eot_id = self._tokenizer.convert_tokens_to_ids("<end_of_turn>")
        if isinstance(eot_id, int) and eot_id >= 0 and eot_id not in eos_ids:
            eos_ids.append(eot_id)

        generate_kwargs = {
            "max_new_tokens": self._max_new_tokens,
            "do_sample": self._do_sample,
            "eos_token_id": eos_ids[0] if len(eos_ids) == 1 else eos_ids,
            "pad_token_id": self._tokenizer.pad_token_id,
        }

        if self._do_sample:
            generate_kwargs["temperature"] = self._temperature
            generate_kwargs["top_p"] = self._top_p

        with self._torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                attention_mask=attention_mask,
                **generate_kwargs,
            )

        generated_ids = output_ids[0][input_ids.shape[-1] :]
        text = self._tokenizer.decode(generated_ids, skip_special_tokens=False)

        if self._stop:
            text = self._apply_stop(text, self._stop)
        print(text)
        return text
