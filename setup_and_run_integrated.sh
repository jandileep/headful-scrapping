#!/bin/bash
# Setup and run script for the integrated crawler

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up environment for Integrated Web Crawler...${NC}"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo -e "${GREEN}Python 3 is installed.${NC}"
else
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install requirements.${NC}"
    exit 1
fi
echo -e "${GREEN}Requirements installed.${NC}"

# Check if URL is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <url> [options]${NC}"
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  --max-depth=N    Maximum depth for recursive crawling (default: 2)"
    echo -e "  --delay=N        Delay between requests in seconds (default: 3)"
    echo -e "  --no-headless    Run Chrome in non-headless mode"
    echo -e "  --no-robots      Ignore robots.txt"
    echo -e "\n${YELLOW}Example:${NC}"
    echo -e "  $0 https://example.com --max-depth=3 --delay=5"
    exit 0
fi

# Parse arguments
URL=$1
shift
MAX_DEPTH=2
DELAY=3
HEADLESS="--headless"
ROBOTS=""

# Parse options
for arg in "$@"; do
    case $arg in
        --max-depth=*)
            MAX_DEPTH="${arg#*=}"
            ;;
        --delay=*)
            DELAY="${arg#*=}"
            ;;
        --no-headless)
            HEADLESS=""
            ;;
        --no-robots)
            ROBOTS="--no-robots"
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            exit 1
            ;;
    esac
done

# Run the crawler
echo -e "${YELLOW}Running integrated crawler on $URL...${NC}"
echo -e "${YELLOW}Max depth: $MAX_DEPTH, Delay: $DELAY seconds${NC}"
if [ -z "$HEADLESS" ]; then
    echo -e "${YELLOW}Running in non-headless mode${NC}"
fi
if [ -n "$ROBOTS" ]; then
    echo -e "${YELLOW}Ignoring robots.txt${NC}"
fi

python3 integrated_crawler.py "$URL" $HEADLESS --max-depth=$MAX_DEPTH --delay=$DELAY $ROBOTS

# Check if crawler ran successfully
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Crawler completed successfully.${NC}"
else
    echo -e "${RED}Crawler encountered an error.${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate
echo -e "${GREEN}Done.${NC}"