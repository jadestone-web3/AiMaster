#!/bin/bash

# AiMaster 后端启动脚本

echo "🚀 启动 AiMaster 后端服务..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

# 进入 backend 目录
cd "$(dirname "$0")"

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "✅ 准备就绪！"
echo ""
echo "📝 默认账号: admin"
echo "🔑 默认密码: admin123"
echo "🌐 服务地址: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/docs"
echo ""
echo "💡 提示: 修改 Chrome 插件的 API 地址为 http://localhost:8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 启动服务
python3 main.py
