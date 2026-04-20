import json
import os
import subprocess
import sys
from pathlib import Path

import psycopg

ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT_DIR.parent
FIXTURE_PATH = WORKSPACE_ROOT / 'sqlite_to_postgres.json'


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


for candidate in (WORKSPACE_ROOT / '.env', ROOT_DIR / '.env'):
    load_env_file(candidate)


PYTHON = sys.executable
MANAGE_PY = str(ROOT_DIR / 'manage.py')
COUNT_SNIPPET = (
    "from django.apps import apps; import json; "
    "print(json.dumps({m._meta.label:m.objects.count() for m in apps.get_models()}, ensure_ascii=False, sort_keys=True))"
)


def run_manage(args: list[str], *, use_postgres: bool, stdout=None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['USE_POSTGRES'] = 'True' if use_postgres else 'False'
    env['PYTHONIOENCODING'] = 'utf-8'
    command = [PYTHON, MANAGE_PY, *args]
    print('RUN:', ' '.join(command))
    return subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        encoding='utf-8',
        stdout=stdout,
        stderr=subprocess.PIPE if stdout is not None else None,
        check=True,
    )


def ensure_postgres_database() -> None:
    db_name = os.getenv('POSTGRES_DB', os.getenv('PGDATABASE', os.getenv('DB_NAME', 'libra_db')))
    db_user = os.getenv('POSTGRES_USER', os.getenv('PGUSER', os.getenv('DB_USER', 'libra_admin')))
    db_password = os.getenv('POSTGRES_PASSWORD', os.getenv('PGPASSWORD', os.getenv('DB_PASSWORD', 'password')))
    db_host = os.getenv('POSTGRES_HOST', os.getenv('PGHOST', os.getenv('DB_HOST', 'localhost')))
    db_port = int(os.getenv('POSTGRES_PORT', os.getenv('PGPORT', os.getenv('DB_PORT', '5432'))))

    conn = psycopg.connect(
        host=db_host,
        port=db_port,
        dbname='postgres',
        user=db_user,
        password=db_password,
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (db_name,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f'Created PostgreSQL database: {db_name}')
            else:
                print(f'PostgreSQL database already exists: {db_name}')
    finally:
        conn.close()


def parse_counts(output: str) -> dict[str, int]:
    start = output.find('{')
    end = output.rfind('}')
    if start == -1 or end == -1:
        raise RuntimeError(f'Could not parse model counts from output:\n{output}')
    return json.loads(output[start:end + 1])


def get_counts(*, use_postgres: bool) -> dict[str, int]:
    env = os.environ.copy()
    env['USE_POSTGRES'] = 'True' if use_postgres else 'False'
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        [PYTHON, MANAGE_PY, 'shell', '-c', COUNT_SNIPPET],
        cwd=ROOT_DIR,
        env=env,
        text=True,
        encoding='utf-8',
        capture_output=True,
        check=True,
    )
    return parse_counts(result.stdout)


def load_fixture_into_postgres() -> None:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'libra.settings'
    os.environ['USE_POSTGRES'] = 'True'

    import django

    django.setup()

    from django.contrib.auth.models import User
    from django.core.management import call_command
    from django.db.models.signals import post_save
    from main.models import create_user_profile, save_user_profile

    post_save.disconnect(create_user_profile, sender=User)
    post_save.disconnect(save_user_profile, sender=User)
    try:
        call_command('flush', interactive=False)
        call_command('loaddata', str(FIXTURE_PATH))
    finally:
        post_save.connect(create_user_profile, sender=User)
        post_save.connect(save_user_profile, sender=User)


def main() -> None:
    ensure_postgres_database()
    run_manage(['migrate', '--noinput'], use_postgres=True)

    with FIXTURE_PATH.open('w', encoding='utf-8') as fixture:
        run_manage(
            [
                'dumpdata',
                '--exclude', 'auth.permission',
                '--exclude', 'contenttypes',
                '--natural-foreign',
                '--natural-primary',
                '--indent', '2',
            ],
            use_postgres=False,
            stdout=fixture,
        )
    print(f'SQLite export saved to: {FIXTURE_PATH}')

    load_fixture_into_postgres()

    sqlite_counts = get_counts(use_postgres=False)
    postgres_counts = get_counts(use_postgres=True)

    print('\nSQLite counts:')
    print(json.dumps(sqlite_counts, ensure_ascii=False, indent=2, sort_keys=True))
    print('\nPostgreSQL counts:')
    print(json.dumps(postgres_counts, ensure_ascii=False, indent=2, sort_keys=True))

    if sqlite_counts != postgres_counts:
        raise SystemExit('Count verification failed: SQLite and PostgreSQL data differ.')

    print('\nMigration completed successfully. SQLite and PostgreSQL counts match exactly.')


if __name__ == '__main__':
    main()
