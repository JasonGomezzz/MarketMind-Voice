# MarketMind IA — Contexto del Proyecto

## Descripción
SaaS de automatización de campañas publicitarias con IA,
dirigido a agencias digitales de marketing.
Permite generar copy + imagen de anuncios automáticamente con IA.
Proyecto académico Tecsup IV ciclo, evaluado con rúbrica SCRUM.
Soy Jason, único dev activo. Anderson y José documentan/testean
cuando hay entregas de laboratorio, pero el código lo hago yo.

## Modelo de negocio
Suscripción por plan con cuota de tokens de IA.
1 crédito = 1 generación o regeneración exitosa de IA.
Al agotar cuota: modo lectura (historial OK, creación bloqueada).
SuperAdmin resetea cuota o cambia plan.
HU18 gestiona planes y cuotas, no solo suspender cuentas.
Campo tokens_disponibles en modelo User (default=100).
Validar cuota ANTES de disparar n8n — nunca después.

## Stack oficial
- Backend: Django REST Framework + simplejwt + Python 3.11.9
- Base de datos: PostgreSQL local (Docker) + Neon.tech en producción
- Automatización IA: n8n + Gemini 2.0 Flash + Stability AI (imágenes, HU21)
- Frontend: React 18 + Vite + Tailwind + Axios + Recharts
- Mobile: Android Kotlin + Jetpack Compose + Retrofit + Hilt
- Contenedores: Docker + OrbStack (Mac)
- Deploy: Render (backend) + Vercel (frontend) + Neon.tech + APK Android
- n8n: local con ngrok en dev, n8n Cloud en producción

## Arquitectura
Monolito modular. Separación estricta de responsabilidades.
- Django → lógica de negocio y API REST
- n8n → orquesta workflows y automatizaciones
- Gemini → genera copy/texto publicitario
- Stability AI → genera imagen del anuncio (HU21, Sprint 4)
- PostgreSQL → fuente de verdad
- React → solo presentación

## Flujo IA completo (target Sprint 4)
Webhook → Gemini (copy) → Stability AI (imagen) →
Respond to Webhook {success, message, data:{copy, imagen_url}}
imagen_url se guarda en campo imagen_url del modelo Campaign.

## Flujo IA actual (Sprint 2, con mock)
USE_MOCK_AI=True → Django devuelve copy e imagen_url fijos
sin llamar a n8n ni Gemini. Para no quemar cuota en desarrollo.

## Sprints
- Sprint 1: HU1-HU4 (auth + n8n + Gemini) ✅ COMPLETO
- Sprint 2: HU5-HU10 (campañas + React) ← ACTIVO
- Sprint 3: HU11-HU15 (Kotlin mobile)
- Sprint 4: HU16-HU21 (emails + analytics + imágenes + deploy)

## Estado Sprint 1
- HU1 Registro usuario ✅
- HU2 Login JWT ✅
- HU3 Webhook n8n ✅ — POST /webhook/marketmind, 200 OK en 88ms
- HU4 Gemini ✅ — flujo Webhook→HTTP Request→Respond to Webhook
  Respond usa modo TEXT con JSON.stringify
  Devuelve {success, message, data:{generated}}

## Estado Sprint 2
- HU5 Modelo Campaign + FSM ✅ COMPLETO
- HU6 CampaignSerializer + endpoint + trigger_ia_generation() ← ACTIVO
- HU7 React Login + rutas protegidas (NO antes de HU6)
- HU8 Dashboard React tabla campañas
- HU9 Formulario React + panel resultado IA
- HU10 Editor WYSIWYG React
REGLA: NO empezar React hasta que HU5+HU6 funcionen con mock.

## Decisiones técnicas fijas
1. USE_MOCK_AI=True en .env para desarrollo. Cuando está activa,
   el endpoint devuelve texto/imagen fijos sin llamar a n8n.
2. Gemini 2.0 Flash para todo (dev y demo).
3. FSM Campaign: VALID_TRANSITIONS dict + método transition_to().
   Lanza InvalidTransitionError si la transición no es válida.
4. Stability AI para imágenes — HU21, Sprint 4, prometido al
   profesor. Campo imagen_url ya en Campaign desde HU5.
5. n8n Cloud para producción. Ngrok solo en desarrollo local.
6. Validar tokens_disponibles ANTES de disparar n8n, nunca después.
   Si tokens == 0: HTTP 402 con mensaje claro.

## Deuda técnica resuelta
- core/asgi.py creado (ASGI_APPLICATION lo declaraba en base.py)
- USE_MOCK_AI=False agregado a base.py y .env.example
- GEMINI_MODEL cambiado a gemini-2.0-flash en base.py
- STATICFILES_STORAGE movido de base.py a prod.py
- tokens_disponibles=100 agregado en create_user() de models.py

## Cómo arrancar el entorno (Mac)
1. docker compose --env-file backend/.env up -d postgres redis n8n
2. ngrok http 5678 (URL cambia cada sesión — solo desarrollo)
3. source backend/venv_mac/bin/activate
4. cd backend && python manage.py runserver

## Aprendizajes clave Sprint 1
- Gemini 2.0 Flash free tier: 20 RPD — se agota rápido en debug
- En n8n los datos del webhook se acceden con $json.body.*
- Respond to Webhook debe usar modo TEXT con JSON.stringify
- Los __pycache__ y venv NUNCA van al repo
- Redis debe estar corriendo para que el rate limiting funcione

## Reglas de código
- Type hints obligatorios en todas las funciones
- Docstrings en todos los servicios
- Manejo centralizado de errores con exceptions.py
- Respuestas API siempre: {success, message, data}
- Settings: base.py / dev.py / prod.py
- Variables de entorno en .env, nunca hardcodeadas
- Commits: feat: / fix: / refactor: / docs:
- Un commit por HU terminada

## Seguridad
- CORS whitelist solo orígenes permitidos
- Rate limiting en register y login (requiere Redis)
- Django ORM siempre, nunca SQL raw
- JWT blacklist activado
- Input sanitization en todos los endpoints

## Estructura backend
backend/
├── apps/
│   ├── authentication/
│   └── campaigns/
├── core/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── exceptions.py
├── services/
│   ├── gemini_service.py
│   └── n8n_service.py
├── requirements/
│   ├── base.txt
│   └── dev.txt
├── manage.py
└── Dockerfile

## Observaciones críticas
1. Frontend es React + Vite, NO Next.js
2. Todo va directo en repo 2026-1-4c24-pi-2b
3. Kotlin es Sprint 3, no antes
4. Deploy: Render + Vercel + Neon.tech + APK Android
5. Anderson y José aparecen en el backlog pero Jason hace
   el código. Documentar evidencias como equipo para la
   rúbrica es válido académicamente.
6. n8n-mcp y n8n-skills instalados en Claude Code para
   construir flujos n8n complejos en Sprint 4.

## Repo
github.com/Tecsupsoft/2026-1-4c24-pi-2b

## Higiene de sesión
Si llevamos más de 30-40 mensajes y notas que repito contexto
o ignoro reglas de este archivo, sugiéreme abrir sesión nueva.