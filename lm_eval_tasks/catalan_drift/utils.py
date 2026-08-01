import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from functools import partial
from pathlib import Path

from lm_eval.api.task import ConfigurableTask

CATALAN_FORBIDDEN_TERMS = ("asunto", "subject", "aquí tienes")
LANGUAGE_FAIL_NON_CA_RATIO = 0.15
LANGUAGE_MIN_CONFIDENCE = 0.71
LANGUAGE_MIN_ALPHA_TOKENS = 5
LANGUAGE_WINDOW_TOKENS = 40
DEFAULT_LANGUAGE_ID_MODEL = "models/lid.176.ftz"
DEFAULT_FASTTEXT_BINARY = "models/fasttext"

_ALPHA_TOKEN_RE = re.compile(r"[^\W\d_]+(?:[.'’·-][^\W\d_]+)*", re.UNICODE)
_CODE_FENCE_RE = re.compile(r"```.*?```", re.S)
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)


def term_pattern(term: object) -> re.Pattern[str] | None:
    text = str(term).casefold()
    if not text:
        return None
    return re.compile(r"(?<!\w)" + re.escape(text) + r"(?!\w)", re.I)


def forbidden_hits(
    response: str,
    forbidden_terms: Iterable[object],
) -> list[str]:
    searchable = response.casefold()
    hits = []
    for term in forbidden_terms:
        pattern = term_pattern(term)
        if pattern and pattern.search(searchable):
            hits.append(str(term))
    return hits


def _text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return next((_text(item) for item in value if _text(item)), "")
    return ""


class CatalanDriftTask(ConfigurableTask):
    def __init__(self, config=None):
        if config:
            config = {key: value for key, value in config.items() if key != "class"}
        super().__init__(config=config)

    def fewshot_context(
        self,
        doc,
        num_fewshot,
        system_instruction=None,
        apply_chat_template=False,
        fewshot_as_multiturn=False,
        chat_template=None,
        gen_prefix=None,
    ):
        if not doc.get("messages"):
            return super().fewshot_context(
                doc,
                num_fewshot,
                system_instruction=system_instruction,
                apply_chat_template=apply_chat_template,
                fewshot_as_multiturn=fewshot_as_multiturn,
                chat_template=chat_template,
                gen_prefix=gen_prefix,
            )

        messages = list(doc["messages"])
        if system_instruction:
            if messages and messages[0].get("role") == "system":
                messages[0] = {
                    "role": "system",
                    "content": system_instruction + "\n\n" + messages[0]["content"],
                }
            else:
                messages.insert(0, {"role": "system", "content": system_instruction})

        if apply_chat_template and chat_template:
            return partial(chat_template, add_generation_prompt=not gen_prefix)(messages)

        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)


def _alpha_tokens(text: str) -> list[str]:
    return _ALPHA_TOKEN_RE.findall(_URL_RE.sub(" ", text))


def _language_segments(text: str) -> Iterable[tuple[str, int]]:
    text = _CODE_FENCE_RE.sub("\n\n", text)
    for block in re.split(r"\n\s*\n+", text):
        block = block.strip()
        if not block:
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        units = lines if len(lines) > 1 else _SENTENCE_BOUNDARY_RE.split(block)
        for unit in units:
            tokens = _alpha_tokens(unit)
            if len(tokens) < LANGUAGE_MIN_ALPHA_TOKENS:
                continue
            if len(tokens) <= LANGUAGE_WINDOW_TOKENS:
                yield _URL_RE.sub(" ", unit), len(tokens)
                continue
            for start in range(0, len(tokens), LANGUAGE_WINDOW_TOKENS):
                window = tokens[start : start + LANGUAGE_WINDOW_TOKENS]
                if len(window) >= LANGUAGE_MIN_ALPHA_TOKENS:
                    yield " ".join(window), len(window)


def _fasttext_binary() -> str:
    binary = os.environ.get("LANGUAGE_ID_FASTTEXT_BIN")
    if binary:
        return binary
    if Path(DEFAULT_FASTTEXT_BINARY).exists():
        return DEFAULT_FASTTEXT_BINARY
    return shutil.which("fasttext") or "fasttext"


def _predict_fasttext(text: str) -> tuple[str, float]:
    model = os.environ.get("LANGUAGE_ID_MODEL", DEFAULT_LANGUAGE_ID_MODEL)
    result = subprocess.run(
        [_fasttext_binary(), "predict-prob", model, "-", "1"],
        input=text.replace("\n", " ") + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    parts = result.stdout.strip().split()
    if len(parts) < 2:
        raise RuntimeError("fastText did not return a prediction")
    lang = parts[0].removeprefix("__label__").casefold().replace("-", "_").split("_", 1)[0]
    return lang, float(parts[1])


def _language_errors(doc, response):
    if doc.get("target_lang") != "ca" or not response.strip():
        return []

    total_tokens = 0
    non_catalan_tokens = 0
    try:
        for segment, tokens in _language_segments(response):
            total_tokens += tokens
            lang, confidence = _predict_fasttext(segment)
            if confidence >= LANGUAGE_MIN_CONFIDENCE and lang != "ca":
                non_catalan_tokens += tokens
    except Exception as exc:
        return [f"detector: {exc}"]

    if total_tokens == 0:
        return ["detector: no detectable language tokens"]

    ratio = non_catalan_tokens / total_tokens
    if ratio >= LANGUAGE_FAIL_NON_CA_RATIO:
        return [f"non_catalan_token_ratio={ratio:.3f}"]
    return []


def process_results(doc, results):
    response = _text(results).strip()
    forbidden_terms = [str(term) for term in (doc.get("forbidden_terms") or [])]
    if doc.get("target_lang") == "ca":
        forbidden_terms.extend(CATALAN_FORBIDDEN_TERMS)
    forbidden = forbidden_hits(
        response,
        forbidden_terms,
    )
    language_errors = _language_errors(doc, response)
    api_or_empty_fail = not response
    passed = not (api_or_empty_fail or forbidden or language_errors)
    category = str(doc.get("category", "unknown"))
    return {
        "drift_pass": float(passed),
        "forbidden_fail": float(bool(forbidden)),
        "language_fail": float(bool(language_errors)),
        "api_or_empty_fail": float(api_or_empty_fail),
        f"{category}_pass": float(passed),
    }
