#!/usr/bin/env bash
# Запускается при старте сессии Claude Code: ставит z3, если его нет. Никогда не роняет сессию.
python3 -c "import z3" 2>/dev/null && exit 0
pip install -q z3-solver >/dev/null 2>&1 \
  || pip install -q --break-system-packages z3-solver >/dev/null 2>&1 \
  || true
exit 0
