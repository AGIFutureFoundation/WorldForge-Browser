#!/bin/sh
# entrypoint.sh -- boot the embedded MariaDB, install the MSF_Map schema once, then run the service.
set -e
: "${MVSADMINKEY:?MVSADMINKEY secret must be set}"
: "${MYSQLPASSWORD:?MYSQLPASSWORD secret must be set}"

if [ ! -d /var/lib/mysql/mysql ]; then
  echo "initializing mariadb datadir..."
  mariadb-install-db --user=mysql --datadir=/var/lib/mysql --skip-test-db >/dev/null 2>&1
fi
mkdir -p /var/run/mysqld && chown mysql:mysql /var/run/mysqld

mysqld --user=mysql --datadir=/var/lib/mysql --bind-address=127.0.0.1 --port=3306 &
# wait over the LOCAL SOCKET (debian mariadb root uses unix_socket auth; TCP is denied)
for i in $(seq 1 60); do
  mysqladmin ping >/dev/null 2>&1 && break
  sleep 1
done

# create the app database + user over the socket (as root), reachable via TCP for the service
mysql -e "CREATE DATABASE IF NOT EXISTS \`${MYSQLDATABASE:-msf_map}\`;
CREATE USER IF NOT EXISTS '${MYSQLUSER:-msf}'@'127.0.0.1' IDENTIFIED BY '${MYSQLPASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQLDATABASE:-msf_map}\`.* TO '${MYSQLUSER:-msf}'@'127.0.0.1';
FLUSH PRIVILEGES;"

node /app/gen-settings.js

cd /app/dist
node install.js
exec node server.js
