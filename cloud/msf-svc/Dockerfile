# worldforge-msf -- the RP1 MSF Map Service (MetaversalCorp/testServer, Apache-2.0) on Fly.io.
# Self-contained: Node 20 + embedded MariaDB in one machine. The Dev Center "Attach Fabric"
# wizard validates a LIVE map service (socket.io + REST); this is that service.
# Build context = repo root (dockerignore whitelists cloud/msf-svc/**).
FROM node:20-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends mariadb-server mariadb-client \
 && rm -rf /var/lib/apt/lists/*

# assemble the service "dist" the same way testServer's build:linux:mysql does
RUN mkdir -p /app/dist/Handlers /app/dist/web
COPY cloud/msf-svc/vendor/svc/handler.json cloud/msf-svc/vendor/svc/mapbase.js cloud/msf-svc/vendor/svc/utils.js /app/dist/
COPY cloud/msf-svc/vendor/svc/Handlers/ /app/dist/Handlers/
COPY cloud/msf-svc/vendor/svc/objects/ /app/dist/objects/
COPY cloud/msf-svc/vendor/site/ /app/dist/web/
COPY cloud/msf-svc/vendor/_Distrib/MSF_Map.sql /app/dist/
COPY cloud/msf-svc/vendor/svc/config/MySQL/server.js /app/dist/
COPY cloud/msf-svc/vendor/svc/config/MySQL/install.js /app/dist/
COPY cloud/msf-svc/vendor/svc/config/MySQL/package.json /app/dist/

WORKDIR /app/dist
RUN npm install --omit=dev --no-audit --no-fund

COPY cloud/msf-svc/gen-settings.js cloud/msf-svc/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh \
 && mkdir -p /var/run/mysqld && chown mysql:mysql /var/run/mysqld \
 && mkdir -p /var/lib/mysql && chown mysql:mysql /var/lib/mysql

ENV PORT=8080 \
    MYSQLHOST=127.0.0.1 \
    MYSQLPORT=3306 \
    MYSQLUSER=msf \
    MYSQLDATABASE=msf_map \
    COMPANY_ID=137
# secrets (flyctl secrets set): MVSADMINKEY, MYSQLPASSWORD
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
