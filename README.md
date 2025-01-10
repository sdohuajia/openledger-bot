# Openledger Bot
Openledger Bot is a simple tool designed to automate the node interaction.

## Features
- **Automated node interaction**
- **Proxy support**

## Prerequisites
- [Node.js](https://nodejs.org/) (version 14 or higher)

## Installation

1. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/recitativonika/openledger-bot.git
   ```
2. Navigate to the project directory:
   ```bash
   cd openledger-bot
   ```
4. Install the necessary dependencies:
   ```bash
   npm install
   ```

## Usage

1. Set the `account.txt` and `proxy.txt (if you want to use proxy)` before running the script. Below how to setup this fie.
2. Configuration:
   Modify the `account.txt` file with your account info
```
token1:workerID1:id1:ownerAddress1
token2:workerID2:id2:ownerAddress2
```
To get `Token`, `WorkerID`, `id` and `owneraddress` follow this steps:
- Register account first, you can [click here to register](https://testnet.openledger.xyz/?referral_code=ffqrnwqlzq)
- Download the [Extension](https://chromewebstore.google.com/detail/teneo-community-node/emcclcoaglgcpoognfiggmhnhgabppkm)
- Open Extension and right click and select `inspect`![no 1](https://github.com/user-attachments/assets/8abd970b-c1bc-44e1-b305-a9d76e7af063)

- Go to `network` tab![no 2](https://github.com/user-attachments/assets/4fa5e1ce-b49c-46c4-b70e-26307d465d62)

- Login to your account, and after login check the `network` tab again, search websocket connection `(orch?auth...)` and open![Screenshot 2025-01-10 022631](https://github.com/user-attachments/assets/a09ab2e5-7873-44c4-a3ce-26feb0ee1dd0)

- open `payload` tab and copy the `bearer/authtoken`![no 4](https://github.com/user-attachments/assets/1a14f452-ae2a-46e6-8d14-1a4d24ebd357)

- open `Messages` tab and copy the `WorkerID/identity`, `id` and `owneraddress` ![no 3](https://github.com/user-attachments/assets/ec6069e8-6a22-45cd-bdc5-ac9352b155f5)



3. Modify and set the `proxy.txt` file if you want to use proxy
```
ip:port
username:password@ip:port
http://ip:port
http://username:password@ip:port
```
4. Run the script:
```bash
node index.js
```
Do not delete `data.json`, it store your websocket data. 

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Note
This script only for testing purpose, using this script might violates ToS and may get your account permanently banned.

Extension link : [Extension](https://chromewebstore.google.com/detail/teneo-community-node/emcclcoaglgcpoognfiggmhnhgabppkm)
Dashboard Link : [Dashboard](https://testnet.openledger.xyz/?referral_code=ffqrnwqlzq)

My reff code if you want to use :) : https://testnet.openledger.xyz/?referral_code=ffqrnwqlzq
