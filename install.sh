#!/bin/bash
# Coach AI Installation Script

set -e

echo "Coach AI Installation"
echo "====================="
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ Found uv"

# Create venv and install
echo ""
echo "Installing dependencies..."
uv venv
uv pip install -e .

echo "✓ Dependencies installed"

# Test database
echo ""
echo "Testing database..."
uv run python test_tools.py

# Determine Claude Desktop config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CONFIG_DIR="$HOME/.config/Claude"
else
    echo "Error: Unsupported OS: $OSTYPE"
    exit 1
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

echo ""
echo "Configuring Claude Desktop..."

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Get absolute path to coach-ai
COACH_AI_PATH="$(cd "$(dirname "$0")" && pwd)"

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Warning: Claude Desktop config already exists at:"
    echo "   $CONFIG_FILE"
    echo ""
    echo "You'll need to manually add coach-ai to your existing config."
    echo "Add this to the 'mcpServers' section:"
    echo ""
    echo '{
  "mcpServers": {
    "coach-ai": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "'"$COACH_AI_PATH"'",
        "python",
        "-m",
        "coach_ai.server"
      ]
    }
  }
}'
    echo ""
else
    # Create new config file
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "coach-ai": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "$COACH_AI_PATH",
        "python",
        "-m",
        "coach_ai.server"
      ]
    }
  }
}
EOF
    echo "✓ Created Claude Desktop config"
    echo "   Location: $CONFIG_FILE"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop completely (Quit and reopen)"
echo "2. Look for the hammer icon in the chat input"
echo "3. Start chatting - try 'What should I focus on right now?'"
echo ""
echo "See QUICKSTART.md for usage examples"
echo ""
