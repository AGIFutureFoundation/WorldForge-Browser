// gen-settings.js -- write /app/dist/settings.json from environment (runs at container boot).
const fs = require('fs');
const settings = {
  MVSF: {
    IO: { bGlobalNotify: true },
    nPort: process.env.PORT || '8080',
    key: process.env.MVSADMINKEY,
    sCompanyId: process.env.COMPANY_ID || '137',
    LAN: {
      port: process.env.PORT || '8080',          // @metaversalcorp/mvsf listens on Settings.LAN.port
      SSL: { bUseSSL: false },                   // plain HTTP: Fly terminates TLS at the edge
    },
  },
  SQL: {
    type: 'MYSQL',
    config: {
      connectionLimit: 10,
      host: process.env.MYSQLHOST || '127.0.0.1',
      port: process.env.MYSQLPORT || '3306',
      user: process.env.MYSQLUSER || 'msf',
      password: process.env.MYSQLPASSWORD,
      database: process.env.MYSQLDATABASE || 'msf_map',
      multipleStatements: true,
    },
  },
};
if (!settings.MVSF.key || !settings.SQL.config.password) {
  console.error('gen-settings: MVSADMINKEY and MYSQLPASSWORD must be set');
  process.exit(1);
}
fs.writeFileSync('/app/dist/settings.json', JSON.stringify(settings, null, 2));
console.log('settings.json written (company ' + settings.MVSF.sCompanyId + ')');
