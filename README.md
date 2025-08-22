# 趣体育Telegram机器人

这是一个专为趣体育平台设计的Telegram机器人，具有多语言支持和完整的用户服务功能。

## 🚀 激活功能（防止Render自动停止）

由于在Render平台上运行，机器人会在15分钟无活动后自动停止。我们添加了以下激活功能：

### 1. 自动心跳系统
- **心跳频率**: 每10分钟自动发送心跳信号
- **活动检测**: 记录所有用户交互，更新最后活动时间
- **日志记录**: 详细记录心跳状态和活动情况

### 2. 手动激活命令
- **/ping**: 检查机器人运行状态
  - 显示最后活动时间
  - 显示心跳状态
  - 显示运行环境信息

### 3. 外部激活服务
您可以使用以下服务来定期ping机器人，保持其活跃状态：

#### 选项1: UptimeRobot (免费)
- 注册 [UptimeRobot](https://uptimerobot.com/)
- 添加监控，类型选择 "HTTP(s)"
- URL设置为: `https://your-bot-domain.onrender.com/` (如果有webhook)
- 监控间隔设置为 5 分钟

#### 选项2: Cron-job.org (免费)
- 访问 [Cron-job.org](https://cron-job.org/)
- 创建新任务
- 设置定时器为每5分钟执行一次
- 目标URL: 通过Telegram Bot API发送 `/ping` 命令

#### 选项3: 自建监控脚本
```python
import requests
import time
import schedule

def ping_bot():
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": "/ping"
    }
    response = requests.post(url, data=data)
    print(f"Ping sent: {response.status_code}")

# 每5分钟执行一次
schedule.every(5).minutes.do(ping_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## 📋 主要功能

### 多语言支持
- 🇨🇳 简体中文
- 🇺🇸 English
- 🇹🇭 ไทย
- 🇻🇳 Tiếng Việt

### 核心服务
- 📝 自助注册
- 🇨🇳 大陆用户注册
- 🌍 海外用户注册
- 📣 趣体育官方招商
- 🏆 2026世界杯足球篮球推单
- 👥 人工客服
- 🌐 语言切换

## 🔧 部署说明

### 环境要求
- Python 3.8+
- python-telegram-bot 20.0+

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
# 在Render中设置
BOT_TOKEN=your_telegram_bot_token
RENDER=true
```

### 启动机器人
```bash
python bot.py
```

## 📊 监控和日志

机器人会自动记录以下信息：
- 用户交互活动
- 心跳信号状态
- 错误和异常情况
- 运行环境信息

## 🆘 故障排除

### 机器人停止响应
1. 检查 `/ping` 命令是否响应
2. 查看日志中的心跳状态
3. 确认外部监控服务是否正常工作

### 心跳任务异常
1. 检查日志中的错误信息
2. 重启机器人服务
3. 验证网络连接状态

## 📞 技术支持

如有问题，请联系：
- 官方客服: @QTY01, @QTY15, @QTY04
- 招商频道: https://t.me/QTY18
- 推单频道: https://t.me/SJB33

---

**注意**: 请确保定期检查机器人的运行状态，特别是在低流量期间，建议设置外部监控服务来保持机器人活跃。
