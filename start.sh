#!/bin/bash

# 股票分析系统启动脚本

echo "🚀 启动智能股票分析系统..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，设置您的 OPENAI_API_KEY"
    echo "   然后重新运行此脚本"
    exit 1
fi

# 检查OpenAI API Key
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  请在 .env 文件中设置您的 OPENAI_API_KEY"
    exit 1
fi

echo "🔧 构建和启动服务..."

# 停止现有服务
docker-compose down

# 构建并启动服务
docker-compose up --build -d

echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "🌐 访问地址："
echo "   前端应用: http://localhost:3000"
echo "   API文档:  http://localhost:8000/docs"
echo "   数据库:   localhost:5432 (用户名: stock_user, 密码: stock_pass)"
echo ""
echo "📝 使用说明："
echo "   1. 打开浏览器访问 http://localhost:3000"
echo "   2. 在股票分析页面输入股票代码进行分析"
echo "   3. 在批量任务页面创建批量分析任务"
echo "   4. 在推荐系统页面查看AI推荐"
echo "   5. 在AI助手页面与智能助手对话"
echo ""
echo "🔧 管理命令："
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""