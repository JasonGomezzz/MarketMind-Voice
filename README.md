[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Q8MxYa_E)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23827676&assignment_repo_type=AssignmentRepo)

======================================
 MARKETMIND IA — CÓMO CORRER EL PROYECTO
======================================

REQUISITOS PREVIOS:
- Python 3.11+ instalado
- Docker Desktop instalado y corriendo
- Node.js 18+ instalado
- Git

PASOS EN ORDEN:

1. CLONAR Y ENTRAR
   git clone https://github.com/Tecsupsoft/2026-1-4c24-pi-2b
   cd 2026-1-4c24-pi-2b

2. COPIAR EL .env (pedírselo a Jason o Anderson)
   Pegar el archivo .env dentro de la carpeta /backend

3. LEVANTAR DOCKER (PostgreSQL + Redis)
   docker-compose up -d
   Verificar que estén UP: docker-compose ps

4. CREAR Y ACTIVAR VENV
   cd backend
   python -m venv venv

   Windows:
   venv\Scripts\activate

   Mac/Linux:
   source venv/bin/activate

   Verificar que aparezca (venv) al inicio de la terminal

5. INSTALAR DEPENDENCIAS
   pip uninstall psycopg2 psycopg2-binary -y
   pip install -r requirements.txt
   pip install psycopg2-binary

   (el paso de uninstall + reinstall al final es obligatorio en Windows)

6. MIGRAR BASE DE DATOS
   python manage.py migrate

7. CREAR USUARIO DE PRUEBA
   python manage.py shell

   Pegar esto:
   from django.contrib.auth import get_user_model
   User = get_user_model()
   u = User.objects.create_user(email='marketero@test.com', password='test1234')
   u.is_active = True
   u.save()
   print("OK:", u.email)

   Salir del shell: exit()

8. CORRER EL BACKEND
   python manage.py runserver
   Debe verse: Starting development server at http://127.0.0.1:8000/

9. CORRER EL FRONTEND (nueva terminal)
   cd frontend
   npm install
   npm run dev
   Abrir: http://localhost:5173

LOGIN:
   Email: marketero@test.com
   Password: test1234

NOTAS IMPORTANTES:
- Siempre tener Docker corriendo ANTES de levantar el backend
- Siempre activar el venv antes de cualquier comando Python
- El .env NUNCA se sube al repo, pedírselo al equipo
- En Windows siempre usar psycopg2-binary, nunca psycopg2 solo
======================================