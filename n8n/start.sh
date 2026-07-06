#!/bin/sh
set -e

echo "==> Iniciando MarketMind n8n"
export N8N_PORT=${PORT:-5678}
export N8N_PROTOCOL=${N8N_PROTOCOL:-http}
WORKFLOW_ID="${N8N_WORKFLOW_ID:-QAkaxptDCI9ahjQU}"
WORKFLOW_FILE="/home/node/workflow.json"

# ── Importar workflow ───────────────────────────────────────────────────────
echo "==> Importando workflow..."
if [ -n "${N8N_PROJECT_ID:-}" ]; then
  n8n import:workflow --input="$WORKFLOW_FILE" --projectId="$N8N_PROJECT_ID" \
    || n8n import:workflow --input="$WORKFLOW_FILE" \
    || echo "==> WARN: import fallo. Puede que el workflow ya exista."
else
  n8n import:workflow --input="$WORKFLOW_FILE" \
    || echo "==> WARN: import fallo. Puede que el workflow ya exista."
fi
echo "==> Import completado."

echo "==> Publicando workflow $WORKFLOW_ID..."
n8n publish:workflow --id="$WORKFLOW_ID" \
  || n8n update:workflow --id="$WORKFLOW_ID" --active=true \
  || echo "==> WARN: no se pudo publicar el workflow automaticamente."

# ── Arrancar n8n ────────────────────────────────────────────────────────────
echo "==> Arrancando n8n en puerto $N8N_PORT..."
exec n8n start
