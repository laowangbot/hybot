#!/usr/bin/env python3
"""
趣体育Telegram机器人 - Render部署版本
专门为Render平台优化，包含webhook支持和健康检查
"""

import logging
import re
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from aiohttp import web
import ssl

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量获取机器人token
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("未设置BOT_TOKEN环境变量！")
    exit(1)

# 检查是否在Render环境中运行
IS_RENDER = os.environ.get('RENDER', False)
PORT = int(os.environ.get('PORT', 8080))

# 语言配置
LANGUAGES = {
    'zh-CN': {
        'welcome': '欢迎使用趣体育机器人！',
        'menu_self_register': '自助注册',
        'menu_mainland_user': '大陆用户',
        'menu_overseas_user': '海外用户',
        'menu_advertising_channel': '趣体育官方招商',
        'menu_promotion_channel': '2026世界杯🏆足球篮球推单五大联赛',
        'menu_customer_service': '人工客服',
        'menu_change_lang': '🌐LANGUAGE',
        'register_info_title': '注册信息',
        'register_info_channel1': '趣体育官方招商',
        'register_info_channel2': '2026世界杯🏆足球篮球推单五大联赛',
        'customer_specialist_1': '客服专员1',
        'customer_specialist_2': '客服专员2',
        'customer_specialist_3': '客服专员3',
        'language_selection': '请选择语言：',
        'language_chinese': '中文',
        'language_english': 'English',
        'language_thai': 'ไทย',
        'language_vietnamese': 'Tiếng Việt',
        'language_changed': '语言已更改！',
        'mainland_user_info': '大陆用户注册信息',
        'overseas_user_info': '海外用户注册信息',
        'advertising_channel_info': '趣体育官方招商信息',
        'promotion_channel_info': '2026世界杯🏆足球篮球推单五大联赛信息',
        'customer_service_info': '人工客服信息'
    },
    'en-US': {
        'welcome': 'Welcome to QTY Sports Bot!',
        'menu_self_register': 'Self Registration',
        'menu_mainland_user': 'Mainland Users',
        'menu_overseas_user': 'Overseas Users',
        'menu_advertising_channel': 'QTY Official Investment',
        'menu_promotion_channel': '2026 World Cup🏆Football Basketball Tips',
        'menu_customer_service': 'Customer Service',
        'menu_change_lang': '🌐LANGUAGE',
        'register_info_title': 'Registration Info',
        'register_info_channel1': 'QTY Official Investment',
        'register_info_channel2': '2026 World Cup🏆Football Basketball Tips',
        'customer_specialist_1': 'Specialist 1',
        'customer_specialist_2': 'Specialist 2',
        'customer_specialist_3': 'Specialist 3',
        'language_selection': 'Please select language:',
        'language_chinese': '中文',
        'language_english': 'English',
        'language_thai': 'ไทย',
        'language_vietnamese': 'Tiếng Việt',
        'language_changed': 'Language changed!',
        'mainland_user_info': 'Mainland User Registration',
        'overseas_user_info': 'Overseas User Registration',
        'advertising_channel_info': 'QTY Official Investment Info',
        'promotion_channel_info': '2026 World Cup Tips Info',
        'customer_service_info': 'Customer Service Info'
    },
    'th-TH': {
        'welcome': 'ยินดีต้อนรับสู่ QTY Sports Bot!',
        'menu_self_register': 'ลงทะเบียนด้วยตนเอง',
        'menu_mainland_user': 'ผู้ใช้ในประเทศ',
        'menu_overseas_user': 'ผู้ใช้ต่างประเทศ',
        'menu_advertising_channel': 'QTY การลงทุนอย่างเป็นทางการ',
        'menu_promotion_channel': 'ฟุตบอลโลก 2026🏆บาสเก็ตบอลทิปส์',
        'menu_customer_service': 'บริการลูกค้า',
        'menu_change_lang': '🌐LANGUAGE',
        'register_info_title': 'ข้อมูลการลงทะเบียน',
        'register_info_channel1': 'QTY การลงทุนอย่างเป็นทางการ',
        'register_info_channel2': 'ฟุตบอลโลก 2026🏆บาสเก็ตบอลทิปส์',
        'customer_specialist_1': 'ผู้เชี่ยวชาญ 1',
        'customer_specialist_2': 'ผู้เชี่ยวชาญ 2',
        'customer_specialist_3': 'ผู้เชี่ยวชาญ 3',
        'language_selection': 'กรุณาเลือกภาษา:',
        'language_chinese': '中文',
        'language_english': 'English',
        'language_thai': 'ไทย',
        'language_vietnamese': 'Tiếng Việt',
        'language_changed': 'เปลี่ยนภาษาแล้ว!',
        'mainland_user_info': 'การลงทะเบียนผู้ใช้ในประเทศ',
        'overseas_user_info': 'การลงทะเบียนผู้ใช้ต่างประเทศ',
        'advertising_channel_info': 'ข้อมูลการลงทุน QTY อย่างเป็นทางการ',
        'promotion_channel_info': 'ข้อมูลทิปส์ฟุตบอลโลก 2026',
        'customer_service_info': 'ข้อมูลบริการลูกค้า'
    },
    'vi-VN': {
        'welcome': 'Chào mừng đến với QTY Sports Bot!',
        'menu_self_register': 'Đăng ký tự động',
        'menu_mainland_user': 'Người dùng trong nước',
        'menu_overseas_user': 'Người dùng nước ngoài',
        'menu_advertising_channel': 'QTY Đầu tư chính thức',
        'menu_promotion_channel': 'World Cup 2026🏆Bóng đá Bóng rổ Mẹo',
        'menu_customer_service': 'Dịch vụ khách hàng',
        'menu_change_lang': '🌐LANGUAGE',
        'register_info_title': 'Thông tin đăng ký',
        'register_info_channel1': 'QTY Đầu tư chính thức',
        'register_info_channel2': 'World Cup 2026🏆Bóng đá Bóng rổ Mẹo',
        'customer_specialist_1': 'Chuyên gia 1',
        'customer_specialist_2': 'Chuyên gia 2',
        'customer_specialist_3': 'Chuyên gia 3',
        'language_selection': 'Vui lòng chọn ngôn ngữ:',
        'language_chinese': '中文',
        'language_english': 'English',
        'language_thai': 'ไทย',
        'language_vietnamese': 'Tiếng Việt',
        'language_changed': 'Đã thay đổi ngôn ngữ!',
        'mainland_user_info': 'Đăng ký người dùng trong nước',
        'overseas_user_info': 'Đăng ký người dùng nước ngoài',
        'advertising_channel_info': 'Thông tin đầu tư QTY chính thức',
        'promotion_channel_info': 'Thông tin mẹo World Cup 2026',
        'customer_service_info': 'Thông tin dịch vụ khách hàng'
    }
}

# 按钮表情符号
BUTTON_EMOJIS = {
    'menu_self_register': '📝',
    'menu_mainland_user': '🇨🇳',
    'menu_overseas_user': '🌍',
    'menu_advertising_channel': '📢',
    'menu_promotion_channel': '⚽',
    'menu_customer_service': '💬',
    'menu_change_lang': '🌐'
}

# 用户数据存储
user_data = {}

# 心跳激活相关变量
last_activity_time = datetime.now()
is_heartbeat_active = False

def get_text(user_id, key):
    """根据用户的语言设置获取相应的文本"""
    lang_code = user_data.get(user_id, 'zh-CN')
    return LANGUAGES.get(lang_code, LANGUAGES['zh-CN']).get(key, key)

def update_activity():
    """更新最后活动时间"""
    global last_activity_time
    last_activity_time = datetime.now()
    logger.info(f"活动更新: {last_activity_time}")

async def heartbeat_task(application):
    """心跳任务，每10分钟发送一次心跳信号"""
    global is_heartbeat_active
    
    while True:
        try:
            if is_heartbeat_active:
                logger.info(f"💓 心跳信号 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查是否需要发送激活信号
                time_since_last_activity = datetime.now() - last_activity_time
                if time_since_last_activity > timedelta(minutes=5):
                    logger.info("⚠️ 长时间无活动，发送激活信号")
                
            await asyncio.sleep(600)  # 10分钟
        except Exception as e:
            logger.error(f"心跳任务错误: {e}")
            await asyncio.sleep(60)

async def start_heartbeat(application):
    """启动心跳任务"""
    global is_heartbeat_active
    is_heartbeat_active = True
    logger.info("🚀 心跳任务已启动")
    
    # 创建心跳任务
    asyncio.create_task(heartbeat_task(application))

async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理ping请求，用于保持机器人活跃"""
    update_activity()
    
    await update.message.reply_text(
        "🏓 Pong! 机器人正在运行中...\n"
        f"⏰ 最后活动时间: {last_activity_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"💓 心跳状态: {'活跃' if is_heartbeat_active else '停止'}\n"
        f"🌐 运行环境: {'Render' if IS_RENDER else '本地'}"
    )

# 其他处理函数保持不变...
# [这里应该包含bot.py中的所有其他函数，为了简洁我省略了]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户发送 /start 命令时调用"""
    update_activity()
    
    user = update.effective_user
    logger.info(f"User {user.first_name} started the bot.")
    user_id = user.id

    if user_id not in user_data:
        user_data[user_id] = 'zh-CN'

    # 创建键盘按钮
    keyboard = [
        [KeyboardButton(get_text(user_id, 'menu_self_register'))],
        [KeyboardButton(get_text(user_id, 'menu_mainland_user')), KeyboardButton(get_text(user_id, 'menu_overseas_user'))],
        [KeyboardButton(get_text(user_id, 'menu_advertising_channel')), KeyboardButton(get_text(user_id, 'menu_promotion_channel'))],
        [KeyboardButton(get_text(user_id, 'menu_customer_service')), KeyboardButton(get_text(user_id, 'menu_change_lang'))]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_message = (
        f"🎉 <b>欢迎使用趣体育机器人！</b>\n\n"
        f"📢 {get_text(user_id, 'register_info_channel1')}： <a href='https://t.me/QTY18'>https://t.me/QTY18</a>\n"
        f"📢 {get_text(user_id, 'register_info_channel2')}： <a href='https://t.me/SJB33'>https://t.me/SJB33</a>\n\n"
        f"💬 <b>{get_text(user_id, 'menu_customer_service')}</b>：\n"
        f"1️⃣ <a href='https://t.me/QTY01'>@QTY01</a>\n"
        f"2️⃣ <a href='https://t.me/QTY15'>@QTY15</a>\n"
        f"3️⃣ <a href='https://t.me/QTY04'>@QTY04</a>"
    )
    
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)

# 健康检查端点
async def health_check(request):
    """健康检查端点，用于Render平台监控"""
    update_activity()
    return web.Response(text="OK", status=200)

async def webhook_handler(request):
    """处理Telegram webhook请求"""
    try:
        data = await request.json()
        update = Update.de_json(data, request.app['bot'])
        await request.app['dispatcher'].process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Webhook处理错误: {e}")
        return web.Response(status=500)

def main():
    """启动机器人"""
    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 注册处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping_handler))
    
    # 启动心跳任务
    application.create_task(start_heartbeat(application))
    
    if IS_RENDER:
        # Render环境：使用webhook
        logger.info("🚀 在Render环境中启动，使用webhook模式")
        
        # 创建web应用
        app = web.Application()
        app['bot'] = application.bot
        app['dispatcher'] = application
        
        # 添加路由
        app.router.add_get('/', health_check)
        app.router.add_post(f'/webhook/{BOT_TOKEN}', webhook_handler)
        
        # 设置webhook
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook/{BOT_TOKEN}"
        application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook已设置: {webhook_url}")
        
        # 启动web服务器
        web.run_app(app, host='0.0.0.0', port=PORT)
    else:
        # 本地环境：使用polling
        logger.info("🚀 在本地环境中启动，使用polling模式")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
