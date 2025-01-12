const fs = require('fs');
const WebSocket = require('ws');
const axios = require('axios');
const readline = require('readline');
const { HttpsProxyAgent } = require('https-proxy-agent');
const { v4: uuidv4 } = require('uuid');

let dataStore = {};
try {
  dataStore = JSON.parse(fs.readFileSync('data.json', 'utf8'));
} catch (err) {
  console.log('未找到现有数据存储，正在创建新的 data.json 文件。');
}

const gpuList = JSON.parse(fs.readFileSync('src/gpu.json', 'utf8'));

function getOrAssignResources(address) {
  if (!dataStore[address].gpu || !dataStore[address].storage) {
    const randomGPU = gpuList[Math.floor(Math.random() * gpuList.length)];
    const randomStorage = (Math.random() * 500).toFixed(2);

    dataStore[address].gpu = randomGPU;
    dataStore[address].storage = randomStorage;

    try {
      fs.writeFileSync('data.json', JSON.stringify(dataStore, null, 2));
    } catch (error) {
      console.error('写入 GPU/存储到 data.json 时出错:', error.message);
    }
  }
}

function displayHeader() {
  const width = process.stdout.columns;
  const headerLines = [
    "<|============================================|>",
    " OpenLedger Bot 自动化节点交互",
    "<|============================================|>"
  ];
  headerLines.forEach(line => {
    console.log(`\x1b[36m${line.padStart((width + line.length) / 2)}\x1b[0m`);
  });
}

let wallets = [];
try {
  wallets = fs.readFileSync('account.txt', 'utf8')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
} catch (err) {
  console.error('读取 account.txt 时出错:', err.message);
  process.exit(1);
}

let proxies = [];
try {
  proxies = fs.readFileSync('proxy.txt', 'utf8')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
} catch (error) {
  console.error('读取 proxy.txt 时出错:', error.message);
}

if (proxies.length > 0 && proxies.length < wallets.length) {
  console.error('代理数量少于钱包数量，请提供足够的代理。');
  process.exit(1);
}

const accountIDs = {};

async function askUseProxy() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    function ask() {
      rl.question('您是否想使用代理？ (y/n): ', (answer) => {
        if (answer.toLowerCase() === 'y') {
          resolve(true);
          rl.close();
        } else if (answer.toLowerCase() === 'n') {
          resolve(false);
          rl.close();
        } else {
          console.log('请回答 y 或 n。');
          ask();
        }
      });
    }
    ask();
  });
}

async function generateTokenForAddress(address, agent) {
  try {
    const result = await axios.post(
      'https://apitn.openledger.xyz/api/v1/auth/generate_token',
      { address },
      {
        headers: { 'Content-Type': 'application/json' },
        httpsAgent: agent
      }
    );
    return result.data?.data?.token || null;
  } catch (error) {
    console.error(`生成钱包 ${address} 的 token 时出错:`, error.message);
    return null;
  }
}

async function getOrCreateWalletData(address, agent) {
  if (!dataStore[address]) {
    dataStore[address] = {
      address,
      workerID: Buffer.from(address).toString('base64'),
      id: uuidv4(),
      token: null,
      gpu: null,
      storage: null
    };
  }

  if (!dataStore[address].token) {
    const token = await generateTokenForAddress(address, agent);
    if (!token) {
      console.log('无法生成 token，将跳过此钱包。');
      return null;
    }
    dataStore[address].token = token;
    try {
      fs.writeFileSync('data.json', JSON.stringify(dataStore, null, 2));
    } catch (error) {
      console.error('写入 data.json 时出错:', error.message);
    }
  }

  return dataStore[address];
}

async function getAccountID(token, address, index, useProxy, delay = 60000) {
  const proxyUrl = proxies.length > 0 ? proxies[index % proxies.length] : '';
  const agent = useProxy && proxyUrl ? new HttpsProxyAgent(proxyUrl) : undefined;
  const proxyText = useProxy && proxyUrl ? proxyUrl : '无代理';

  let attempt = 1;
  while (true) {
    try {
      const response = await axios.get('https://apitn.openledger.xyz/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` },
        httpsAgent: agent
      });
      const acctID = response.data.data.id;
      accountIDs[address] = acctID;
      console.log(`\x1b[31m[${index + 1}]\x1b[0m 账号ID \x1b[31m${acctID}\x1b[0m, 总心跳数 0, 总积分 0, 代理: \x1b[31m${proxyText}\x1b[0m`);
      return;
    } catch (error) {
      console.error(`\x1b[31m[${index + 1}]\x1b[0m 获取钱包 ${address} 的账号ID时出错，第${attempt}次重试:`, error.message);
      console.log(`\x1b[31m[${index + 1}]\x1b[0m 正在重试... ${delay / 1000}秒后继续`);
      await new Promise(resolve => setTimeout(resolve, delay));
      attempt++;
    }
  }
}

async function checkAndClaimReward(token, address, index, useProxy, retries = 3, delay = 60000) {
  const proxyUrl = proxies.length > 0 ? proxies[index % proxies.length] : '';
  const agent = useProxy && proxyUrl ? new HttpsProxyAgent(proxyUrl) : undefined;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const claimDetailsResponse = await axios.get('https://rewardstn.openledger.xyz/api/v1/claim_details', {
        headers: { 'Authorization': `Bearer ${token}` },
        httpsAgent: agent
      });

      const claimed = claimDetailsResponse.data.data?.claimed;
      if (!claimed) {
        const claimRewardResponse = await axios.get('https://rewardstn.openledger.xyz/api/v1/claim_reward', {
          headers: { 'Authorization': `Bearer ${token}` },
          httpsAgent: agent
        });

        if (claimRewardResponse.data.status === 'SUCCESS') {
          console.log(
            `\x1b[31m[${index + 1}]\x1b[0m 钱包 \x1b[31m${address}\x1b[0m, ` +
            `账号ID \x1b[31m${accountIDs[address]}\x1b[0m \x1b[32m成功领取每日奖励！\x1b[0m`
          );
        }
      }
      return;
    } catch (error) {
      console.error(`领取钱包 ${address} 奖励时出错，第${attempt}次重试:`, error.message);
      if (attempt < retries) {
        console.log(`重试中... ${delay / 1000}秒后继续`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        console.error('所有重试都失败了。');
      }
    }
  }
}

async function checkAndClaimRewardsPeriodically(useProxy) {
  const promises = wallets.map(async (address, index) => {
    const { token } = dataStore[address] || {};
    if (!token) return;
    await checkAndClaimReward(token, address, index, useProxy);
  });
  await Promise.all(promises);

  setInterval(async () => {
    const promises = wallets.map(async (address, idx) => {
      const { token } = dataStore[address] || {};
      if (!token) return;
      await checkAndClaimReward(token, address, idx, useProxy);
    });
    await Promise.all(promises);
  }, 12 * 60 * 60 * 1000);
}

function connectWebSocket({ token, workerID, id, address }, index, useProxy) {
  const proxyUrl = proxies.length > 0 ? proxies[index % proxies.length] : '';
  const agent = useProxy && proxyUrl ? new HttpsProxyAgent(proxyUrl) : undefined;
  const wsUrl = `wss://apitn.openledger.xyz/ws/v1/orch?authToken=${token}`;
  const wsOptions = {
    agent,
    headers: {
      'Accept-Encoding': 'gzip, deflate, br, identity',
      'Authorization': `Bearer ${token}`,
      'Connection': 'keep-alive',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      'Content-Type': 'application/json',
      'x-worker-id': workerID
    }
  };

  const ws = new WebSocket(wsUrl, wsOptions);

  ws.on('open', () => {
    console.log(`\x1b[31m[${index + 1}]\x1b[0m WebSocket 已连接，钱包 \x1b[31m${address}\x1b[0m`);
  });

  ws.on('message', (message) => {
    const data = JSON.parse(message);
    if (data.action === 'REGISTER') {
      console.log(`注册成功: ${data.message}`);
    }
    console.log(`收到消息: \x1b[31m${JSON.stringify(data)}\x1b[0m`);
  });

  ws.on('error', (error) => {
    console.error(`WebSocket 错误: ${error.message}`);
  });

  ws.on('close', () => {
    console.log(`WebSocket 连接关闭: 钱包 \x1b[31m${address}\x1b[0m`);
  });
}

(async function main() {
  displayHeader();

  const useProxy = await askUseProxy();

  const promises = wallets.map(async (address, index) => {
    getOrAssignResources(address);
    const walletData = await getOrCreateWalletData(address, useProxy);
    if (!walletData) return;

    await getAccountID(walletData.token, address, index, useProxy);
    connectWebSocket(walletData, index, useProxy);
  });

  await Promise.all(promises);

  await checkAndClaimRewardsPeriodically(useProxy);
})();
