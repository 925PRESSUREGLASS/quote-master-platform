#!/bin/bash

# Quote Master Pro - Test Runner Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
PARALLEL=false
MARKERS=""

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Run tests for Quote Master Pro"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE       Test type: unit, integration, e2e, all (default: all)"
    echo "  -m, --markers MARKERS Run tests with specific markers"
    echo "  -c, --no-coverage     Disable coverage reporting"
    echo "  -v, --verbose         Enable verbose output"
    echo "  -p, --parallel        Run tests in parallel"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 -t unit            # Run only unit tests"
    echo "  $0 -m 'not slow'      # Run tests except slow ones"
    echo "  $0 -t integration -v  # Run integration tests with verbose output"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            show_usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}🧪 Quote Master Pro Test Runner${NC}"
echo -e "${YELLOW}Test Type: $TEST_TYPE${NC}"

# Prepare pytest arguments
PYTEST_ARGS=""

# Add coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml"
fi

# Add verbose option
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

# Add parallel option
if [ "$PARALLEL" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m '$MARKERS'"
fi

# Set test paths based on type
case $TEST_TYPE in
    unit)
        TEST_PATH="tests/unit"
        ;;
    integration)
        TEST_PATH="tests/integration"
        ;;
    e2e)
        TEST_PATH="tests/e2e"
        ;;
    all)
        TEST_PATH="tests"
        ;;
    *)
        echo -e "${RED}❌ Invalid test type: $TEST_TYPE${NC}"
        echo "Valid types: unit, integration, e2e, all"
        exit 1
        ;;
esac

# Check if Docker containers are running for integration/e2e tests
if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "e2e" ] || [ "$TEST_TYPE" = "all" ]; then
    echo -e "${YELLOW}🔧 Checking test dependencies...${NC}"
    
    if ! docker ps | grep -q "quote-master-db\|postgres"; then
        echo -e "${YELLOW}⚠️  Starting test database...${NC}"
        docker-compose up -d db redis
        echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
        sleep 10
    fi
    
    # Run database migrations for tests
    echo -e "${YELLOW}🗄️  Setting up test database...${NC}"
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/quote_master_test"
    alembic upgrade head
fi

# Run the tests
echo -e "${GREEN}🚀 Running $TEST_TYPE tests...${NC}"
echo "Command: pytest $TEST_PATH $PYTEST_ARGS"

if pytest $TEST_PATH $PYTEST_ARGS; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    # Show coverage report if enabled
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}📊 Coverage Report:${NC}"
        echo "HTML report available at: htmlcov/index.html"
        echo "XML report available at: coverage.xml"
    fi
    
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi