#!/bin/bash
# -*- coding: utf-8 -*-
# SysCRED Quick Start Script
# Gère l'installation et le démarrage automatique avec détection des problèmes

set -e  # Arrêter sur erreur

echo "🚀 SysCRED Quick Start"
echo "======================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier qu'on est dans le bon répertoire
if [ ! -f "syscred/backend_app.py" ]; then
    echo -e "${RED}❌ Erreur: Lancez ce script depuis ~/Desktop/systemFactChecking/02_Code${NC}"
    echo "   cd ~/Desktop/systemFactChecking/02_Code"
    echo "   bash ../quick_start.sh"
    exit 1
fi

echo -e "${GREEN}✅ Répertoire correct${NC}"

# 2. Activer l'environnement virtuel
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  venv non trouvé, création...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✅ Environment virtuel activé${NC}"

# 3. Détecter la version de Python
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "🐍 Python version: $PYTHON_VERSION"

# 4. Installer les dépendances selon la version Python
echo ""
echo "📦 Installation des dépendances..."

# Dépendances de base (toujours installées)
pip install -q --upgrade pip
pip install -q flask flask-cors requests beautifulsoup4 nltk rdflib python-dotenv pydantic psycopg2-binary supabase

# PyTorch et Transformers (si Python <= 3.13)
if python -c "import sys; exit(0 if sys.version_info >= (3, 14) else 1)" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Python 3.14+ détecté - PyTorch non disponible${NC}"
    echo "   → Mode sans ML activé automatiquement"
    export SYSCRED_LOAD_ML_MODELS="false"
    ML_MODE="disabled"
else
    echo "   Installation de PyTorch et Transformers..."
    pip install -q torch transformers 2>/dev/null || {
        echo -e "${YELLOW}⚠️  PyTorch non disponible - Mode sans ML${NC}"
        export SYSCRED_LOAD_ML_MODELS="false"
        ML_MODE="disabled"
    }
    ML_MODE="enabled"
fi

echo -e "${GREEN}✅ Dépendances installées${NC}"

# 5. Trouver un port libre
PORT=5001
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    echo -e "${YELLOW}⚠️  Port $PORT occupé${NC}"
    PORT=$((PORT + 1))
done
echo -e "${GREEN}✅ Port libre: $PORT${NC}"

# 6. Configuration des variables d'environnement
export DATABASE_URL='postgresql://postgres:FactCheckingSystem2026_test@db.zmluirvqfkmfazqitqgi.supabase.co:5432/postgres'
export SYSCRED_PORT=$PORT
export SYSCRED_HOST="0.0.0.0"
export SYSCRED_DEBUG="true"
export SYSCRED_ENV="development"

echo ""
echo "🔧 Configuration:"
echo "   - Port: $PORT"
echo "   - Modèles ML: $ML_MODE"
echo "   - Database: Supabase"

# 7. Test connexion DB (rapide)
echo ""
echo "🔌 Test connexion Supabase..."
python3 -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect('$DATABASE_URL', connect_timeout=3)
    print('✅ Connexion Supabase réussie')
    conn.close()
except Exception as e:
    print(f'⚠️  Avertissement DB: {str(e)[:60]}...')
    print('   Le serveur démarrera quand même')
" || echo "⚠️  Test DB ignoré"

# 8. Créer le fichier .env s'il n'existe pas
if [ ! -f "syscred/.env" ]; then
    echo ""
    echo "📝 Création du fichier .env..."
    cat > syscred/.env << ENVEOF
DATABASE_URL=$DATABASE_URL
SYSCRED_PORT=$PORT
SYSCRED_HOST=0.0.0.0
SYSCRED_DEBUG=true
SYSCRED_LOAD_ML_MODELS=$SYSCRED_LOAD_ML_MODELS
SYSCRED_ENV=development
ENVEOF
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
fi

# 9. Démarrer le serveur
echo ""
echo "=========================="
echo "🌐 Démarrage du serveur..."
echo "=========================="
echo ""
echo "📍 URL: http://localhost:$PORT"
echo "📍 Health: http://localhost:$PORT/api/health"
echo "📍 Docs: http://localhost:$PORT/api/config"
echo ""
echo "   Ctrl+C pour arrêter"
echo ""

python syscred/backend_app.py
