#!/bin/bash
# ============================================
# save_to_notes.sh
# Script pour sauvegarder la documentation vers Obsidian et Notion
# 
# Usage: ./save_to_notes.sh [chemin_fichier_optionnel]
# 
# Par défaut: Sauvegarde SysCRED_Documentation.md
# ============================================

# Configuration - MODIFIEZ CES CHEMINS SELON VOTRE SETUP
OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-/Users/bk280625/documents041025/Obsidian_UQAM25_bk051225}"
NOTION_CLIPBOARD=true  # true = copie dans le presse-papiers pour Notion

# Couleurs pour output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Date pour le versioning
DATE=$(date +%Y%m%d)
DATETIME=$(date +"%Y-%m-%d %H:%M")

# Fichier source (argument ou défaut)
if [ -n "$1" ]; then
    DOC_SOURCE="$1"
else
    DOC_SOURCE="/Users/bk280625/documents041025/MonCode/syscred/SysCRED_Documentation.md"
fi

# Vérifier que le fichier existe
if [ ! -f "$DOC_SOURCE" ]; then
    echo -e "${YELLOW}⚠️  Fichier non trouvé: $DOC_SOURCE${NC}"
    exit 1
fi

# Nom du fichier sans chemin
FILENAME=$(basename "$DOC_SOURCE" .md)

echo -e "${BLUE}📝 Sauvegarde de: $DOC_SOURCE${NC}"
echo "   Date: $DATETIME"
echo ""

# ============================================
# 1. OBSIDIAN
# ============================================
echo -e "${BLUE}📚 OBSIDIAN${NC}"

# Créer le dossier Obsidian s'il n'existe pas
if [ ! -d "$OBSIDIAN_VAULT" ]; then
    echo "   ⚠️  Vault Obsidian non trouvé: $OBSIDIAN_VAULT"
    echo "   Création du dossier..."
    mkdir -p "$OBSIDIAN_VAULT"
fi

# Copier le fichier avec date
OBSIDIAN_FILE="$OBSIDIAN_VAULT/${FILENAME}.md"
cp "$DOC_SOURCE" "$OBSIDIAN_FILE"

if [ -f "$OBSIDIAN_FILE" ]; then
    echo -e "   ${GREEN}✅ Copié: $OBSIDIAN_FILE${NC}"
    
    # Ouvrir dans Obsidian (Mac uniquement)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Encoder le nom de fichier pour l'URL
        ENCODED_FILE=$(echo "$FILENAME" | sed 's/ /%20/g')
        VAULT_NAME=$(basename "$OBSIDIAN_VAULT")
        
        # Ouvrir Obsidian avec le fichier
        open "obsidian://open?vault=$VAULT_NAME&file=$ENCODED_FILE" 2>/dev/null
        echo "   📖 Ouvert dans Obsidian"
    fi
else
    echo "   ❌ Échec de copie"
fi

echo ""

# ============================================
# 2. NOTION (via presse-papiers)
# ============================================
echo -e "${BLUE}📋 NOTION${NC}"

if [ "$NOTION_CLIPBOARD" = true ]; then
    # Copier le contenu dans le presse-papiers
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        cat "$DOC_SOURCE" | pbcopy
        echo -e "   ${GREEN}✅ Contenu copié dans le presse-papiers${NC}"
        echo "   📝 Pour coller dans Notion:"
        echo "      1. Ouvrez Notion"
        echo "      2. Créez une nouvelle page"
        echo "      3. Cmd+V pour coller"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux avec xclip
        if command -v xclip &> /dev/null; then
            cat "$DOC_SOURCE" | xclip -selection clipboard
            echo -e "   ${GREEN}✅ Contenu copié dans le presse-papiers${NC}"
        else
            echo "   ⚠️  xclip non installé (sudo apt install xclip)"
        fi
    fi
fi

echo ""

# ============================================
# 3. RÉSUMÉ
# ============================================
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✨ Sauvegarde terminée!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Fichiers:"
echo "  • Original: $DOC_SOURCE"
echo "  • Obsidian: $OBSIDIAN_FILE"
echo "  • Notion:   📋 (presse-papiers)"
echo ""
echo "Taille: $(wc -c < "$DOC_SOURCE" | tr -d ' ') octets"
echo "Lignes: $(wc -l < "$DOC_SOURCE" | tr -d ' ')"
