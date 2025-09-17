FROM python:3.8-bullseye

# Install required Python packages
RUN pip install foliantcontrib.utils requests psycopg2-binary pyodbc

WORKDIR /app
ENTRYPOINT ["./test.sh"]
