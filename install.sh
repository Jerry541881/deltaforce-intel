#!/bin/bash
echo "========================================"
echo "  三角洲情报站 - 一键安装脚本"
echo "========================================"
echo ""

echo "[1/4] 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ 未检测到 Node.js，请先安装 Node.js 20+"
    echo "   下载地址: https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js $(node -v) 已安装"
echo ""

echo "[2/4] 检查 Git..."
if ! command -v git &> /dev/null; then
    echo "❌ 未检测到 Git，请先安装 Git"
    echo "   下载地址: https://git-scm.com/"
    exit 1
fi
echo "✅ Git 已安装"
echo ""

echo "[3/4] 安装依赖..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi
echo "✅ 依赖安装完成"
echo ""

echo "[4/4] 启动本地预览..."
echo ""
echo "🚀 浏览器打开 http://localhost:3000 查看效果"
echo "   按 Ctrl+C 停止服务器"
echo ""
npm run dev
