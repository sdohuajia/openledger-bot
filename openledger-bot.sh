#!/bin/bash

# 检查是否以 root 用户运行脚本
if [ "$(id -u)" != "0" ]; then
    echo "此脚本需要以 root 用户权限运行。"
    echo "请尝试使用 'sudo -i' 命令切换到 root 用户，然后再次运行此脚本。"
    exit 1
fi

# 安装 Node.js 和 npm
function install_nodejs_npm() {
    echo "正在检查 Node.js 和 npm 是否已安装..."

    # 检查是否安装了 Node.js
    if ! command -v node &> /dev/null; then
        echo "未找到 Node.js，正在安装..."
        apt update || { echo "更新包列表失败"; exit 1; }
        apt install -y nodejs || { echo "安装 Node.js 失败"; exit 1; }
    else
        echo "Node.js 已安装，版本为: $(node -v)"
    fi

    # 检查是否安装了 npm
    if ! command -v npm &> /dev/null; then
        echo "未找到 npm，正在安装..."
        apt install -y npm || { echo "安装 npm 失败"; exit 1; }
    else
        echo "npm 已安装，版本为: $(npm -v)"
    fi

    # 检查是否安装了 screen
    if ! command -v screen &> /dev/null; then
        echo "未找到 screen，正在安装..."
        apt install -y screen || { echo "安装 screen 失败"; exit 1; }
    else
        echo "screen 已安装"
    fi

    # 检查是否安装了 git
    if ! command -v git &> /dev/null; then
        echo "未找到 git，正在安装..."
        apt install -y git || { echo "安装 git 失败"; exit 1; }
    else
        echo "git 已安装"
    fi
}

# 设置账户信息
function setup_account() {
    echo "请输入 token1:"
    read -r token1
    echo "请输入 workerID1:"
    read -r workerID1
    echo "请输入 id1:"
    read -r id1
    echo "请输入 ownerAddress1:"
    read -r ownerAddress1

    # 合并这些信息
    account="$token1:$workerID1:$id1:$ownerAddress1"

    # 保存到 account.txt
    echo "$account" > account.txt
    echo "账户信息已保存到 account.txt"
}

# 设置代理信息
function setup_proxy() {
    echo "请输入代理 IP："
    read -r proxy
    echo "$proxy" > proxy.txt
    echo "代理 IP 已保存到 proxy.txt"
}

# 启动 bot
function start_bot() {
    # 检查openledger-bot目录是否已存在
    if [ -d "openledger-bot" ]; then
        echo "检测到已存在openledger-bot目录,正在删除..."
        rm -rf openledger-bot
    fi

    echo "正在更新系统包列表..."
    apt update || { echo "更新包列表失败"; exit 1; }
    
    echo "正在安装必要的 npm 包..."
    npm install -g node-fetch@2 global-agent https-proxy-agent socks-proxy-agent || { 
        echo "安装npm包失败"; 
        exit 1; 
    }

    echo "正在克隆 openledger 仓库..."
    git clone https://github.com/sdohuajia/openledger-bot.git || {
        echo "克隆仓库失败";
        exit 1;
    }

    echo "进入项目目录并安装依赖..."
    cd openledger-bot || { echo "进入目录失败"; exit 1; }
    npm install || { echo "安装项目依赖失败"; exit 1; }

    # 获取用户输入
    setup_account
    setup_proxy

    # 启动进程
    echo "正在启动 Openledger Bot 进程..."
    # 创建并直接进入 screen 会话
    screen -S openledger
    screen -dmS openledger bash -c 'cd openledger-bot && node index.js'
    echo "Bot 已在 screen 会话中启动"
    echo "使用 'screen -r openledger' 命令可以查看运行状态"
    echo "使用 'Ctrl + A + D' 可以退出 screen 会话"
    echo "使用 'screen -X -S openledger quit' 可以终止 bot 运行"
}

# 主菜单
function main_menu() {
    clear
    echo "================================================================"
    echo "                    Openledger Bot 安装脚本"
    echo "================================================================"
    echo "脚本由大赌社区编写，推特 @ferdie_jhovie"
    echo "电报群：t.me/Sdohua"
    echo "================================================================"
    echo "1. 安装并启动 bot"
    echo "2. 退出脚本"
    echo "================================================================"
    
    read -p "请输入选项 [1-2]: " choice

    case $choice in
        1)
            install_nodejs_npm
            start_bot
            ;;
        2)
            echo "退出脚本"
            exit 0
            ;;
        *)
            echo "无效的选项，请重新选择"
            sleep 2
            main_menu
            ;;
    esac
}

# 运行主菜单
main_menu
