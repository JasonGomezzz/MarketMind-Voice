#!/bin/sh
set -e
export N8N_PORT=${PORT:-5678}

echo "Importando workflow MarketMind IA..."
n8n import:workflow --input=/home/node/workflow.json

# Activar el workflow ANTES de levantar el servidor: la activacion es lo que
# registra los webhooks (/webhook/marketmind, /webhook/marketmind-email) en la BD.
# Sin esto el import deja el workflow inactivo aunque el JSON diga active:true.
# --id usa el ID del JSON; si la BD virgen de Render reasigna el ID, --all cubre
# el caso (solo hay 1 workflow en esta instancia).
echo "Activando workflow para registrar webhooks..."
n8n update:workflow --id=QAkaxptDCI9ahjQU --active=true || n8n update:workflow --all --active=true

echo "Workflow importado y activo. Iniciando n8n en puerto $N8N_PORT..."
exec n8n start
