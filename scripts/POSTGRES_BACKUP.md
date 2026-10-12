# Respaldo manual local de PostgreSQL

Verificación del 11 de octubre de 2026: primer respaldo local generado y restauración ejecutada
correctamente en una base nueva de prueba con 27 tablas. La base original no se modificó.
Esto no demuestra continuidad periódica, respaldo externo ni que cada función de la aplicación
se haya probado contra la copia. No conectar la aplicación a una restauración sin revisión.

Desde la raíz del proyecto, con Docker y `marketmind_postgres` activos:

```powershell
.\scripts\backup-postgres.ps1
```

Guarda un archivo custom de `pg_dump` y SHA256 en `backups/postgres/`, ignorado por Git.
Los nombres son únicos; no reemplaza respaldos anteriores. Se valida el índice con
`pg_restore --list`. Esa comprobación NO sustituye una restauración completa de prueba.
El SHA256 detecta cambios accidentales; no cifra ni autentica el archivo frente a manipulación.

## Restaurar a una base nueva, nunca sobre la base de la aplicación

Use la ruta exacta emitida al crear el respaldo:

```powershell
.\scripts\restore-postgres-copy.ps1 -BackupFile 'C:\ruta\exacta\nexomark-respaldo.dump'
```

Se verifica SHA256 y se crea una base `nexomark_restore_...`. Si el nombre existe, falla;
no borra ni limpia bases. No cambia `.env` ni conecta la aplicación a la copia.
La base de prueba contiene datos privados igual que la original. Si falla la restauración,
la copia incompleta se conserva y se informa para revisión; no se elimina automáticamente.
Compruebe tablas/datos y compatibilidad antes de considerar probado el procedimiento.
No activar flujos de publicación ni correo en la copia. Cualquier cambio de la base principal
o eliminación de la base de prueba requiere una decisión separada, con destino verificado.

## Alcance y límites

- Solo respalda la base indicada por `POSTGRES_DB` del contenedor. No exporta sus variables privadas.
- No incluye `.env`, clave de cifrado social, configuración/workflows n8n ni archivos externos.
  Conservar la configuración privada por un canal seguro; sin la clave original las credenciales
  sociales cifradas no se pueden recuperar aunque el dump exista.
- El dump incluye datos personales, hashes y credenciales sociales cifradas. No es un archivo
  cifrado: restringir su acceso y no enviarlo a GitHub, TikTok ni chats.
- Una copia en la misma laptop no protege ante pérdida o fallo de todo el equipo.
  Una segunda copia cifrada en otro medio requiere acordar ubicación y custodia.
- No se configuraron tareas periódicas ni eliminación tras 30 días. La retención de 30 días
  sigue siendo propuesta; no borrar automáticamente copias sin una política aprobada.
- Revisar espacio libre, compatibilidad de PostgreSQL y permisos locales antes de cada ejecución.
- Los temporales de dump se retiran del contenedor por ruta exacta; el respaldo local se conserva.
