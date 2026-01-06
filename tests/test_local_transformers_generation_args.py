from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class FakeTensor:
    def __init__(self, data: list[list[int]]):
        self.data = data
        self.shape = (len(data), len(data[0]) if data else 0)
        self.device = "cpu"

    def to(self, device: str) -> "FakeTensor":
        self.device = device
        return self

    def __getitem__(self, idx: int):
        return self.data[idx]


class FakeTokenizer:
    def __init__(self) -> None:
        self.chat_template = "template"
        self.pad_token_id = 0
        self.eos_token_id = 0
        self.pad_token = "<pad>"
        self.last_apply_chat_template = None
        self.last_tokenize = None

    @classmethod
    def from_pretrained(cls, *args, **kwargs) -> "FakeTokenizer":
        return cls()

    def apply_chat_template(
        self,
        messages,
        tokenize: bool,
        add_generation_prompt: bool,
        return_tensors: str | None = None,
    ) -> str:
        self.last_apply_chat_template = {
            "messages": messages,
            "tokenize": tokenize,
            "add_generation_prompt": add_generation_prompt,
            "return_tensors": return_tensors,
        }
        if tokenize:
            return "tokenized"
        return "rendered"

    def __call__(self, text: str, return_tensors: str | None = None):
        self.last_tokenize = {"text": text, "return_tensors": return_tensors}
        return {
            "input_ids": FakeTensor([[1, 2, 3]]),
            "attention_mask": FakeTensor([[1, 1, 1]]),
        }

    def decode(self, ids, skip_special_tokens: bool = True) -> str:
        return "decoded text"


class FakeModel:
    last_instance = None

    def __init__(self) -> None:
        type(self).last_instance = self
        self.device = "cpu"
        self.last_generate_kwargs = None

    def to(self, device: str) -> "FakeModel":
        self.device = device
        return self

    def eval(self) -> None:
        return None

    def generate(self, input_ids, **kwargs):
        self.last_generate_kwargs = kwargs
        return [[1, 2, 3, 4, 5]]


class FakeAutoModelForCausalLM:
    @classmethod
    def from_pretrained(cls, *args, **kwargs) -> FakeModel:
        return FakeModel()


class FakeAutoTokenizer:
    @classmethod
    def from_pretrained(cls, *args, **kwargs) -> FakeTokenizer:
        return FakeTokenizer()


class FakeNoGrad:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _install_fake_transformers(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_torch = SimpleNamespace(
        float16="float16",
        bfloat16="bfloat16",
        float32="float32",
        no_grad=lambda: FakeNoGrad(),
        ones_like=lambda tensor: FakeTensor([[1] * tensor.shape[-1]]),
    )
    fake_torch.backends = SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False))

    fake_transformers = SimpleNamespace(
        AutoModelForCausalLM=FakeAutoModelForCausalLM,
        AutoTokenizer=FakeAutoTokenizer,
    )

    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)


def test_generate_passes_attention_mask_without_sampling_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_transformers(monkeypatch)

    from llm.local_transformers import LocalTransformersClient

    client = LocalTransformersClient(
        {
            "model_path": "fake-model",
            "apply_chat_template": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": False,
        }
    )

    client.generate("hello")

    model = FakeModel.last_instance
    assert model is not None
    kwargs = model.last_generate_kwargs
    assert kwargs is not None
    assert "attention_mask" in kwargs
    assert "temperature" not in kwargs
    assert "top_p" not in kwargs
    assert kwargs["do_sample"] is False
    assert client._tokenizer.last_apply_chat_template["tokenize"] is False


def test_generate_passes_sampling_args_when_do_sample_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_transformers(monkeypatch)

    from llm.local_transformers import LocalTransformersClient

    client = LocalTransformersClient(
        {
            "model_path": "fake-model",
            "apply_chat_template": True,
            "temperature": 0.6,
            "top_p": 0.8,
            "do_sample": True,
        }
    )

    client.generate("hello")

    model = FakeModel.last_instance
    assert model is not None
    kwargs = model.last_generate_kwargs
    assert kwargs is not None
    assert "attention_mask" in kwargs
    assert kwargs["temperature"] == 0.6
    assert kwargs["top_p"] == 0.8
    assert kwargs["do_sample"] is True
