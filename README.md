[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Q8MxYa_E)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23827676&assignment_repo_type=AssignmentRepo)

# MarketMind IA - Como correr el proyecto

Guia para levantar el entorno local completo: PostgreSQL, Redis, n8n, Django,
Spring Boot y React.

## Requisitos previos

- Python 3.11 o 3.12 recomendado.
- Docker Desktop instalado y corriendo.
- Node.js 18 o superior.
- Git.

> Nota: si estas en WSL, ejecuta los comandos desde la terminal de WSL. Evita
> mezclar un `venv` creado en Windows con comandos ejecutados desde Linux/WSL.

## Puertos locales

- Django API: `http://localhost:8000`
- React/Vite: `http://localhost:5173`
- Spring Boot API: `http://localhost:8080`
- n8n: `http://localhost:5678`
- PostgreSQL desde tu maquina: `localhost:5433`
- PostgreSQL dentro de Docker: `postgres:5432`
- Redis: `localhost:6379`

Spring Boot escucha en `8080` dentro del contenedor y se publica en `8080`
en tu maquina.

## 1. Clonar y entrar al proyecto

```bash
git clone https://github.com/Tecsupsoft/2026-1-4c24-pi-2b
cd 2026-1-4c24-pi-2b
```

## 2. Configurar variables de entorno

### Backend Django

Pide el archivo `.env` al equipo o crea uno a partir de
`backend/.env.example`:

```bash
cp backend/.env.example backend/.env
```

Para desarrollo local con el `docker-compose.yml` de la raiz, verifica que
`backend/.env` tenga estos valores:

```env
DB_NAME=marketmind_db
DB_USER=marketmind_user
DB_PASSWORD=localpass123
DB_HOST=localhost
DB_PORT=5433
DB_SSLMODE=disable
DJANGO_SETTINGS_MODULE=core.settings.dev
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

`DB_PORT=5433` es importante: Docker expone PostgreSQL hacia tu maquina en
`5433`, aunque dentro de Docker el puerto siga siendo `5432`.

### Docker Compose / Spring Boot

Docker Compose lee variables desde un `.env` ubicado en la raiz del proyecto.
Este archivo es util para compartir el mismo `SECRET_KEY` entre Django y Spring
Boot, porque Spring Boot valida los JWT emitidos por Django.

Crea `.env` en la raiz con, como minimo:

```env
SECRET_KEY=django-insecure-dev-key-marketmind-2026-local
DB_NAME=marketmind_db
DB_USER=marketmind_user
DB_PASSWORD=localpass123
SPRINGBOOT_HOST_PORT=8080
INTERNAL_EVENT_TOKEN=dev-internal-event-token
GEMINI_API_KEY=tu-api-key-de-google-ai-studio
RESEND_API_KEY=tu-api-key-de-resend
RESEND_FROM_EMAIL=onboarding@resend.dev
```

Si tu `backend/.env` usa otro `SECRET_KEY`, copia exactamente el mismo valor en
el `.env` de la raiz.

n8n tambien lee variables desde el `.env` de la raiz. Si `GEMINI_API_KEY` solo
esta en `backend/.env`, n8n respondera el webhook pero Gemini fallara con 403.
Despues de cambiar estas variables, recrea n8n:

```bash
docker compose up -d --force-recreate n8n
```

Para que Django pueda avisar a Spring Boot cuando una campaña se envía al
cliente, agrega también en `backend/.env`:

```env
SPRINGBOOT_INTERNAL_URL=http://localhost:8080
INTERNAL_EVENT_TOKEN=dev-internal-event-token
```

El valor de `INTERNAL_EVENT_TOKEN` debe coincidir entre `.env` de la raiz y
`backend/.env`.

### Frontend React

Crea `frontend/.env`:

```bash
cp frontend/.env.example frontend/.env
```

Debe quedar asi para desarrollo local:

```env
VITE_API_URL=http://localhost:8000
VITE_USER_API_URL=http://localhost:8080
```

Vite no lee `.env.example` automaticamente; el archivo real debe llamarse
`frontend/.env`.

## 3. Levantar servicios base con Docker

Primero levanta PostgreSQL, Redis y n8n:

```bash
docker compose up -d postgres redis n8n
```

Verifica el estado:

```bash
docker compose ps
```

PostgreSQL debe aparecer como `healthy`.

## 4. Crear y activar el entorno virtual del backend

```bash
cd backend
python -m venv venv
```

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
venv\Scripts\activate.bat
```

Mac/Linux/WSL:

```bash
source venv/bin/activate
```

Verifica que aparezca `(venv)` al inicio de la terminal.

## 5. Instalar dependencias del backend

Con el `venv` activado y estando dentro de `backend`:

```bash
python -m pip install --upgrade pip
pip uninstall psycopg2 psycopg2-binary -y
pip install -r requirements.txt
pip install psycopg2-binary
```

El paso de desinstalar y reinstalar `psycopg2-binary` al final ayuda a evitar
problemas comunes en Windows.

## 6. Migrar la base de datos

Con Docker corriendo y el `venv` activado:

```bash
python manage.py migrate
```

Este paso crea las tablas que usan Django y Spring Boot. Si no se ejecuta,
Spring Boot puede fallar con errores como `missing table [campaigns]`.

## 7. Crear usuario de prueba

Abre el shell de Django:

```bash
python manage.py shell
```

Pega esto:

```python
from django.contrib.auth import get_user_model

User = get_user_model()

u, created = User.objects.get_or_create(
    email="marketero@test.com",
    defaults={
        "nombre": "Marketero Test",
        "rol": "marketero",
        "is_active": True,
    },
)
u.nombre = "Marketero Test"
u.rol = "marketero"
u.is_active = True
u.set_password("test1234")
u.save()

print("OK:", u.email, "created=", created)
```

Sal del shell:

```python
exit()
```

Credenciales de prueba:

```text
Email: marketero@test.com
Password: test1234
```

## 8. Correr el backend Django

Desde `backend`, con el `venv` activado:

```bash
python manage.py runserver
```

Debe verse algo similar a:

```text
Starting development server at http://127.0.0.1:8000/
```

Deja esta terminal abierta.

## 9. Levantar Spring Boot

En otra terminal, desde la raiz del proyecto:

```bash
docker compose up -d --build springboot
```

Verifica el health check:

```bash
curl http://localhost:8080/actuator/health
```

Respuesta esperada:

```json
{"status":"UP"}
```

## 10. Correr el frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre:

```text
http://localhost:5173
```

El dashboard del cliente se conecta por WebSocket a Spring Boot
(`ws://localhost:8080/ws/client-campaigns`) para recibir campañas nuevas sin
refrescar la página.

## Orden recomendado para volver a correr el proyecto

Cuando ya instalaste todo una vez:

```bash
docker compose up -d postgres redis n8n springboot
cd backend
source venv/bin/activate
python manage.py runserver
```

En otra terminal:

```bash
cd frontend
npm run dev
```

En Windows cambia `source venv/bin/activate` por el comando de activacion de
Windows indicado arriba.

## Problemas comunes

### Spring Boot no arranca y dice `missing table [campaigns]`

Faltan migraciones. Ejecuta:

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

Luego:

```bash
cd ..
docker compose up -d springboot
```

### Spring Boot no puede publicar el puerto 8080

Puedes cambiar el puerto publicado por Spring Boot desde el `.env` de la raiz.
Por defecto usa:

```text
http://localhost:8080
```

Si `8080` esta ocupado, edita `SPRINGBOOT_HOST_PORT` en el `.env` de la raiz y
actualiza tambien `VITE_USER_API_URL` en `frontend/.env` y
`SPRINGBOOT_INTERNAL_URL` en `backend/.env`.

### Login funciona en Django pero falla en pantallas del cliente

Revisa que `SECRET_KEY` sea exactamente igual en:

- `backend/.env`
- `.env` en la raiz del proyecto

Spring Boot necesita validar el mismo JWT que genera Django.

### El frontend no encuentra la API

Confirma que exista `frontend/.env` y que tenga:

```env
VITE_API_URL=http://localhost:8000
VITE_USER_API_URL=http://localhost:8080
```

Reinicia `npm run dev` despues de cambiar variables `VITE_*`.

### Error instalando `psycopg2`

Usa `psycopg2-binary`:

```bash
pip uninstall psycopg2 psycopg2-binary -y
pip install psycopg2-binary
```

### Docker no responde desde WSL

Abre Docker Desktop y verifica que la integracion con tu distro WSL este
activada. Luego prueba:

```bash
docker compose ps
```

## Notas importantes

- Siempre levanta Docker antes de ejecutar `python manage.py runserver`.
- Siempre activa el `venv` antes de usar comandos Python del backend.
- No subas archivos `.env` al repositorio.
- Despues de cambiar `.env` del frontend, reinicia Vite.
- Despues de cambiar `docker-compose.yml` o `.env` de la raiz, recrea el
  servicio afectado con `docker compose up -d <servicio>`.
