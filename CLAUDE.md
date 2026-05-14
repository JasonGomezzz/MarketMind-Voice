# MarketMind IA — Contexto del Proyecto

## Descripción

SaaS de automatización de campañas publicitarias con IA.

Proyecto académico Tecsup IV ciclo, evaluado con rúbrica SCRUM.

## Stack oficial

- Backend: Django REST Framework + simplejwt + Python 3.11.9
- Base de datos: PostgreSQL ([Neon.tech](http://Neon.tech))
- Automatización IA: n8n + Gemini 2.0 Flash
- Frontend: React 18 + Vite + Tailwind + Axios + Recharts
- Mobile: Android Kotlin + Jetpack Compose + Retrofit + Hilt
- Contenedores: Docker + Docker Compose
- Deploy: Render (backend) + Vercel (frontend)

## Arquitectura

Monolito modular. Separación estricta de responsabilidades.

- Django → lógica de negocio y API REST
- n8n → orquesta workflows y automatizaciones
- Gemini → solo genera contenido IA
- PostgreSQL → fuente de verdad
- React → solo presentación

## Sprints

- Sprint 1: HU1-HU4 (auth + n8n + Gemini)
- Sprint 2: HU5-HU10 (campañas + React)
- Sprint 3: HU11-HU15 (Kotlin mobile)
- Sprint 4: HU16-HU20 (emails + analytics + deploy)

## Reglas de código

- Type hints obligatorios
- Docstrings en servicios
- Manejo centralizado de errores
- Respuestas API: {success, message, data}
- Settings: [base.py](http://base.py) / [dev.py](http://dev.py) / [prod.py](http://prod.py)
- Variables de entorno en .env, nunca hardcodeadas
- Commits: feat: / fix: / refactor: / docs:

## Seguridad

- CORS whitelist solo orígenes permitidos
- Rate limiting en register y login
- Django ORM siempre, nunca SQL raw
- JWT blacklist activado
- Input sanitization en todos los endpoints

## Higiene de sesión

Higiene de sesión 

Si detectas que llevamos más de ~30-40 mensajes 
en la misma sesión y noto que repites contexto,
Ignoras reglas de este CLAUDE.md, o sugieres cosas 
que ya descartamos, sugiéreme ‘/clear’ o cerrar la sesión.

No intentes seguir si la sesión está envenenada: es peor el remiendo que la pausa.

## Estado actual del Sprint 1
- HU1 (Registro usuario): ✅ Completa
- HU2 (Login JWT): ✅ Completa
- HU3 (Webhook n8n): ✅ Completa — POST /webhook/marketmind, 200 OK en 88ms
- HU4 (Gemini): HU4 está ✅,  Completa — agregar nodo HTTP Request en n8n

## Contexto técnico actual
- n8n corriendo en Docker localhost:5678
- Workflow "My workflow" activo con Webhook + Respond to Webhook
- ngrok URL cambia cada sesión — relanzar con: ngrok http 5678
- GEMINI_API_KEY configurada en .env
- venv en Mac: source backend/venv_mac/bin/activate
- Docker levantar con: docker compose up -d postgres n8n

## Observaciones críticas

1. Frontend es React + Vite, NO Next.js
2. Todo va directo en repo 2026-1-4c24-pi-2b
3. Kotlin es Sprint 3, no antes
4. Deploy: Render + Vercel + [Neon.tech](http://Neon.tech) + APK Android
5. Obsidian es documentación personal, no va al repo

