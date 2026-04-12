# Mawdah wa Rahmah (مودة ورحمة)

Django 5.2 (LTS) project: supervised matchmaking platform (MVT, SQLite by default).

**Repository:** [github.com/mustafajuba98/Mawdah-W-Rahmah](https://github.com/mustafajuba98/Mawdah-W-Rahmah)

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
python manage.py runserver
```

Copy `.env.example` to `.env` if you use environment variables.

## Roles

After `setup_roles`, assign users to Django groups `moderator` or `platform_admin` in the admin site.
