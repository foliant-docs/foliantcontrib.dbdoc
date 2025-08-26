container=${1:-testdb}
network=${2:-testnetwork}

docker run -d --name ${container} \
    --network ${network} \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=testdb \
    -v $(pwd)/tests/db/psql/data:/docker-entrypoint-initdb.d \
    -p 5432:5432 \
    postgres:15

rm -rf init-scripts
