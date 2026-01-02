#!/bin/bash
# nextWeek.sh - Automated rollover and progression

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ADD_WEIGHT=false
WEIGHT_INCREMENT=2.5
PYTHON_ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--add-weight)
            ADD_WEIGHT=true
            shift
            ;;
        -i|--increment)
            WEIGHT_INCREMENT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -w, --add-weight         Add progressive weight to exercises"
            echo "  -i, --increment VALUE    Weight increment amount (default: 2.5)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --add-weight --increment 5.0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# If no flag provided, prompt user
if [ "$ADD_WEIGHT" = false ]; then
    echo -e "${BLUE}Do you want to add progressive weight to exercises? (Y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        ADD_WEIGHT=true
        echo -e "${GREEN}Weight progression enabled: +${WEIGHT_INCREMENT} lbs${NC}"
    else
        echo -e "${YELLOW}Continuing without weight progression${NC}"
    fi
fi

# Build Python arguments
if [ "$ADD_WEIGHT" = true ]; then
    PYTHON_ARGS="--add-weight --weight-increment ${WEIGHT_INCREMENT}"
fi

# Create progress directory if it doesn't exist
mkdir -p progress

# Backup the current week's workout if it exists
if [ -f "generated_week.json" ]; then
    BACKUP_FILE="progress/week_$(date +%Y%m%d).json"
    cp generated_week.json "$BACKUP_FILE"
    mv generated_week.json previous_week.json
    echo -e "${GREEN}✓ Progression history updated: $BACKUP_FILE${NC}"
fi

# Clean up old generated files
echo -e "${BLUE}Cleaning workspace...${NC}"
rm -f generated_week.md generated_week_*.pdf

# Generate the new week with optional weight progression
echo -e "${BLUE}Generating new workout week...${NC}"
python3 workout_generator.py $PYTHON_ARGS

echo -e "${GREEN}✓ New workout week generated successfully!${NC}"
echo ""
echo "Files created:"
echo "  - generated_week.json (workout data)"
echo "  - generated_week.md (readable format)"
echo ""
echo "To generate PDF: python3 workout_generator.py --pdf"