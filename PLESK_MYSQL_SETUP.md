# Plesk MySQL/MariaDB setup

1. Create a MySQL or MariaDB database in Plesk.
2. Add environment variables from [.env.example](.env.example).
3. Install dependencies from [requirements.txt](requirements.txt).
4. Run Django migrations.
5. Load fixture data from [libra/data.json](libra/data.json).

Suggested environment variables:
- USE_MYSQL=True
- MYSQL_DATABASE=your_database_name
- MYSQL_USER=your_database_user
- MYSQL_PASSWORD=your_database_password
- MYSQL_HOST=localhost
- MYSQL_PORT=3306
- ALLOWED_HOSTS=your-domain.kz,www.your-domain.kz

Suggested commands on the server:
- python manage.py migrate --noinput
- python manage.py collectstatic --noinput
- python manage.py loaddata data.json
