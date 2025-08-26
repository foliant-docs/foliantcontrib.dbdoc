#!/bin/bash

container=${1:-testdb-mysql}
network=${2:-testnetwork}

docker run -d --name ${container} \
    --network ${network} \
    -e MYSQL_ROOT_PASSWORD=password \
    -e MYSQL_DATABASE=testdb \
    -v $(pwd)/tests/db/mysql/data:/docker-entrypoint-initdb.d \
    -p 3306:3306 \
    mysql:8

rm -rf init-scripts
