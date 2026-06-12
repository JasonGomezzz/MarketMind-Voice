#!/bin/sh
echo "==> Iniciando MarketMind n8n"
echo "==> PORT recibido de Render: ${PORT}"

# n8n escucha en N8N_PORT (env var). NO existe flag --port en `n8n start`:
# el puerto SOLO se controla por esta variable. Render inyecta $PORT y espera
# que el servicio escuche ahi; si no, mata el contenedor (exit 1).
export N8N_PORT=${PORT:-5678}
export N8N_PROTOCOL=https

# La DB de n8n se configura por env vars en Render (DB_TYPE=postgresdb +
# DB_POSTGRESDB_* apuntando a Neon, schema 'n8n'). NO se fuerza aqui:
# si el script forzara SQLite, n8n no persistiria en el disco efimero de
# Render free tier y crashearia con "Database is not ready" (503).

echo "==> Importando workflow..."
n8n import:workflow --input=/home/node/workflow.json
IMPORT_EXIT=$?
echo "==> Import exit code: $IMPORT_EXIT"

if [ $IMPORT_EXIT -eq 0 ]; then
  # El import deja el workflow INACTIVO (n8n loggea "Deactivating workflow").
  # Activar registra los webhooks /webhook/marketmind y /webhook/marketmind-email.
  echo "==> Activando workflow..."
  # publish:workflow reemplaza al deprecado update:workflow --active=true
  # (el log de Render lo confirma: "Please use: publish:workflow").
  # Publica/activa el workflow y registra sus webhooks.
  n8n publish:workflow --id=QAkaxptDCI9ahjQU \
    || n8n update:workflow --id=QAkaxptDCI9ahjQU --active=true \
    || echo "==> WARN: activacion fallo, n8n start intentara activar"
else
  echo "==> WARN: import fallo con $IMPORT_EXIT, continuando de todas formas"
fi

echo "==> Arrancando n8n en puerto $N8N_PORT..."
exec n8n start
