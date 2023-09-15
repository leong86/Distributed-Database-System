FROM mysql:8.0

ENV MYSQL_DATABASE=test
ENV MYSQL_ROOT_PASSWORD=root

COPY setup.sql /docker-entrypoint-initdb.d/
