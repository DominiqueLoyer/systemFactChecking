#!/bin/bash
# Script de déploiement vers HuggingFace Spaces
# Usage: ./deploy_huggingface.sh

set -e

# Configuration
HF_SPACE="DomLoyer/syscred"
DEPLOY_DIR="$HOME/syscred-hf-deploy"

echo "🚀 Déploiement SysCRED vers HuggingFace Spaces"
echo "================================================"

# Nettoyer et créer le répertoire de déploiement
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copier les fichiers HuggingFace
echo "📁 Copie des fichiers de configuration..."
cp huggingface_space/Dockerfile "$DEPLOY_DIR/"
cp huggingface_space/README.md "$DEPLOY_DIR/"
cp huggingface_space/requirements.txt "$DEPLOY_DIR/"

# Copier le module syscred
echo "📦 Copie du module syscred..."
cp -r 02_Code/syscred "$DEPLOY_DIR/"

# Supprimer les fichiers inutiles
echo "🧹 Nettoyage..."
find "$DEPLOY_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name ".DS_Store" -delete 2>/dev/null || true

echo ""
echo "✅ Fichiers préparés dans: $DEPLOY_DIR"
echo ""
echo "📋 Prochaines étapes manuelles:"
echo "================================"
echo "1. Connectez-vous à HuggingFace:"
echo "   huggingface-cli login"
echo ""
echo "2. Clonez votre Space:"
echo "   cd $HOME"
echo "   git clone https://huggingface.co/spaces/$HF_SPACE syscred-space"
echo ""
echo "3. Copiez les fichiers:"
echo "   cp -r $DEPLOY_DIR/* $HOME/syscred-space/"
echo ""
echo "4. Poussez vers HuggingFace:"
echo "   cd $HOME/syscred-space"
echo "   git add ."
echo "   git commit -m 'Deploy SysCRED with PyTorch'"
echo "   git push"
echo ""
echo "🎉 Votre Space sera disponible sur:"
echo "   https://huggingface.co/spaces/$HF_SPACE"
