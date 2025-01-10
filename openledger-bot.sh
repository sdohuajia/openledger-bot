#!/bin/bash

# 安装和配置 openledger-bot 函数
function setup_openledger() {
    # 检查 openledger 目录是否存在，如果存在则删除
    if [ -d "openledger" ]; then
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

    # 安装 Node.js 和 npm（如果尚未安装）
    if ! command -v npm &> /dev/null; then
        echo "正在安装 Node.js 和 npm..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi

    # 安装 npm 依赖项
    echo "正在安装 npm 依赖项..."
    npm install || { echo "npm 依赖项安装失败"; exit 1; }

    # 获取 token 和其他信息
    read -p "请输入token: " token
    read -p "请输入workerID: " workerID
    echo  # 换行
    read -p "请输入id: " id
    echo  # 换行
    read -p "请输入ownerAddress: " ownerAddress
    echo  # 换行

    # 将信息保存到 account.txt 文件
    echo "${token}:${workerID}:${id}:${ownerAddress}" >> account.txt
    echo "信息已保存到 account.txt"

    # 配置代理信息
    read -p "请输入您的代理信息，格式为 http://user:pass@ip:port (可以为空): " proxy_info
    proxy_file="/root/openledger-bot/proxy.txt"

    # 如果代理信息不为空，则写入文件
    if [[ -n "$proxy_info" ]]; then
        echo "$proxy_info" > "$proxy_file"
        echo "代理信息已添加到 $proxy_file."
    else
        echo "没有输入代理信息，文件保持不变."
    fi

    # 检查是否安装了 screen，如果没有安装，则安装它
    if ! command -v screen &> /dev/null; then
        echo "检测到未安装 screen，正在安装..."
        sudo apt-get install -y screen || { echo "screen 安装失败"; exit 1; }
    fi

    echo "正在使用 screen 启动应用..."

    # 创建新的 screen 会话，名称为 openledger
    screen -dmS openledger bash -c "cd openledger-bot && node index.js"

    # 检查 screen 会话是否成功创建
    if screen -ls | grep -q "openledger"; then
        echo "screen 会话 openledger 已成功启动。"
    else
        echo "无法启动 screen 会话 openledger，请检查错误。"
    fi

    # 提示用户如何查看日志
    echo "使用 'screen -r openledger' 命令来查看日志。"
    echo "要退出 screen 会话，请按 Ctrl+A 然后按 D。"

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
        echo "1. 安装部署openledger "
        echo "2. 退出"

        read -p "请输入您的选择 (1,2): " choice
        case $choice in
            1)
                setup_openledger  # 调用安装和配置函数
                ;;   
            2)
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
