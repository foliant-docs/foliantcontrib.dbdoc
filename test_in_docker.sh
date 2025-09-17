#!/bin/bash

set -e  # Exit on error

# Default values
PYTHON_VERSIONS=("3.8" "3.9")
DB_TYPE=("pgsql" "mysql")

CONTAINER_NAME="testdb"
NETWORK_NAME="testnetwork"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --python-version)
            PYTHON_VERSIONS=("$2")
            shift 2
            ;;
        --db-type)
            DB_TYPE=("$2")
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Test Configuration ==="
echo "Python versions: ${PYTHON_VERSIONS[*]}"
echo "Database type: ${DB_TYPE[*]}"
echo "=========================="

for version in "${PYTHON_VERSIONS[@]}"; do
    for type in "${DB_TYPE[@]}"; do
        echo "=== Testing with Python ${version} with DB ${type} ==="

        cat > Dockerfile << EOF
FROM python:${version}-bullseye

# Install required Python packages
RUN pip install foliantcontrib.utils requests psycopg2-binary pyodbc

WORKDIR /app
ENTRYPOINT ["./test.sh"]
EOF
        echo "Building test image..."
        docker build . -t test-foliant:${version} --no-cache

        if ! docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
            docker network create "${NETWORK_NAME}"
        fi

        ./tests/db/${type}/init_db.sh ${CONTAINER_NAME} ${NETWORK_NAME} || exit 1

        echo "Running tests with Docker access..."
        docker rm -f test-foliant:${version} 2>/dev/null || true
        docker run --rm \
            --network ${NETWORK_NAME} \
            -v "./:/app/" \
            -w /app \
            test-foliant:${version} \
            "${type}"

        echo "Cleaning up..."
        rm -f Dockerfile
        docker rm -f ${CONTAINER_NAME} 2>/dev/null || true
        docker rmi test-foliant:${version} 2>/dev/null || true
        docker network rm ${NETWORK_NAME} 2>/dev/null || true

        echo "=== Completed Python ${version} with ${type} tests ==="
        echo ""
    done
done