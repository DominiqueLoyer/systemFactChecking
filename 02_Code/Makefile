# Makefile for SysCRED Project
# Usage: make [target]
#
# Targets:
#   install    - Install all dependencies
#   install-ml - Install ML dependencies (PyTorch, Transformers)
#   start      - Start the Flask backend server
#   start-lite - Start server without ML models (fast)
#   test       - Run health checks
#   test-db    - Test Supabase connection
#   clean      - Clean Python cache files
#   setup      - First-time setup (venv + deps)
#   help       - Show this help message

.PHONY: help install install-ml start start-lite test test-db clean setup

# Variables
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python
DB_URL := postgresql://postgres:FactCheckingSystem2026_test@db.zmluirvqfkmfazqitqgi.supabase.co:5432/postgres
PORT := 5002

# Couleurs pour output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Cible par défaut
.DEFAULT_GOAL := help

help:
	@echo "SysCRED - Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "  make setup        - Première installation complète"
	@echo "  make install      - Installer les dépendances de base"
	@echo "  make install-ml   - Installer PyTorch et Transformers"
	@echo "  make start        - Démarrer le serveur (avec ML)"
	@echo "  make start-lite   - Démarrer sans ML (rapide)"
	@echo "  make test         - Test de santé de l'API"
	@echo "  make test-db      - Tester la connexion Supabase"
	@echo "  make clean        - Nettoyer les fichiers cache"
	@echo ""
	@echo "Exemples:"
	@echo "  make setup        # Première fois"
	@echo "  make start-lite   # Démarrage rapide"
	@echo ""

# Créer l'environnement virtuel
$(VENV)/bin/activate: requirements.txt
	@echo "$(GREEN)✅ Création de l'environnement virtuel...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✅ Environment créé$(NC)"

# Setup complet (première installation)
setup: $(VENV)/bin/activate
	@echo "$(GREEN)✅ Configuration initiale de SysCRED...$(NC)"
	$(PIP) install --upgrade pip
	$(MAKE) install
	@echo ""
	@echo "$(GREEN)===========================$(NC)"
	@echo "$(GREEN)✅ Setup terminé!$(NC)"
	@echo "$(GREEN)===========================$(NC)"
	@echo ""
	@echo "Prochaines étapes:"
	@echo "  make start-lite   # Démarrer sans ML (rapide)"
	@echo "  make install-ml   # Installer les modèles ML"
	@echo "  make start        # Démarrer avec ML"
	@echo ""

# Installer les dépendances de base
install: $(VENV)/bin/activate
	@echo "$(GREEN)📦 Installation des dépendances de base...$(NC)"
	$(PIP) install -q flask flask-cors requests beautifulsoup4 nltk rdflib python-dotenv pydantic psycopg2-binary supabase
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

# Installer les dépendances ML (peut échouer sur Python 3.14+)
install-ml: $(VENV)/bin/activate
	@echo "$(YELLOW)🧠 Installation des modèles ML...$(NC)"
	@$(PIP) install torch transformers 2>/dev/null && echo "$(GREEN)✅ ML installé$(NC)" || echo "$(RED)❌ PyTorch non disponible (Python 3.14+?)$(NC)"

# Démarrer le serveur avec ML
start: $(VENV)/bin/activate
	@echo "$(GREEN)🚀 Démarrage du serveur SysCRED (avec ML)...$(NC)"
	@echo "   Port: $(PORT)"
	@echo "   URL: http://localhost:$(PORT)"
	@echo ""
	DATABASE_URL=$(DB_URL) \
	SYSCRED_PORT=$(PORT) \
	SYSCRED_LOAD_ML_MODELS=true \
	SYSCRED_DEBUG=true \
	$(PYTHON_VENV) syscred/backend_app.py

# Démarrer sans ML (rapide, fonctionne toujours)
start-lite: $(VENV)/bin/activate
	@echo "$(GREEN)🚀 Démarrage rapide (sans ML)...$(NC)"
	@echo "   Port: $(PORT)"
	@echo "   URL: http://localhost:$(PORT)"
	@echo "   Modèles ML: Désactivés"
	@echo ""
	DATABASE_URL=$(DB_URL) \
	SYSCRED_PORT=$(PORT) \
	SYSCRED_LOAD_ML_MODELS=false \
	SYSCRED_DEBUG=true \
	$(PYTHON_VENV) syscred/backend_app.py

# Tester l'API
test:
	@echo "$(YELLOW)🧪 Test de santé de l'API...$(NC)"
	@curl -s http://localhost:$(PORT)/api/health | python3 -m json.tool || echo "$(RED)❌ Serveur non accessible$(NC)"

# Tester la connexion Supabase
test-db: $(VENV)/bin/activate
	@echo "$(YELLOW)🔌 Test connexion Supabase...$(NC)"
	@$(PYTHON_VENV) -c "
import psycopg2; \
import sys; \
try: \
    conn = psycopg2.connect('$(DB_URL)', connect_timeout=5); \
    print('✅ Connexion Supabase réussie'); \
    cursor = conn.cursor(); \
    cursor.execute('SELECT version()'); \
    version = cursor.fetchone()[0]; \
    print(f'   PostgreSQL: {version[:50]}...'); \
    cursor.close(); \
    conn.close(); \
except Exception as e: \
    print(f'❌ Erreur: {e}'); \
    sys.exit(1)
"

# Nettoyer les fichiers cache
clean:
	@echo "$(YELLOW)🧹 Nettoyage...$(NC)"
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	find . -type f -name '*.pyo' -delete 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

# Afficher la configuration
config:
	@echo "Configuration SysCRED:"
	@echo "======================"
	@echo "Python: $$(python3 --version)"
	@echo "Port: $(PORT)"
	@echo "Database: Supabase"
	@echo "Venv: $(VENV)"
	@echo ""
