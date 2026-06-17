#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

MODEL="${MODEL:-qwen3-30b-a3b-instruct-2507}"
# EPISODE="${EPISODE:-}"
# HORIZON="${HORIZON:-}"
# K="${K:-0}"
# RETRIVAL_METHOD="${RETRIVAL_METHOD:-recent_k}"
PYTHON_BIN="${PYTHON_BIN:-python}"
DATA_DIR="${DATA_DIR:-data}"
EVAL_RESULT_DIR="${EVAL_RESULT_DIR:-eval_result}"
LOG_DIR="${LOG_DIR:-log/${MODEL}}"
RUN_EXPERIMENTS="${RUN_EXPERIMENTS:-1}"
RUN_EVALUATION="${RUN_EVALUATION:-1}"
RUN_ORGANIZE="${RUN_ORGANIZE:-1}"

mkdir -p "${LOG_DIR}"

mapfile -t ORDERS < <(
  find prompts/recipe -maxdepth 1 -type f -name '*.txt' \
    -printf '%f\n' \
    | sed -E 's/^[0-9]+_//; s/\.txt$//' \
    | sort
)

ORDERS_ARG="${ORDERS[*]}"

echo "[all-eval] model=${MODEL}"
echo "[all-eval] tasks=${#ORDERS[@]}"
# echo "[all-eval] episode=${EPISODE}, horizon=${HORIZON}"

if [[ "${RUN_EXPERIMENTS}" == "1" ]]; then
  for order in "${ORDERS[@]}"; do
    echo "[all-eval] running experiment: ${order}"
    main_args=(
      main.py
      --gpt_model "${MODEL}"
      --order "${order}"
      # --episode "${EPISODE}"
      # --horizon "${HORIZON}"
      # --K "${K}"
      # --retrival_method "${RETRIVAL_METHOD}"
      --statistics_save_dir "${DATA_DIR}"
    )
    if [[ -n "${COLLAB_LLM_API_BASE:-}" ]]; then
      main_args+=(--local_server_api "${COLLAB_LLM_API_BASE}")
    fi
    if [[ -n "${COLLAB_EMBEDDING_API_BASE:-}" ]]; then
      main_args+=(--embedding_server_api "${COLLAB_EMBEDDING_API_BASE}")
    fi
    "${PYTHON_BIN}" "${main_args[@]}" > "${LOG_DIR}/${order}.log" 2>&1
  done
fi

if [[ "${RUN_EVALUATION}" == "1" ]]; then
  echo "[all-eval] evaluating all tasks"
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
fi

if [[ "${RUN_ORGANIZE}" == "1" ]]; then
  echo "[all-eval] organizing CSV results"
  "${PYTHON_BIN}" organize_result.py \
    --model "${MODEL}" \
    --orders "${ORDERS_ARG}" \
    --eval_result_dir "${EVAL_RESULT_DIR}"

  "${PYTHON_BIN}" convert_result.py \
    --models "${MODEL}" \
    --eval_result_dir "${EVAL_RESULT_DIR}"
fi

echo "[all-eval] done"
echo "[all-eval] per-task logs: ${SCRIPT_DIR}/${LOG_DIR}"
echo "[all-eval] task CSV: ${SCRIPT_DIR}/${EVAL_RESULT_DIR}/statistics_data.csv"
echo "[all-eval] level CSV: ${SCRIPT_DIR}/${EVAL_RESULT_DIR}/converted_data.csv"
