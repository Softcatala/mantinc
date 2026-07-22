import re
from collections.abc import Iterable
from functools import partial

from langdetect import DetectorFactory, LangDetectException, detect_langs
from lm_eval.api.task import ConfigurableTask

DetectorFactory.seed = 0

CATALAN_FORBIDDEN_TERMS = ("asunto", "subject", "aquí tienes")


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


def _language_errors(doc, response):
    if doc.get("target_lang") != "ca" or not response.strip():
        return []

    try:
        prediction = detect_langs(response)[0]
    except (LangDetectException, IndexError):
        return []
    if prediction.lang != "ca" and prediction.prob >= 0.75:
        return [f"document: {prediction.lang} ({prediction.prob:.2f})"]
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
