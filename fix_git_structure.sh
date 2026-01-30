#!/bin/bash
# Script de réparation de la structure Git
# ----------------------------------------

echo "1. Suppression du git imbriqué..."
# On supprime le dossier .git qui est DANS le sous-dossier (ce qui cause l'erreur)
rm -rf systemFactChecking/.git

echo "2. Nettoyage du cache git..."
git rm --cached systemFactChecking

echo "3. Ajout propre des fichiers..."
git add .
git commit -m "fix: resolve embedded git repository issue"

echo "4. Envoi vers GitHub..."
git push -f origin master:main

echo "---------------------------------------"
echo "✅ TERMINÉ ! Vous pouvez maintenant faire votre Release."
echo "---------------------------------------"
