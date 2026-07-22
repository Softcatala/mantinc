TASK ?= catalan_drift
RUN_NAME ?= lm-eval
LM_EVAL_MODEL ?= hf
MODEL_ARGS ?=
GEN_KWARGS ?=
DISPLAY_MODEL ?= $(MODEL_ARGS)
OUT_DIR ?= outputs/lm_eval/$(RUN_NAME)
EVAL_TIMELINE ?= outputs/eval_timeline.tsv
PROMPTS ?= data/prompts_monolingual.yaml data/prompts_crosslingual_basic.yaml data/prompts_multi_turn.yaml data/prompts_crosslingual_advanced.yaml
EXPORT ?= data/lm_eval/catalan_drift.jsonl
DEFAULT_EVAL_RUNS ?= gpt-5.5 gemini-2.5-flash
ALL_EVAL_RUNS ?= gpt-5.5 gemini-2.5-flash gemma-3-12b-it-Q8_0 gemma-4-E4B_q4_0-it gemma-2-2b-it-Q8_0 Qwen3.5-9B-Q8_0 Qwen2.5-1.5B-Instruct-Q8_0 Ministral-3-8B-Instruct-2512-Q8_0 salamandra-7b-instruct-2606.Q8_0
LOCAL_OPENAI_BASE_URL ?= http://localhost:9090/v1/chat/completions
UV_CACHE_DIR ?= .uv-cache
UV_PYTHON_INSTALL_DIR ?= .uv-python
UV_RUN ?= UV_CACHE_DIR=$(UV_CACHE_DIR) UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run
PYTHON ?= $(UV_RUN) python
LM_EVAL ?= $(UV_RUN) lm_eval
SKIP_EXPORT ?=
LIMIT ?=
EVAL_EXPORT_PREREQ := $(if $(SKIP_EXPORT),,export-lm-eval)

.PHONY: build clean-outputs export-lm-eval eval eval-one eval-local-openai eval-all eval-summary eval-gpt55 eval-gemini-flash-25 eval-gemma2-2b eval-gemma3-12b eval-gemma4-e4b eval-ministral-3-8b eval-qwen25-1-5b eval-qwen35-9b eval-salamandra-7b

build:
	$(PYTHON) scripts/build_dataset.py

clean-outputs:
	@echo "Clearing outputs/"
	@mkdir -p outputs
	@find outputs -mindepth 1 -maxdepth 1 -exec rm -rf {} +

export-lm-eval: build
	$(PYTHON) scripts/catalan_drift_eval.py export-lm-eval --prompts $(PROMPTS) --output "$(EXPORT)"

eval: clean-outputs export-lm-eval
	$(MAKE) -j2 SKIP_EXPORT=1 eval-gpt55 eval-gemini-flash-25
	$(MAKE) eval-summary

eval-all: clean-outputs export-lm-eval
	$(MAKE) -j2 SKIP_EXPORT=1 eval-gpt55 eval-gemini-flash-25
	$(MAKE) SKIP_EXPORT=1 eval-gemma3-12b
	$(MAKE) SKIP_EXPORT=1 eval-gemma4-e4b
	$(MAKE) SKIP_EXPORT=1 eval-gemma2-2b
	$(MAKE) SKIP_EXPORT=1 eval-qwen35-9b
	$(MAKE) SKIP_EXPORT=1 eval-qwen25-1-5b
	$(MAKE) SKIP_EXPORT=1 eval-ministral-3-8b
	$(MAKE) SKIP_EXPORT=1 eval-salamandra-7b
	$(MAKE) eval-summary DEFAULT_EVAL_RUNS="$(ALL_EVAL_RUNS)"

eval-summary:
	$(PYTHON) scripts/catalan_drift_eval.py summary-lm-eval --task "$(TASK)" --timeline "$(EVAL_TIMELINE)" --runs $(DEFAULT_EVAL_RUNS)

eval-one:
	@test -n "$(MODEL_ARGS)" || (echo "Set MODEL_ARGS, for example: make eval MODEL_ARGS=pretrained=Qwen/Qwen3.5-9B-Q8_0-llama" && exit 2)
	@mkdir -p "$$(dirname "$(EVAL_TIMELINE)")"
	@start=$$(date +%s); start_iso=$$(date -Is); \
	printf '[%s] eval start: %s\n' "$(DISPLAY_MODEL)" "$$start_iso"; \
	printf '%s\t%s\t%s\t%s\t%s\n' "$(RUN_NAME)" "$(DISPLAY_MODEL)" start "$$start_iso" "" >> "$(EVAL_TIMELINE)"; \
	$(LM_EVAL) --include_path lm_eval_tasks --tasks "$(TASK)" --model "$(LM_EVAL_MODEL)" --model_args "$(MODEL_ARGS)" --apply_chat_template --log_samples --output_path "$(OUT_DIR)" $(if $(LIMIT),--limit "$(LIMIT)",) $(if $(GEN_KWARGS),--gen_kwargs '$(GEN_KWARGS)',); status=$$?; \
	if [ $$status -eq 0 ]; then \
		$(PYTHON) scripts/catalan_drift_eval.py score-lm-eval --prompts $(PROMPTS) --samples "$$(find "$(OUT_DIR)" -name "samples_$(TASK)*.jsonl" | sort | tail -n 1)" --model "$(DISPLAY_MODEL)" --responses-output "outputs/$(RUN_NAME).$(TASK).responses.jsonl" --report "outputs/$(RUN_NAME).$(TASK).custom_report.json" --failures-file "outputs/failures_$(RUN_NAME).txt" --passes-file "outputs/pass_$(RUN_NAME).txt" --prompt-result-file "outputs/$(RUN_NAME).$(TASK).prompt_result.txt"; status=$$?; \
	fi; \
	end=$$(date +%s); end_iso=$$(date -Is); elapsed=$$((end - start)); \
	if [ $$status -eq 0 ]; then event=end; printf '[%s] eval end: %s (duration %ss)\n' "$(DISPLAY_MODEL)" "$$end_iso" "$$elapsed"; else event=failed; printf '[%s] eval failed: %s (duration %ss, status %s)\n' "$(DISPLAY_MODEL)" "$$end_iso" "$$elapsed" "$$status"; fi; \
	printf '%s\t%s\t%s\t%s\t%s\n' "$(RUN_NAME)" "$(DISPLAY_MODEL)" "$$event" "$$end_iso" "$$elapsed" >> "$(EVAL_TIMELINE)"; \
	exit $$status

eval-local-openai: $(EVAL_EXPORT_PREREQ)
	@test -n "$(DISPLAY_MODEL)" || (echo "Set DISPLAY_MODEL, for example: make eval-local-openai DISPLAY_MODEL=gemma-3-12b-it-Q8_0" && exit 2)
	OPENAI_API_KEY=local $(MAKE) eval-one LM_EVAL_MODEL=local-chat-completions MODEL_ARGS="model=$(DISPLAY_MODEL),base_url=$(LOCAL_OPENAI_BASE_URL),tokenized_requests=False" DISPLAY_MODEL="$(DISPLAY_MODEL)" RUN_NAME="$(DISPLAY_MODEL)" GEN_KWARGS='$(GEN_KWARGS)'

eval-gpt55: $(EVAL_EXPORT_PREREQ)
	$(MAKE) eval-one LM_EVAL_MODEL=openai-chat-completions MODEL_ARGS="model=gpt-5.5" DISPLAY_MODEL=gpt-5.5 RUN_NAME=gpt-5.5 GEN_KWARGS='{"reasoning_effort":"none","temperature":0}'

eval-gemini-flash-25: $(EVAL_EXPORT_PREREQ)
	$(MAKE) eval-one LM_EVAL_MODEL=litellm MODEL_ARGS="model=gemini/gemini-2.5-flash" DISPLAY_MODEL=gemini-2.5-flash RUN_NAME=gemini-2.5-flash GEN_KWARGS='{"reasoning_effort":"none","temperature":0}'

eval-gemma3-12b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=gemma-3-12b-it-Q8_0

eval-gemma4-e4b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=gemma-4-E4B_q4_0-it GEN_KWARGS='{"chat_template_kwargs":{"enable_thinking":false}}'

eval-gemma2-2b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=gemma-2-2b-it-Q8_0

eval-qwen25-1-5b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=Qwen2.5-1.5B-Instruct-Q8_0

eval-ministral-3-8b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=Ministral-3-8B-Instruct-2512-Q8_0

eval-salamandra-7b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=salamandra-7b-instruct-2606.Q8_0

eval-qwen35-9b:
	$(MAKE) eval-local-openai DISPLAY_MODEL=Qwen3.5-9B-Q8_0 GEN_KWARGS='{"chat_template_kwargs":{"enable_thinking":false},"thinking_budget_tokens":0,"reasoning_control":true}'
