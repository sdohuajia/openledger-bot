const fs = require('fs');
const WebSocket = require('ws');
const axios = require('axios');
const readline = require('readline');
const { HttpsProxyAgent } = require('https-proxy-agent');

// 显示头部信息
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

// 从文件读取账号信息
const tokens = fs.readFileSync('account.txt', 'utf8').trim().split('\n').map(line => {
  const [token, workerID, id, ownerAddress] = line.split(':');
  return { token, workerID, id, ownerAddress };
});

// 从文件读取代理信息
let proxies = [];
try {
  proxies = fs.readFileSync('proxy.txt', 'utf8').trim().split(/\s+/);
} catch (error) {
  console.error('读取 proxy.txt 文件时出错:', error.message);
}

// 检查代理数量是否足够
if (proxies.length < tokens.length) {
  console.error('代理数量少于账号数量，请提供足够的代理。');
  process.exit(1);
}

const accountIDs = {};

// 从文件读取 GPU 列表
const gpuList = JSON.parse(fs.readFileSync('src/gpu.json', 'utf8'));

// 尝试从文件读取现有数据分配，如果没有则初始化新的分配
let dataAssignments = {};
try {
  dataAssignments = JSON.parse(fs.readFileSync('data.json', 'utf8'));
} catch (error) {
  console.log('没有找到现有的数据分配，初始化新的分配。');
}

// 获取或分配资源
function getOrAssignResources(workerID) {
  if (!dataAssignments[workerID]) {
    const randomGPU = gpuList[Math.floor(Math.random() * gpuList.length)];
    const randomStorage = (Math.random() * 500).toFixed(2);
    dataAssignments[workerID] = {
      gpu: randomGPU,
      storage: randomStorage
    };
    fs.writeFileSync('data.json', JSON.stringify(dataAssignments, null, 2));
  }
  return dataAssignments[workerID];
}

// 提示是否使用代理
async function askUseProxy() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    function ask() {
      rl.question('你想使用代理吗？ (y/n): ', (answer) => {
        if (answer.toLowerCase() === 'y') {
          resolve(true);
          rl.close();
        } else if (answer.toLowerCase() === 'n') {
          resolve(false);
          rl.close();
        } else {
          console.log('请输入 y 或 n。');
          ask();
        }
      });
    }
    ask();
  });
}

// 获取账号ID
async function getAccountID(token, index, useProxy) {
  try {
    const proxyUrl = proxies[index];
    const agent = useProxy ? new HttpsProxyAgent(proxyUrl) : undefined;
    const proxyText = useProxy ? proxyUrl : '无';

    const response = await axios.get('https://apitn.openledger.xyz/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      httpsAgent: agent
    });
    const accountID = response.data.data.id;
    accountIDs[token] = accountID;
    console.log(`\x1b[31m[${index + 1}] 账号ID ${accountID}, 总心跳数 -, 总积分 -, 代理: ${proxyText}\x1b[0m`);
  } catch (error) {
    console.error(`获取 token 索引 ${index} 的账号ID时出错:`, error.message);
  }
}

// 获取账号详情
async function getAccountDetails(token, index, useProxy) {
  try {
    const proxyUrl = proxies[index];
    const agent = useProxy ? new HttpsProxyAgent(proxyUrl) : undefined;
    const proxyText = useProxy ? proxyUrl : '无';

    const rewardRealtimeResponse = await axios.get('https://rewardstn.openledger.xyz/api/v1/reward_realtime', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      httpsAgent: agent
    });
    const rewardHistoryResponse = await axios.get('https://rewardstn.openledger.xyz/api/v1/reward_history', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      httpsAgent: agent
    });

    const totalHeartbeats = parseInt(rewardRealtimeResponse.data.data[0].total_heartbeats, 10);
    const totalPoints = parseInt(rewardHistoryResponse.data.data[0].total_points, 10);
    const total = totalHeartbeats + totalPoints;

    console.log(`\x1b[31m[${index + 1}] 账号ID ${accountIDs[token]}, 总心跳数 ${totalHeartbeats}, 总积分 ${total}, 代理: ${proxyText}\x1b[0m`);
  } catch (error) {
    console.error(`获取 token 索引 ${index} 的账号详情时出错:`, error.message);
  }
}

// 处理请求
async function processRequests(useProxy) {
  const promises = tokens.map(({ token, workerID, id, ownerAddress }, index) => {
    return (async () => {
      await getAccountID(token, index, useProxy);
      if (accountIDs[token]) {
        await getAccountDetails(token, index, useProxy);
        connectWebSocket({ token, workerID, id, ownerAddress }, index, useProxy);
      }
    })();
  });

  await Promise.all(promises);
}

// 连接 WebSocket
function connectWebSocket({ token, workerID, id, ownerAddress }, index, useProxy) {
  const wsUrl = `wss://apitn.openledger.xyz/ws/v1/orch?authToken=${token}`;
  let ws = new WebSocket(wsUrl);
  const proxyText = useProxy ? proxies[index] : '无';
  let heartbeatInterval;

  function sendHeartbeat() {
    const { gpu: assignedGPU, storage: assignedStorage } = getOrAssignResources(workerID);
    const heartbeatMessage = {
      message: {
        Worker: {
          Identity: workerID,
          ownerAddress,
          type: 'LWEXT',
          Host: 'chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc'
        },
        Capacity: {
          AvailableMemory: (Math.random() * 32).toFixed(2),
          AvailableStorage: assignedStorage,
          AvailableGPU: assignedGPU,
          AvailableModels: []
        }
      },
      msgType: 'HEARTBEAT',
      workerType: 'LWEXT',
      workerID
    };
    console.log(`\x1b[36m[${index + 1}] 发送心跳信息，workerID: ${workerID}, 账号ID ${accountIDs[token]}, 代理: ${proxyText}\x1b[0m`);
    ws.send(JSON.stringify(heartbeatMessage));
  }

  ws.on('open', function open() {
    console.log(`\x1b[36m[${index + 1}] 已连接到 WebSocket，workerID: ${workerID}, 账号ID ${accountIDs[token]}, 代理: ${proxyText}\x1b[0m`);

    const registerMessage = {
      workerID,
      msgType: 'REGISTER',
      workerType: 'LWEXT',
      message: {
        id,
        type: 'REGISTER',
        worker: {
          host: 'chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc',
          identity: workerID,
          ownerAddress,
          type: 'LWEXT'
        }
      }
    };
    ws.send(JSON.stringify(registerMessage));

    heartbeatInterval = setInterval(sendHeartbeat, 30000);
  });

  ws.on('message', function incoming(data) {
    console.log(`\x1b[36m[${index + 1}] 收到消息，workerID: ${workerID}: ${data}, 账号ID ${accountIDs[token]}, 代理: ${proxyText}\x1b[0m`);
  });

  ws.on('error', function error(err) {
    console.error(`\x1b[33m[${index + 1}] WebSocket 错误，workerID: ${workerID}:`, err);
  });

  ws.on('close', function close() {
    console.log(`\x1b[33m[${index + 1}] WebSocket 连接关闭，workerID: ${workerID}, 账号ID ${accountIDs[token]}, 代理: ${proxyText}\x1b[0m`);
    clearInterval(heartbeatInterval);
    setTimeout(() => {
      console.log(`\x1b[33m[${index + 1}] 正在重新连接 WebSocket，workerID: ${workerID}, 账号ID ${accountIDs[token]}, 代理: ${proxyText}\x1b[0m`);
      connectWebSocket({ token, workerID, id, ownerAddress }, index, useProxy);
    }, 30000);
  });
}

// 定期更新账号详情
async function updateAccountDetailsPeriodically(useProxy) {
  setInterval(async () => {
    const promises = tokens.map(({ token }, index) => getAccountDetails(token, index, useProxy));
    await Promise.all(promises);
  }, 5 * 60 * 1000);
}

// 主程序入口
(async () => {
  displayHeader();
  const useProxy = await askUseProxy();
  await processRequests(useProxy);
  updateAccountDetailsPeriodically(useProxy);
})();
