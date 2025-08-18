#!/bin/bash

# Kyra Admin Management Script Wrapper
# This script makes it easy to manage admin users

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Kyra Admin Management Script${NC}"
echo -e "${BLUE}================================${NC}"

# Check if we're in the right directory
if [ ! -f "$BACKEND_DIR/app/db/models.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the backend directory${NC}"
    echo -e "   Current directory: $(pwd)"
    echo -e "   Expected: $BACKEND_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    cd "$BACKEND_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r ../requirements.txt
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source "$BACKEND_DIR/.venv/bin/activate"

# Set Python path
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# Check if make_admin.py exists
if [ ! -f "$SCRIPT_DIR/make_admin.py" ]; then
    echo -e "${RED}❌ make_admin.py script not found!${NC}"
    exit 1
fi

# Make script executable
chmod +x "$SCRIPT_DIR/make_admin.py"

# Run the Python script with all arguments
echo -e "${GREEN}✅ Running admin management script...${NC}"
echo ""

cd "$BACKEND_DIR"
python "$SCRIPT_DIR/make_admin.py" "$@"
