#!/bin/bash

# 趣体育机器人 Render 部署脚本
# 使用方法: ./deploy.sh

echo "🚀 趣体育机器人 Render 部署脚本"
echo "================================"

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo "❌ 错误: 当前目录不是Git仓库"
    echo "请先运行: git init"
    exit 1
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  检测到未提交的更改，正在提交..."
    git add .
    git commit -m "feat: 更新部署配置"
fi

# 推送到GitHub
echo "📤 推送到GitHub..."
git push origin master

echo ""
echo "✅ 代码已推送到GitHub！"
echo ""
echo "🔧 接下来请在Render上部署："
echo "1. 访问 https://dashboard.render.com/"
echo "2. 创建新的Web Service"
echo "3. 连接您的GitHub仓库"
echo "4. 设置环境变量BOT_TOKEN"
echo "5. 部署服务"
echo ""
echo "📖 详细部署指南请查看: RENDER_DEPLOYMENT.md"
echo ""
echo "🎉 祝您部署顺利！"
