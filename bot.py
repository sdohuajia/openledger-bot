from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, base64, uuid, json, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class OepnLedger:
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
        self.proxy_index = 0
        self.account_proxies = {}
        self.proxy_scheme = "https"  # 默认使用 https，可以改为 "socks5"

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
        {Fore.GREEN + Style.BRIGHT}自动Ping {Fore.BLUE + Style.BRIGHT}开放账本 - 机器人
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<这是水印>
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
                return

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}文件 {filename} 未找到。{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}未找到代理。{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}代理总数  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}加载代理失败: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxy):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        # 如果代理已有协议前缀，直接返回
        if any(proxy.startswith(scheme) for scheme in schemes):
            return proxy
        # 否则使用默认协议（https 或 socks5）
        return f"{self.proxy_scheme}://{proxy}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
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
        browser_id = str(uuid.uuid4())
        return browser_id
        
    def generate_worker_id(self, account: str):
        identity = base64.b64encode(account.encode("utf-8")).decode("utf-8")
        return identity
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account

    def print_message(self, account, proxy, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ 账户:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(account)} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} 代理: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{proxy}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}状态:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    def print_question(self):
        while True:
            try:
                print("1. 使用私人代理运行 (HTTPS)")
                print("2. 使用私人代理运行 (SOCKS5)")
                print("3. 不使用代理运行")
                choose = int(input("选择 [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    if choose == 2:
                        self.proxy_scheme = "socks5"  # 设置为 SOCKS5
                    else:
                        self.proxy_scheme = "https"  # 设置为 HTTPS
                    proxy_type = (
                        "使用私人代理运行 (HTTPS)" if choose == 1 else 
                        "使用私人代理运行 (SOCKS5)" if choose == 2 else 
                        "不使用代理运行"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} 已选择。{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}请输入1、2或3。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}无效输入。请输入一个数字（1、2或3）。{Style.RESET_ALL}")

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
                response = await asyncio.to_thread(requests.post, url=url, headers=headers, data=data, proxy=proxy, timeout=60, impersonate="safari15_5")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.print_message(address, proxy, Fore.RED, f"{msg_type} 失败: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
        
    async def process_accounts(self, address: str, token: str, use_proxy: bool):
        worker_id = self.generate_worker_id(address)
        browser_id = self.generate_browser_id()
        memory = round(random.uniform(0, 32), 2)
        storage = str(round(random.uniform(0, 500), 2))

        for msg_type in ["REGISTER", "HEARTBEAT"]:
            if msg_type == "REGISTER":
                proxy = self.get_next_proxy_for_account(address) if use_proxy else None
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
                    proxy = self.get_next_proxy_for_account(address) if use_proxy else None
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
                self.log(f"{Fore.RED+Style.BRIGHT}未加载任何账户。{Style.RESET_ALL}")
                return
            
            use_proxy_choice = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            self.clear_terminal()
            self.welcome()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}账户总数: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
            )

            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

            while True:
                tasks = []
                for account in accounts:
                    if account:
                        address = account["Address"]
                        token = account["Access_Token"]
                        if address and token:
                            tasks.append(asyncio.create_task(self.process_accounts(address, token, use_proxy)))

                await asyncio.gather(*tasks)
                await asyncio.sleep(10)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}错误: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = OepnLedger()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ 退出 ] 开放账本 - 机器人{Style.RESET_ALL}                                       "                              
        )