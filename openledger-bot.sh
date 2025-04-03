#!/bin/bash

# 脚本保存路径
SCRIPT_PATH="$HOME/openledger-bot.sh"

# 检查是否以 root 用户运行脚本
if [ "$(id -u)" != "0" ]; then
    echo "此脚本需要以 root 用户权限运行。"
    echo "请尝试使用 'sudo -i' 命令切换到 root 用户，然后再次运行此脚本。"
    exit 1
fi

# 安装和配置 openledger-bot 函数
function setup_openledger() {
    # 检查 openledger 目录是否存在，如果存在则删除
    if [ -d "openledger-bot" ]; then
        echo "检测到 openledger 目录已存在，正在删除..."
        rm -rf openledger-bot
        echo "openledger-bot 目录已删除。"
    fi

    echo "正在从 GitHub 克隆 openledger 仓库..."
    git clone https://github.com/sdohuajia/openledger-bot.git
    if [ ! -d "openledger-bot" ]; then
        echo "克隆失败，请检查网络连接或仓库地址。"
        exit 1
    fi

    cd "openledger-bot" || { echo "无法进入 openledger-bot 目录"; exit 1; }

    # 安装 Python3 和 pip（如果尚未安装）
    if ! command -v python3 &> /dev/null; then
        echo "正在安装 Python3 和 pip..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    fi

    # 安装 jq（如果尚未安装）
    if ! command -v jq &> /dev/null; then
        echo "正在安装 jq..."
        sudo apt-get install -y jq
    fi

    # 安装 requirements.txt 中的依赖项
    echo "正在安装 Python 依赖项..."
    pip install -r requirements.txt || { echo "依赖项安装失败"; exit 1; }

    # 创建或清空 accounts.json 文件
    echo "[]" > accounts.json
    
    # 提示用户输入账户数量
    read -p "请输入需要配置的账户数量: " account_count
    
    # 循环获取每个账户的信息
    for ((i=1; i<=account_count; i++)); do
        echo "正在配置第 $i 个账户:"
        read -p "请输入 Address: " address
        read -p "请输入 Access_Token: " access_token
        
        # 使用 jq 添加到 JSON 文件
        jq --arg addr "$address" --arg token "$access_token" \
           '. += [{"Address": $addr, "Access_Token": $token}]' accounts.json > tmp.json && mv tmp.json accounts.json
    done
    
    echo "账户信息已保存到 accounts.json"
    echo "当前 accounts.json 内容如下:"
    cat accounts.json

    # 配置代理信息
    read -p "请输入您的代理信息，格式为 http或者socks5://user:pass@ip:port (可以为空): " proxy_info
    proxy_file="/root/openledger-bot/proxy.txt"

    # 如果代理信息不为空，则写入文件
    if [[ -n "$proxy_info" ]]; then
        echo "$proxy_info" > "$proxy_file"
        echo "代理信息已添加到 $proxy_file."
    else
        echo "没有输入代理信息，文件保持不变."
    fi

    echo "正在使用 screen 启动 bot.py..."
    screen -S openledger -dm  # 创建新的 screen 会话，名称为 openledger
    sleep 1  # 等待1秒钟确保会话已启动

    # 进入目录并启动 Python 脚本
    screen -S openledger -X stuff "cd /root/openledger-bot && python3 bot.py\n" 
    echo "使用 'screen -r openledger' 命令来查看日志。"
    echo "要退出 screen 会话，请按 Ctrl+A+D。"

    # 提示用户按任意键返回主菜单
    read -n 1 -s -r -p "按任意键返回主菜单..."
}

# 删除函数
function delete_openledger() {
    # 杀死 screen 会话
    echo "正在终止 openledger screen 会话..."
    screen -S openledger -X quit 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "screen 会话已成功终止"
    else
        echo "未找到 openledger screen 会话或已终止"
    fi

    # 删除 openledger-bot 目录
    if [ -d "/root/openledger-bot" ]; then
        echo "正在删除 openledger-bot 目录..."
        rm -rf /root/openledger-bot
        echo "openledger-bot 目录已删除"
    else
        echo "未找到 openledger-bot 目录"
    fi

    # 提示用户按任意键返回主菜单
    read -n 1 -s -r -p "按任意键返回主菜单..."
}

# 主菜单函数
function main_menu() {
    while true; do
        clear
        echo "脚本由大赌社区哈哈哈哈编写，推特 @ferdie_jhovie，免费开源，请勿相信收费"
        echo "如有问题，可联系推特，仅此只有一个号"
        echo "================================================================"
        echo "退出脚本，请按键盘 ctrl + C 退出即可"
        echo "请选择要执行的操作:"
        echo "1. 安装部署openledger"
        echo "2. 删除openledger"
        echo "3. 退出"

        read -p "请输入您的选择 (1,2,3): " choice
        case $choice in
            1)
                setup_openledger  # 调用安装和配置函数
                ;;   
            2)
                delete_openledger  # 调用删除函数
                ;;
            3)
                echo "退出脚本..."
                exit 0
                ;;
            *)
                echo "无效的选择，请重试."
                read -n 1 -s -r -p "按任意键继续..."
                ;;
        esac
    done
}

# 进入主菜单
main_menu
