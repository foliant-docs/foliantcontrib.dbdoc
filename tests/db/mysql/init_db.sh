#!/bin/bash

set -e

container=${1:-testdb}
network=${2:-testnetwork}

docker rm -f ${container}
docker run -d --name ${container} \
    --network ${network} \
    -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_USER=testuser \
    -e MYSQL_PASSWORD=testpassword \
    -e MYSQL_DATABASE=testdb \
    -v $(pwd)/tests/db/mysql/data:/docker-entrypoint-initdb.d \
    -p 3306:3306 \
    mysql:8
