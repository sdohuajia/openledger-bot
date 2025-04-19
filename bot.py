from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, base64, uuid, json, os, pytz
from web3 import Web3
from eth_account import Account
import hashlib
import urllib.parse

wib = pytz.timezone('Asia/Jakarta')

class OpenLedger:
    def __init__(self) -> None:
        self.extension_id = "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc"
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": self.extension_id,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Storage-Access": "active",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.account_proxies = {}
        self.default_proxy_scheme = "https"  # 默认代理协议

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
    {Fore.GREEN + Style.BRIGHT}自动Ping与奖励领取 {Fore.BLUE + Style.BRIGHT}Openledger - 机器人
        """
            f"""
    {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<这是测试>
        """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def load_accounts(self):
        filename = "accounts.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}文件 {filename} 未找到。{Style.RESET_ALL}")
                return []
            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            self.log(f"{Fore.RED}文件 {filename} 格式错误。{Style.RESET_ALL}")
            return []

    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.YELLOW + Style.BRIGHT}文件 {filename} 未找到，将不使用代理。{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.YELLOW + Style.BRIGHT}未找到代理，将不使用代理。{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}代理总数: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}加载代理失败: {e}，将不使用代理。{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxy):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxy.startswith(scheme) for scheme in schemes):
            return proxy
        return f"{self.default_proxy_scheme}://{proxy}"

    def get_next_proxy_for_account(self, account):
        if not self.proxies:
            return None
        accounts = self.load_accounts()
        for i, acc in enumerate(accounts):
            if acc["Address"] == account:
                if i >= len(self.proxies):
                    self.log(f"{Fore.RED + Style.BRIGHT}账号 {self.mask_account(account)} 没有对应的代理可用！{Style-RESET_ALL}")
                    return None
                proxy = self.check_proxy_schemes(self.proxies[i])
                self.account_proxies[account] = proxy
                return proxy
        return None

    def generate_register_message(self, address: str, worker_id: str, browser_id: str, msg_type: str):
        register_message = {
            "workerID": worker_id,
            "msgType": msg_type,
            "workerType": "LWEXT",
            "message": {
                "id": browser_id,
                "type": msg_type,
                "worker": {
                    "host": self.extension_id,
                    "identity": worker_id,
                    "ownerAddress": address,
                    "type": "LWEXT"
                }
            }
        }
        return register_message

    def generate_heartbeat_message(self, address: str, worker_id: str, msg_type: str, memory: int, storage: str):
        heartbeat_message = {
            "message": {
                "Worker": {
                    "Identity": worker_id,
                    "ownerAddress": address,
                    "type": "LWEXT",
                    "Host": self.extension_id,
                    "pending_jobs_count": 0
                },
                "Capacity": {
                    "AvailableMemory": memory,
                    "AvailableStorage": storage,
                    "AvailableGPU": "",
                    "AvailableModels": []
                }
            },
            "msgType": msg_type,
            "workerType": "LWEXT",
            "workerID": worker_id
        }
        return heartbeat_message

    def generate_browser_id(self):
        return str(uuid.uuid4())
        
    def generate_worker_id(self, account: str):
        return base64.b64encode(account.encode("utf-8")).decode("utf-8")

    def mask_account(self, account):
        return account[:6] + '*' * 6 + account[-6:]

    def print_message(self, account, proxy, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ 账户:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(account)} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} 代理: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{proxy if proxy else '无代理'}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}状态:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    async def get_private_key(self, address):
        accounts = self.load_accounts()
        for acc in accounts:
            if acc["Address"].lower() == address.lower():
                try:
                    private_key = acc["Private_Key"]
                    if len(private_key) == 64 and all(c in "0123456789abcdefABCDEF" for c in private_key):
                        formatted_key = "0x" + private_key
                        account = Account.from_key(formatted_key)
                        if account.address.lower() == address.lower():
                            self.print_message(address, '', Fore.GREEN, "找到有效私钥")
                            return formatted_key
                    self.log(f"{Fore.RED}账户 {self.mask_account(address)} 的私钥格式无效{Style.RESET_ALL}")
                    return None
                except Exception as e:
                    self.log(f"{Fore.RED}处理私钥时出错: {e}{Style.RESET_ALL}")
                    return None
        self.log(f"{Fore.RED}未找到账户 {self.mask_account(address)} 的私钥{Style.RESET_ALL}")
        return None

    async def checkin_details(self, address: str, token: str, use_proxy: bool, proxy=None):
        url = "https://rewardstn.openledger.xyz/ext/api/v2/claim_details"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        try:
            response = await asyncio.to_thread(
                requests.get, url=url, headers=headers, proxy=proxy if use_proxy else None,
                timeout=60, impersonate="safari15_5", verify=False
            )
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            self.print_message(address, proxy, Fore.RED, f"获取每日签到数据失败: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
            return None

    async def claim_checkin_reward(self, address: str, token: str, use_proxy: bool, proxy=None, checkin_data=None):
        if not checkin_data or checkin_data.get('claimed', True):
            self.print_message(address, proxy, Fore.YELLOW, "每日签到奖励已领取或数据缺失")
            return {'claimed': True}

        private_key = await self.get_private_key(address)
        if not private_key:
            self.print_message(address, proxy, Fore.RED, "未找到有效私钥")
            return None

        try:
            session = requests.Session()
            if use_proxy and proxy:
                session.proxies = {'http': proxy, 'https': proxy}

            w3 = Web3(Web3.HTTPProvider("https://rpctn.openledger.xyz/", session=session))
            chain_id = w3.eth.chain_id
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(address))
            gas_price = w3.eth.gas_price
            contract_address = "0x5d2cd1059b67ed3ae2d153149c8cedceb3344b9b"

            reward_point = int(checkin_data.get('dailyPoint', 10))
            server_signature = checkin_data.get('signature')
            salt = int(checkin_data.get('salt', 0))

            sig = server_signature[2:] if server_signature.startswith('0x') else server_signature
            v = int(sig[-2:], 16) + 27 if int(sig[-2:], 16) < 27 else int(sig[-2:], 16)
            r_hex = sig[:64]
            s_hex = sig[64:128]

            data = "0x8aca7c1a" + \
                   hex(reward_point)[2:].zfill(64) + \
                   hex(salt)[2:].zfill(64) + \
                   hex(v)[2:].zfill(64) + r_hex + s_hex

            tx_params = {
                'chainId': chain_id,
                'nonce': nonce,
                'gasPrice': gas_price,
                'gas': 300000,
                'to': Web3.to_checksum_address(contract_address),
                'value': 0,
                'data': data,
                'accessList': []
            }

            account = Account.from_key(private_key)
            signed_tx = account.sign_transaction(tx_params)
            signed_tx_hex = signed_tx.rawTransaction.hex()

            claim_url = "https://rewardstn.openledger.xyz/ext/api/v2/claim_reward"
            headers = {**self.headers, "Authorization": f"Bearer {token}"}
            payload = {"signedTx": signed_tx_hex}

            response = await asyncio.to_thread(
                requests.post, url=claim_url, headers=headers, json=payload,
                proxy=proxy if use_proxy else None, timeout=60, impersonate="safari15_5", verify=False
            )
            response_data = response.json()
            if response.status_code == 200 and response_data.get('status') == 'SUCCESS':
                self.print_message(address, proxy, Fore.GREEN, f"成功领取奖励: {reward_point} PTS")
                return {'claimed': True}
            else:
                self.print_message(address, proxy, Fore.RED, f"领取奖励失败: {response_data.get('message')}")
                return None
        except Exception as e:
            self.print_message(address, proxy, Fore.RED, f"领取每日签到奖励失败: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
            return None

    async def process_claim_checkin_reward(self, address: str, token: str, use_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            if use_proxy and not proxy:
                self.log(f"{Fore.RED + Style.BRIGHT}账号 {self.mask_account(address)} 无可用代理，跳过奖励领取。{Style.RESET_ALL}")
                return

            checkin = await self.checkin_details(address, token, use_proxy, proxy)
            if checkin:
                if not checkin['claimed']:
                    result = await self.claim_checkin_reward(address, token, use_proxy, proxy, checkin)
                    if result and result.get('claimed'):
                        self.print_message(address, proxy, Fore.GREEN,
                            f"每日签到奖励已领取 "
                            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT} 奖励: {Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT}{checkin['dailyPoint']} PTS{Style.RESET_ALL}"
                        )
                    else:
                        self.print_message(address, proxy, Fore.RED, "每日签到奖励未领取")
                else:
                    self.print_message(address, proxy, Fore.YELLOW, "每日签到奖励已领取")
            await asyncio.sleep(24 * 60 * 60)

    async def nodes_communicate(self, address: str, token: str, msg_type: str, payload: dict, use_proxy: bool, proxy=None):
        url = "https://apitn.openledger.xyz/ext/api/v2/nodes/communicate"
        data = json.dumps(payload)
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        while True:
            try:
                response = await asyncio.to_thread(
                    requests.post, url=url, headers=headers, data=data, proxy=proxy if use_proxy else None,
                    timeout=60, impersonate="safari15_5", verify=False
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.print_message(address, proxy, Fore.RED, f"{msg_type} 失败: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                await asyncio.sleep(5)

    async def process_accounts(self, address: str, token: str, use_proxy: bool):
        worker_id = self.generate_worker_id(address)
        browser_id = self.generate_browser_id()
        memory = round(random.uniform(0, 32), 2)
        storage = str(round(random.uniform(0, 500), 2))

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        if use_proxy and not proxy:
            self.log(f"{Fore.RED + Style.BRIGHT}账号 {self.mask_account(address)} 无可用代理，跳过处理。{Style.RESET_ALL}")
            return

        for msg_type in ["REGISTER", "HEARTBEAT"]:
            if msg_type == "REGISTER":
                payload = self.generate_register_message(address, worker_id, browser_id, msg_type)
                register = await self.nodes_communicate(address, token, msg_type, payload, use_proxy, proxy)
                if register:
                    self.print_message(address, proxy, Fore.GREEN, f"{msg_type} 成功: {Fore.BLUE + Style.BRIGHT}{register}")
                print(
                    f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}等待5分钟进行下一次Ping...{Style.RESET_ALL}",
                    end="\r"
                )
                await asyncio.sleep(5 * 60)
            elif msg_type == "HEARTBEAT":
                payload = self.generate_heartbeat_message(address, worker_id, msg_type, memory, storage)
                while True:
                    heartbeat = await self.nodes_communicate(address, token, msg_type, payload, use_proxy, proxy)
                    if heartbeat:
                        self.print_message(address, proxy, Fore.GREEN, f"{msg_type} 成功: {Fore.BLUE + Style.BRIGHT}{heartbeat}")
                    print(
                        f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}等待5分钟进行下一次Ping...{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(5 * 60)

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(f"{Fore.RED + Style.BRIGHT}未加载任何账户。{Style.RESET_ALL}")
                return
            
            await self.load_proxies()
            use_proxy = bool(self.proxies)  # 如果有代理则使用代理

            self.clear_terminal()
            self.welcome()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}账户总数: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
            )

            if use_proxy and len(self.proxies) < len(accounts):
                self.log(f"{Fore.YELLOW + Style.BRIGHT}警告：代理数量 ({len(self.proxies)}) 小于账户数量 ({len(accounts)})，多余账户将被忽略。{Style.RESET_ALL}")

            self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}" * 75)

            while True:
                tasks = []
                for account in accounts:
                    if account:
                        address = account["Address"]
                        token = account["Access_Token"]
                        if address and token:
                            tasks.append(asyncio.create_task(self.process_accounts(address, token, use_proxy)))
                            tasks.append(asyncio.create_task(self.process_claim_checkin_reward(address, token, use_proxy)))

                await asyncio.gather(*tasks)
                await asyncio.sleep(10)

        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}错误: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = OpenLedger()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ 退出 ] Openledger - 机器人{Style.RESET_ALL}                                       "
        )
