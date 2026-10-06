#!/usr/bin/env bash
set -e

PLUGIN_ID="org.kde.plasma.antigravity"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [[ "$1" == "--uninstall" || "$1" == "-u" ]]; then
    echo -e "${YELLOW}==> Uninstalling $PLUGIN_ID...${NC}"
    if command -v kpackagetool6 &>/dev/null; then
        kpackagetool6 --type Plasma/Applet --remove "$PLUGIN_ID" || true
    fi
    rm -rf "$HOME/.local/share/plasma/plasmoids/$PLUGIN_ID"
    echo -e "${GREEN}==> $PLUGIN_ID removed successfully.${NC}"
    exit 0
fi

echo -e "${BLUE}==> Installing / Upgrading $PLUGIN_ID (KDE Plasma 6)...${NC}"

# Check requirements
if ! command -v kpackagetool6 &>/dev/null; then
    echo -e "${YELLOW}[!] kpackagetool6 not found in PATH. Performing direct installation to ~/.local/share/plasma/plasmoids/...${NC}"
    TARGET_DIR="$HOME/.local/share/plasma/plasmoids/$PLUGIN_ID"
    mkdir -p "$TARGET_DIR"
    cp -r "$SRC_DIR/metadata.json" "$SRC_DIR/contents" "$TARGET_DIR/"
else
    # Try upgrade, fallback to install
    kpackagetool6 --type Plasma/Applet --upgrade "$SRC_DIR" 2>/dev/null || \
    kpackagetool6 --type Plasma/Applet --install "$SRC_DIR"
fi

# Ensure executable scripts have +x permission
chmod +x "$HOME/.local/share/plasma/plasmoids/$PLUGIN_ID/contents/scripts/status_provider.py" 2>/dev/null || true

echo -e "${GREEN}==> Successfully installed $PLUGIN_ID!${NC}"

if [[ "$1" == "--restart-plasma" || "$2" == "--restart-plasma" ]]; then
    echo -e "${BLUE}==> Restarting Plasma Shell...${NC}"
    systemctl --user restart plasma-plasmashell.service 2>/dev/null || kquitapp6 plasmashell && kstart5 plasmashell &
    echo -e "${GREEN}==> Plasma Shell restarted.${NC}"
else
    echo -e "\n${BLUE}Next steps:${NC}"
    echo "  • Test standalone window:  ./test.sh"
    echo "  • Right click Desktop → 'Add Widgets...' → search for 'Antigravity Status'"
    echo "  • Restart Plasma shell:    systemctl --user restart plasma-plasmashell.service"
fi
