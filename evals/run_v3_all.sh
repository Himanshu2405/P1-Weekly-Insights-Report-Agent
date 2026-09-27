#!/bin/zsh
# prompt v3 + judge v4 evaluation on Sonnet 5, in order. Each step is resumable.
set -eo pipefail
cd "$(dirname "$0")/.."
PY=./.venv/bin/python
echo "== 1. re-judge v2 golden with judge v4 (Sonnet 5)"; $PY scripts/judge_golden.py --experiment v2_opus-5 --rejudge --model claude-sonnet-5 | tail -1
echo "== 2. v3 golden (Sonnet 5)";                         $PY scripts/run_golden.py --version v3 --model claude-sonnet-5 | tail -1
echo "== 3. judge v3 golden (Sonnet 5)";                   $PY scripts/judge_golden.py --experiment v3_sonnet-5 --model claude-sonnet-5 | tail -1
echo "== 4. v2 held-out (Sonnet 5)";                       $PY scripts/run_golden.py --version v2 --set heldout --model claude-sonnet-5 | tail -1
echo "== 5. judge v2 held-out (Sonnet 5)";                 $PY scripts/judge_golden.py --experiment heldout_v2_sonnet-5 --model claude-sonnet-5 | tail -1
echo "== 6. v3 held-out (Sonnet 5)";                       $PY scripts/run_golden.py --version v3 --set heldout --model claude-sonnet-5 | tail -1
echo "== 7. judge v3 held-out (Sonnet 5)";                 $PY scripts/judge_golden.py --experiment heldout_v3_sonnet-5 --model claude-sonnet-5 | tail -1
echo "== done"
