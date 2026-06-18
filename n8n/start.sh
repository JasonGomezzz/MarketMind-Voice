#!/bin/sh
set -e

echo "==> Iniciando MarketMind n8n"
echo "==> PORT recibido de Render: ${PORT}"

export N8N_PORT=${PORT:-5678}
export N8N_PROTOCOL=https

# Render termina SSL en su edge (Cloudflare). Sin esto, express-rate-limit
# lanza ValidationError: ERR_ERL_UNEXPECTED_X_FORWARDED_FOR en cada request.
export N8N_PROXY_HOPS=1

# ── Esperar que PostgreSQL (Neon) acepte conexiones TCP ────────────────────
# Neon puede tardar 2-5s en salir de cold start. Sin este wait, n8n
# import:workflow falla con "Database connection timed out" → webhooks sin
# registrar → 503 en cada POST al webhook de marketmind.
wait_for_db() {
  echo "==> Verificando conexion TCP a PostgreSQL (Neon)..."
  RETRIES=15
  while [ $RETRIES -gt 0 ]; do
    node -e "
const net = require('net');
const host = process.env.DB_POSTGRESDB_HOST || 'localhost';
const port = parseInt(process.env.DB_POSTGRESDB_PORT || '5432');
const sock = net.createConnection(port, host);
sock.on('connect', () => { process.exit(0); });
sock.on('error', () => { process.exit(1); });
setTimeout(() => { process.exit(1); }, 4000);
" 2>/dev/null && echo "==> PostgreSQL disponible." && return 0

    echo "==> PostgreSQL no disponible. Reintentando en 3s... ($RETRIES restantes)"
    RETRIES=$((RETRIES - 1))
    sleep 3
  done
  echo "==> WARN: PostgreSQL no respondio en tiempo. n8n intentara conectar de todas formas."
}

wait_for_db

# ── Importar workflow ───────────────────────────────────────────────────────
# --projectId evita workflows huerfanos (sin shared_workflow row → no aparecen
# en UI y no registran webhooks). Si N8N_PROJECT_ID está vacío, import igual
# funciona pero el workflow puede quedar fuera del proyecto por defecto.
echo "==> Importando workflow..."
if [ -n "${N8N_PROJECT_ID:-}" ]; then
  n8n import:workflow \
    --input=/home/node/workflow.json \
    --projectId="$N8N_PROJECT_ID" \
    || echo "==> WARN: import con projectId fallo. Intentando sin projectId..."  \
    && n8n import:workflow --input=/home/node/workflow.json \
    || echo "==> WARN: import fallo. Puede que el workflow ya exista con datos correctos."
else
  n8n import:workflow --input=/home/node/workflow.json \
    || echo "==> WARN: import fallo. Puede que el workflow ya exista."
fi
echo "==> Import completado."

# ── Activar workflow via publish (reemplaza update:workflow deprecado) ──────
# update:workflow --active=true está deprecado desde n8n 2.x y emite SIGTERM
# que reinicia el contenedor antes de que n8n arranque.
# publish:workflow escribe el estado activo en BD sin levantar el servidor.
echo "==> Activando workflow via publish..."
n8n publish:workflow --id="${N8N_WORKFLOW_ID:-QAkaxptDCI9ahjQU}" \
  || echo "==> WARN: publish fallo. n8n start activara el workflow al arrancar."

# ── Arrancar n8n ────────────────────────────────────────────────────────────
echo "==> Arrancando n8n en puerto $N8N_PORT..."
exec n8n start
