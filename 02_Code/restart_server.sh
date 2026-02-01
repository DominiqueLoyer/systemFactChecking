#!/bin/bash
echo "🛑 Arrêt des anciens processus..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:5000 | xargs kill -9 2>/dev/null

echo "📦 Vérification des dépendances..."
source venv/bin/activate
pip install flask_sqlalchemy psycopg2-binary flask_cors

echo "🚀 Démarrage du serveur SysCRED..."
export FLASK_ENV=development
python syscred/backend_app.py
