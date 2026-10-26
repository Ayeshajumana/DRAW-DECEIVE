web: python manage.py migrate && python manage.py seed_words && daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application
