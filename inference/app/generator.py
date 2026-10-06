"""Small instruct-model text generation — the implementation behind the
/generate route.

transformers' generate() call is synchronous and has no built-in wall-clock
timeout, so it runs in a worker thread and the caller gets None if timeout_s
elapses first. The generation itself is not cancelled — it keeps running in
the background and its result is discarded — which is acceptable for a
short-prompt rewriting workload but worth knowing about under load.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


class TextGenerator:
    def __init__(self, model_name: str, device: str) -> None:
        self._model_name = model_name
        self._device = device
        self._model = None
        self._tokenizer = None
        self._executor = ThreadPoolExecutor(max_workers=2)

    def load(self) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModelForCausalLM.from_pretrained(self._model_name).to(self._device)
        self._model.eval()

    def warm(self) -> None:
        self.generate("Say hello in one short sentence.", max_tokens=16, timeout_s=30)

    def generate(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("TextGenerator.load() must be called before generate()")

        future = self._executor.submit(self._generate_sync, prompt, max_tokens)
        try:
            return future.result(timeout=timeout_s)
        except FutureTimeoutError:
            return None

    def _generate_sync(self, prompt: str, max_tokens: int) -> str:
        import torch

        messages = [{"role": "user", "content": prompt}]
        chat_text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(chat_text, return_tensors="pt").to(self._device)

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        generated_ids = output_ids[0][inputs["input_ids"].shape[1] :]
        return self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
