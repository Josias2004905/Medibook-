#!/bin/sh

echo "Application Django : demarrage..."

echo "Application des migrations..."
python manage.py migrate --noinput

echo "Seed des donnees..."
python manage.py seed_data

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Lancement du serveur..."
exec "$@"
