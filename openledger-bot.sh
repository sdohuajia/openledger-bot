#!/bin/bash

# 脚本保存路径
SCRIPT_PATH="$HOME/openledger-bot.sh"

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
}

# 安装必要的软件包
function start_openledger_bot() {
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

    # 依赖安装完成后继续让用户填写信息
    echo "依赖安装完成，现在继续填写账户信息和代理 IP..."
    setup_account
    setup_proxy
}

# 让用户输入并保存到 account.txt
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
    echo "$account" >> account.txt
    echo "账户信息已保存到 account.txt"

# 让用户输入代理IP并保存到 proxy.txt
    echo "请输入代理 IP："
    read -r proxy
    echo "$proxy" >> proxy.txt
    echo "代理 IP 已保存到 proxy.txt"

    # 启动进程
    echo "正在启动 Openledger Bot 进程..."
    screen -dmS openledger bash -c 'cd openledger-bot && node index.js'
    echo "请使用 'screen -r openledger' 连接到进程。"
    echo "按任意键返回主菜单..."
    # 等待任意键输入后才返回主菜单
    read -n 1 -s -r
}

# 主菜单函数
function main_menu() {
    # 首次运行检查依赖
    install_nodejs_npm

    while true; do
        clear
        echo "================================================================"
        echo "脚本由大赌社区哈哈哈哈编写，推特 @ferdie_jhovie，免费开源，请勿相信收费"
        echo "如有问题，可联系推特，仅此只有一个号"
        echo "新建了一个电报群，方便大家交流：t.me/Sdohua"
        echo "================================================================"
        echo "退出脚本，请按键盘 ctrl + C 退出即可"
        echo "请选择要执行的操作:"
        echo "1. 启动 openledger"
        echo "2. 退出脚本"
        echo "================================================================"
        
        read -p "请输入选项 [1-2]: " choice

        case $choice in
            1)
                start_openledger_bot
                ;;

            2)
                echo "退出脚本。"
                exit 0
                ;;
            *)
                echo "无效的选项，请重新选择"
                sleep 2
                ;;
        esac
    done
}

# 运行主菜单
main_menu
