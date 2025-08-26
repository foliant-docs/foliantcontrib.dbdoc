#!/bin/bash

set -e  # Exit on error

# Default values
PYTHON_VERSIONS=("3.8" "3.9")
DB_TYPE=("psql")

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
    for db_type in "${DB_TYPE[@]}"; do
        echo "=== Testing with Python ${version} ==="

        # Write Dockerfile
        cat > Dockerfile << EOF
FROM python:${version}-bullseye

# Install required Python packages
RUN pip install foliantcontrib.utils requests psycopg2-binary pyodbc

# Create working directory
WORKDIR /app

EOF

        echo "Building test image..."
        docker build . -t test-foliant:${version} --no-cache

        container_name="testdb"
        network_name="testnetwork"

        docker network create ${network_name}

        ./tests/db/${db_type}/init_db.sh ${container_name} ${network_name} || exit 1

        echo "Running tests with Docker access..."
        docker run --rm \
            --network ${network_name}\
            -v "./:/app/" \
            -w /app \
            test-foliant:${version} \
            "./test.sh"

        echo "Cleaning up..."
        rm -f Dockerfile
        docker rm -f ${container_name} 2>/dev/null || true
        docker rmi test-foliant:${version}-${DB_TYPE} 2>/dev/null || true
        docker network rm ${network_name} 2>/dev/null || true

        echo "=== Completed Python ${version} with ${DB_TYPE} tests ==="
        echo ""
    done
done