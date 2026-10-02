"""Run the existing SQLite suite with synthetic settings and disabled sockets."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    reports = root / "ci-artifacts"
    reports.mkdir(exist_ok=True)
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "core.settings.test",
        "SECRET_KEY": "ci-only-django-key-not-for-deployment-0123456789",
        "DB_NAME": "ci_unused", "DB_USER": "ci_unused", "DB_PASSWORD": "ci_unused",
        "DB_HOST": "127.0.0.1", "DB_PORT": "5432", "DB_SSLMODE": "disable",
        "REDIS_URL": "redis://127.0.0.1:1/0",
        "ALLOWED_HOSTS": "localhost,127.0.0.1,testserver",
        "USE_MOCK_AI": "True", "GEMINI_API_KEY": "", "RESEND_API_KEY": "",
        "N8N_WEBHOOK_BASE_URL": "http://127.0.0.1:1",
        "N8N_WEBHOOK_URL": "http://127.0.0.1:1",
        "SPRINGBOOT_INTERNAL_URL": "http://127.0.0.1:1",
        "INTERNAL_EVENT_TOKEN": "ci-only-internal-placeholder",
    }
    commands = [
        ["manage.py", "check", "--settings=core.settings.ci_checks"],
        ["manage.py", "makemigrations", "--check", "--dry-run", "--settings=core.settings.ci_checks"],
        ["-m", "pytest", "-q", "--no-cov", "--disable-socket",
         f"--junitxml={reports / 'django.xml'}"],
    ]
    for command in commands:
        print("Running: python " + " ".join(command), flush=True)
        result = subprocess.run([sys.executable, *command], cwd=root / "backend", env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
