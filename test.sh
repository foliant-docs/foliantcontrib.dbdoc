#!/bin/bash

db_type=${1-psql}

# before testing make sure that you have installed the fresh version of preprocessor:
pip3 install .
# also make sure that fresh version of test framework is installed:
pip3 install --upgrade foliantcontrib.test_framework

# install dependencies
pip3 install sqlalchemy mysqlclient

python3 -m unittest discover -v -p "*${db_type}*"
