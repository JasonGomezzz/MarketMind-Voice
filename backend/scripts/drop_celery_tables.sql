-- Limpieza de tablas huérfanas de Celery (decisión del proyecto: NO Celery,
-- la asincronía vive en n8n). Las apps django_celery_beat/django_celery_results
-- fueron retiradas de INSTALLED_APPS el 4 jul 2026; estas tablas quedaron
-- huérfanas en la BD. Correr una vez en cada entorno (local ya aplicado;
-- PENDIENTE en Neon prod via psql o SQL Editor de Neon).
-- Es seguro: ninguna otra tabla las referencia y el código no las usa.

BEGIN;
DROP TABLE IF EXISTS django_celery_results_chordcounter CASCADE;
DROP TABLE IF EXISTS django_celery_results_groupresult CASCADE;
DROP TABLE IF EXISTS django_celery_results_taskresult CASCADE;
DROP TABLE IF EXISTS django_celery_beat_periodictask CASCADE;
DROP TABLE IF EXISTS django_celery_beat_periodictasks CASCADE;
DROP TABLE IF EXISTS django_celery_beat_clockedschedule CASCADE;
DROP TABLE IF EXISTS django_celery_beat_crontabschedule CASCADE;
DROP TABLE IF EXISTS django_celery_beat_intervalschedule CASCADE;
DROP TABLE IF EXISTS django_celery_beat_solarschedule CASCADE;
DELETE FROM django_migrations WHERE app IN ('django_celery_beat', 'django_celery_results');
COMMIT;
