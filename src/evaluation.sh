#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL="${MODEL:-qwen3-30b-a3b-instruct-2507}"
PYTHON_BIN="${PYTHON_BIN:-python}"
DATA_DIR="${DATA_DIR:-data}"
EVAL_RESULT_DIR="${EVAL_RESULT_DIR:-eval_result}"

mapfile -t ORDERS < <(
  find prompts/recipe -maxdepth 1 -type f -name '*.txt' \
    -printf '%f\n' \
    | sed -E 's/^[0-9]+_//; s/\.txt$//' \
    | sort
)

ORDERS_ARG="${ORDERS[*]}"

eval_args=(
  evaluation.py
  --test_mode build_in
  --model "${MODEL}"
  --orders "${ORDERS_ARG}"
  --log_dir "${DATA_DIR}"
  --save_dir "${EVAL_RESULT_DIR}"
)
if [[ -n "${COLLAB_EMBEDDING_API_BASE:-}" ]]; then
  eval_args+=(--embedding_server_api "${COLLAB_EMBEDDING_API_BASE}")
fi

"${PYTHON_BIN}" "${eval_args[@]}"
"${PYTHON_BIN}" organize_result.py \
  --model "${MODEL}" \
  --orders "${ORDERS_ARG}" \
  --eval_result_dir "${EVAL_RESULT_DIR}"
"${PYTHON_BIN}" convert_result.py \
  --models "${MODEL}" \
  --eval_result_dir "${EVAL_RESULT_DIR}"
