#!/bin/bash

# setup.sh for ManPage Explorer
# Usage:
#   ./setup.sh --install     Install manpage-explorer command and desktop entry (Linux/macOS)
#   ./setup.sh --uninstall   Remove installed files and launcher

TARGET_NAME="manpage-explorer"
SOURCE_PATH="$(pwd)/manpage-explorer.py"
TARGET_PATH="/usr/local/bin/$TARGET_NAME"
DESKTOP_ENTRY_PATH="$HOME/.local/share/applications/${TARGET_NAME}.desktop"

function install() {
    echo "Installing ManPage Explorer..."

    if [ ! -f "$SOURCE_PATH" ]; then
        echo "❌ Error: manpage-explorer.py not found in current directory."
        exit 1
    fi

    chmod +x "$SOURCE_PATH"

    PLATFORM="$(uname)"
    if [[ "$PLATFORM" == "Linux" ]]; then
        echo "Detected Linux."
        echo "Installing CLI launcher to $TARGET_PATH..."
        sudo ln -sf "$SOURCE_PATH" "$TARGET_PATH"

        echo "Installing desktop entry..."
        mkdir -p "$(dirname "$DESKTOP_ENTRY_PATH")"
        cat > "$DESKTOP_ENTRY_PATH" <<EOF
[Desktop Entry]
Name=ManPage Explorer
Exec=$TARGET_PATH
Icon=utilities-terminal
Type=Application
Categories=Utility;Documentation;
Terminal=false
EOF

        echo "✅ Installed on Linux. Run 'manpage-explorer' or find it in your application menu."

    elif [[ "$PLATFORM" == "Darwin" ]]; then
        echo "Detected macOS."
        echo "Installing CLI launcher to /usr/local/bin/$TARGET_NAME..."
        ln -sf "$SOURCE_PATH" "/usr/local/bin/$TARGET_NAME"
        echo "✅ You can now run it using 'manpage-explorer' in Terminal."
        echo "💡 If you'd like to launch it from the Dock, create a custom Automator app."

    else
        echo "⚠️ Unsupported platform. Please create a manual shortcut to:"
        echo "   $SOURCE_PATH"
    fi
}

function uninstall() {
    echo "Uninstalling ManPage Explorer..."

    echo "Removing CLI launcher from /usr/local/bin..."
    sudo rm -f "$TARGET_PATH"

    echo "Removing desktop entry..."
    rm -f "$DESKTOP_ENTRY_PATH"

    echo "✅ Uninstallation complete."
}

case "$1" in
    --install)
        install
        ;;
    --uninstall)
        uninstall
        ;;
    *)
        echo "Usage: $0 [ --install | --uninstall ]"
        exit 1
        ;;
esac