source venv/bin/activate

# https://stackoverflow.com/a/43929298/8608146
watchmedo auto-restart -d . -p '**/*.py' -- python scripts/celery.py
