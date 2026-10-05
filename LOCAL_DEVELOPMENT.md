# Ejecución local consistente

Usa una sola instancia de Spring Boot: el contenedor Docker. No ejecutes
`mvn spring-boot:run` al mismo tiempo. Apache puede seguir usando su puerto.

| Servicio | Dirección desde Windows |
|---|---|
| Web | http://localhost:5173 |
| Django | http://localhost:8000 |
| Spring Boot | http://localhost:8081 |
| PostgreSQL | localhost:5435 |
| Redis | localhost:6379 |
| n8n | http://localhost:5678 |

Spring escucha en 8080 **dentro** de Docker y se publica en 8081 en Windows.
El `.env` raíz usa `SPRINGBOOT_HOST_PORT=8081`, `backend/.env` usa
`SPRINGBOOT_INTERNAL_URL=http://localhost:8081` y `frontend/.env` usa
`VITE_USER_API_URL=http://localhost:8081`. Las tareas de VS Code ya coinciden.

Desde la raíz:

```powershell
docker compose up -d --build postgres redis n8n springboot
```

En otra terminal:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

En otra terminal:

```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
```

Para revisar la API: `Invoke-RestMethod http://localhost:8081/actuator/health`.
Reinicia Django/Vite después de modificar sus archivos `.env`.
Si 8081 está ocupado, identifica el proceso y cierra solo la instancia duplicada
del proyecto; no cierres procesos ajenos automáticamente.

## Pruebas Spring

Las pruebas no usan PostgreSQL real ni envían correos; comprueban permisos,
cuentas suspendidas, JWT revocados, propiedad de campañas, valoración,
aprobación, rechazo y conflictos de versión.

Usa JDK 21 (igual que Docker y CI). En esta laptop:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
cd springboot
mvn test
```

Esto cambia Java solo en esa terminal. El Mockito de esta versión del proyecto
no es compatible con el JDK 25 instalado también en la laptop.
