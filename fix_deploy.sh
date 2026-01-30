#!/bin/bash
# Script de réparation de la synchronisation GitHub
# ------------------------------------------------

echo "1. Vérification du dossier..."
cd ~/Desktop/systemFactChecking

echo "2. Préparation des fichiers..."
git checkout master
git add .
git commit -m "fix: manual sync for deployment"

echo "3. Envoi forcé vers GitHub (Main)..."
# Force push master vers main
git push -f origin master:main

echo "---------------------------------------"
echo "✅ TERMINÉ ! Retournez voir GitHub maintenant."
echo "---------------------------------------"
