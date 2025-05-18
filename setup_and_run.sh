#!/bin/bash
# Setup and run script for the Selenium Web Crawler
# This script helps users quickly set up and run the crawler

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print banner
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}   Selenium Web Crawler Setup    ${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""

# Check Python installation
echo -e "${YELLOW}Checking Python installation...${NC}"
if command_exists python3; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}Python 3 is installed.${NC}"
elif command_exists python; then
    PYTHON_CMD="python"
    echo -e "${GREEN}Python is installed.${NC}"
else
    echo -e "${RED}Error: Python is not installed. Please install Python 3.6 or higher.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Check if pip is installed
echo -e "${YELLOW}Checking pip installation...${NC}"
if command_exists pip3; then
    PIP_CMD="pip3"
    echo -e "${GREEN}pip3 is installed.${NC}"
elif command_exists pip; then
    PIP_CMD="pip"
    echo -e "${GREEN}pip is installed.${NC}"
else
    echo -e "${RED}Error: pip is not installed. Please install pip.${NC}"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
$PIP_CMD install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Check Chrome installation
echo -e "${YELLOW}Checking Chrome installation...${NC}"
if command_exists google-chrome || command_exists google-chrome-stable || command_exists chrome || command_exists "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; then
    echo -e "${GREEN}Chrome is installed.${NC}"
else
    echo -e "${RED}Warning: Chrome may not be installed or not found in PATH.${NC}"
    echo -e "${RED}Please make sure Chrome is installed before running the crawler.${NC}"
fi

# Check ChromeDriver installation
echo -e "${YELLOW}Note: ChromeDriver should be compatible with your Chrome version.${NC}"
echo -e "${YELLOW}If you encounter WebDriver errors, please download the appropriate ChromeDriver version.${NC}"
echo ""

# Ask user if they want to run a test crawl
echo -e "${YELLOW}Would you like to run a test crawl? (y/n)${NC}"
read -r run_test

if [[ $run_test == "y" || $run_test == "Y" ]]; then
    echo -e "${YELLOW}Enter a URL to test the crawler (e.g., https://example.com):${NC}"
    read -r test_url
    
    if [[ -z $test_url ]]; then
        test_url="https://example.com"
        echo -e "${YELLOW}Using default URL: $test_url${NC}"
    fi
    
    echo -e "${YELLOW}Running test crawl on $test_url...${NC}"
    $PYTHON_CMD test_crawler.py "$test_url"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Test crawl completed successfully!${NC}"
    else
        echo -e "${RED}Test crawl failed. Please check the error messages above.${NC}"
    fi
fi

# Ask user if they want to run a full crawl
echo -e "${YELLOW}Would you like to run a full crawl? (y/n)${NC}"
read -r run_full

if [[ $run_full == "y" || $run_full == "Y" ]]; then
    echo -e "${YELLOW}Enter the URL to crawl:${NC}"
    read -r crawl_url
    
    if [[ -z $crawl_url ]]; then
        echo -e "${RED}Error: URL is required for crawling.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Enter maximum crawl depth (default: 3):${NC}"
    read -r crawl_depth
    
    if [[ -z $crawl_depth ]]; then
        crawl_depth=3
    fi
    
    echo -e "${YELLOW}Enter maximum number of pages to crawl (default: 100):${NC}"
    read -r crawl_pages
    
    if [[ -z $crawl_pages ]]; then
        crawl_pages=100
    fi
    
    echo -e "${YELLOW}Enter output directory (default: crawled_data):${NC}"
    read -r crawl_output
    
    if [[ -z $crawl_output ]]; then
        crawl_output="crawled_data"
    fi
    
    echo -e "${YELLOW}Running full crawl on $crawl_url...${NC}"
    echo -e "${YELLOW}Depth: $crawl_depth, Max Pages: $crawl_pages, Output: $crawl_output${NC}"
    
    $PYTHON_CMD web_crawler.py "$crawl_url" --depth "$crawl_depth" --max-pages "$crawl_pages" --output "$crawl_output"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Crawl completed successfully!${NC}"
        
        # Ask if user wants to generate a summary report
        echo -e "${YELLOW}Would you like to generate a summary report? (y/n)${NC}"
        read -r gen_report
        
        if [[ $gen_report == "y" || $gen_report == "Y" ]]; then
            $PYTHON_CMD crawler_utils.py summary --output "$crawl_output"
        fi
    else
        echo -e "${RED}Crawl failed. Please check the error messages above.${NC}"
    fi
fi

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}   Setup and Run Complete        ${NC}"
echo -e "${GREEN}=================================${NC}"