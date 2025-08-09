# bot.py - 修正后的 Telegram 机器人代码，使用 FastAPI 框架
# This file has been updated to ensure all language welcome messages are consistent.

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Optional
from fastapi import FastAPI, Request, Response
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# 1. 设置 Bot Token 和 Webhook URL
# 建议将这些值储存在环境变量中
# ⚠️ 注意: 这里的 BOT_TOKEN 是范例，请替换成您自己的 Token
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# Webhook URL 路径应是一个安全且不公开的字符串，与 BOT_TOKEN 分开
WEBHOOK_URL_PATH = f"/telegram-webhook"
# 如果 WEBHOOK_URL 没有设置，程序将会退出
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL 环境变量未设置。无法以 Webhook 模式运行。")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 环境变量未设置。")

PORT = int(os.environ.get("PORT", 5000))

# 2. 启用日志记录
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. 定义游戏的 URL 和客服句柄
GAME_URL_QU = "https://www.qu32.vip:30011/entry/register/?i_code=6944642"
GAME_URL_MK = "https://www.mk2001.com:9081/CHS"
CS_HANDLE = "@QTY18"

# 定义按钮的表情符号
BUTTON_EMOJIS = {
    'menu_account_info': '🏠',
    'menu_play_game': '▶️',
    'menu_advertising_channel': '👋',
    'menu_promotion_channel': '📢',
    'menu_invite_friend': '🎁',
    'menu_customer_service': '👥',
    'menu_download_app': '📱',
    'menu_change_lang': '🌐',
    'menu_self_register': '📝',
    'menu_mainland_user': '🇨🇳',
    'menu_overseas_user': '🌍',
}

# 4. 准备多语言文本
LANGUAGES = {
    'zh-CN': {
        # 新的 /start 命令欢迎资讯
        'start_welcome_html': """🎉 嗨，{user} ！欢迎来到 趣体育⚽️MKsports
我是您的专属注册服务助手，请选择您需要的服务👇
 
🔥 限时福利活动（30天）
 💎 活动期间 注册并储值成功
 🎁 即可获赠 价值 398 元 VIP 会员
 
📢 招商频道
 👉 <a href="https://t.me/QTY18">https://t.me/QTY18</a>
 
📢 推单频道
 👉 <a href="https://t.me/AISOUOO">https://t.me/AISOUOO</a>
 
💬 官方客服
 1️⃣ <a href="https://t.me/QTY01">@QTY01</a>
 2️⃣ <a href="https://t.me/QTY15">@QTY15</a>
 3️⃣ <a href="https://t.me/QTY04">@QTY04</a>""",
        'welcome': "🎉 嗨，{user}！欢迎来到趣体育⚽️MKsports。我是您的专属注册服务助手，请在下方选择您需要的服务。\n\n",
        'main_menu_prompt': "请从主菜单中选择一个选项。",
        'menu_account_info': "注册账号",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}进入游戏",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}招商频道",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}推单频道",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}邀请好友",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}人工客服",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}下载APP",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Language",
        'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}自助注册",
        'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}大陆用户",
        'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}海外用户",
        'live_customer_service_title': "请点击以下客服专员联系：",
        'customer_specialist_1': "客服专员一",
        'customer_specialist_2': "客服专员二",
        'customer_specialist_3': "客服专员三",
        'download_app_info': "点击下方按钮下载应用程序：",
        'download_android': "安卓下载",
        'download_ios': "苹果下载",
        'invite_title': "❤️邀请好友注册赚取奖金",
        'invite_message': "👉邀请您的好友，联系客服专员获取您的奖金!",
        'invite_link_heading': "邀请链接 🔗",
        'invite_link_qu': "趣体育（大陆用户）\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
        'invite_link_mk': "MK体育（全球用户）\nhttps://www.mk2001.com:9081/CHS",
        'language_selection': "请选择您的语言：",
        'lang_changed': "语言已成功切换！",
        'welcome_to_sports': "欢迎来到 quSports！",
        'official_group_handle': "官方群组： @QTY18",
        'official_channel_handle': "官方频道： @QTY18 ",
        'customer_service_handle': "官方客服： @QTY01",
        'account_info_title': "我的账户",
        'member_id': "会员 ID： {user_id}",
        'member_account': "会员账号： {username}",
        'balance': "账户余额： {balance:.2f}CNY",
        'vip_level': "会员等级： VIP{vip}",
        'advertising_channel_prompt': "点击下方按钮进入招商频道：",
        'promotion_channel_prompt': "点击下方按钮进入推单频道：",
        'play_game_choice_prompt': "请选择您要进入的游戏：",
        'register_info_title': "欢迎来到 趣体育⚽️MKsports",
        'register_info_channel1': "招商频道",
        'register_info_channel2': "推单频道",
        'register_info_cs1': "官方客服1",
        'register_info_cs2': "官方客服2",
        'register_info_cs3': "官方客服3",
        'register_info_qu_link_text': "趣体育（大陆用户注册）",
        'register_info_mk_link_text': "MK体育（全球用户）",
        'register_info_notice_prompt': "请点击下方按钮前往注册：",
        'register_info_download_notice': """
        📝 <b>注册注意事项</b>
        1️⃣ <b>请勿直接下载APP</b>
        ‼<b>★ 重要提醒 ★</b>‼ 请先完成账号注册 → 由专员登记福利 → 再下载APP

        2️⃣ <b>注册需使用实名信息</b>
        我们是正规平台，为确保顺利提现，请务必使用真实姓名注册。

        3️⃣ <b>手机号与实名一致</b>
        注册手机号必须与实名信息相符。

        4️⃣ <b>安卓APP无法打开</b>
        如遇问题，请联系专员协助处理。
        """,
        'download_app_qu_title': "趣体育",
        'download_app_mk_title': "MK体育",
        'game_qu_name': "趣体育",
        'game_mk_name': "MK体育",
        'welcome_text_html': "🎉 嗨，{user} ！欢迎来到 趣体育⚽️MKsports",
        
        # 新增: 自助注册的完整资讯
        'self_register_info_html': """🎉 嗨，{user} ！欢迎来到 趣体育⚽️MKsports
我是您的专属注册服务助手，请选择您需要的服务👇
 
🔥 限时福利活动（30天）
 💎 活动期间 注册并储值成功
 🎁 即可获赠 价值 398 元 VIP 会员
 
📢 招商频道
 👉 <a href="https://t.me/QTY18">https://t.me/QTY18</a>
 
📢 推单频道
 👉 <a href="https://t.me/AISOUOO">https://t.me/AISOUOO</a>
 
💬 官方客服
 1️⃣ <a href="https://t.me/QTY01">@QTY01</a>
 2️⃣ <a href="https://t.me/QTY15">@QTY15</a>
 3️⃣ <a href="https://t.me/QTY04">@QTY04</a>

📝 <b>注册注意事项</b>
 1️⃣ <b>请勿直接下载APP</b>
 ‼<b>★ 重要提醒 ★</b>‼ 请先完成账号注册 → 由专员登记福利 → 再下载APP

 2️⃣ <b>注册需使用实名信息</b>
 我们是正规平台，为确保顺利提现，请务必使用真实姓名注册。

 3️⃣ <b>手机号与实名一致</b>
 注册手机号必须与实名信息相符。

 4️⃣ <b>安卓APP无法打开</b>
 如遇问题，请联系专员协助处理。
"""
    },
    'en': {
        # New welcome message for the /start command
        'start_welcome_html': """🎉 Hey, {user}! Welcome to quSports⚽️MKsports
I'm your exclusive registration service assistant. Please choose the service you need below👇
 
🔥 Limited-Time Offer (30 days)
 💎 During the event, successfully register and top up
 🎁 You will receive a free VIP membership worth 398 CNY
 
📢 Advertising Channel
 👉 <a href="https://t.me/QTY18">https://t.me/QTY18</a>
 
📢 Promotion Channel
 👉 <a href="https://t.me/AISOUOO">https://t.me/AISOUOO</a>
 
💬 Official Customer Service
 1️⃣ <a href="https://t.me/QTY01">@QTY01</a>
 2️⃣ <a href="https://t.me/QTY15">@QTY15</a>
 3️⃣ <a href="https://t.me/QTY04">@QTY04</a>""",
        'welcome': "Welcome to quSports {user}, click on the menu below to interact.",
        'main_menu_prompt': "Please select an option from the main menu.",
        'menu_account_info': "Register Account",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}Play Game",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}Advertising Channel",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}Promotion Channel",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}Invite Friends",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}Customer Service",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}Download APP",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Language",
        'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}Self-Registration",
        'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}Mainland User",
        'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}Overseas User",
        'live_customer_service_title': "Please click on a customer service specialist to contact:",
        'customer_specialist_1': "Specialist 1",
        'customer_specialist_2': "Specialist 2",
        'customer_specialist_3': "Specialist 3",
        'download_app_info': "Click the buttons below to download the app:",
        'download_android': "Android Download",
        'download_ios': "iOS Download",
        'invite_title': "Invite friends and earn money together!",
        'invite_message': "By inviting friends to register through your exclusive link, you can get rich rewards!",
        'invite_link_heading': "Your invitation link  ",
        'invite_link_qu': "quSports (Mainland China Users)\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
        'invite_link_mk': "MK Sports (Global Users)\nhttps://www.mk2001.com:9081/CHS",
        'language_selection': "Please select your language:",
        'lang_changed': "Language switched successfully!",
        'welcome_to_sports': "Welcome to quSports!",
        'official_group_handle': "Official Group: @quyuyule",
        'official_channel_handle': "Official Channel: @qu337",
        'customer_service_handle': "Official Customer Service: @maoyiyule",
        'account_info_title': "My Account",
        'member_id': "Member ID: {user_id}",
        'member_account': "Member Account: {username}",
        'balance': "Account Balance: {balance:.2f}CNY",
        'vip_level': "Member Level: VIP{vip}",
        'advertising_channel_prompt': "Click the button below to enter the advertising channel:",
        'promotion_channel_prompt': "Click the button below to enter the promotion channel:",
        'play_game_choice_prompt': "Please select the game you want to enter:",
        'register_info_title': "Welcome to quSports⚽️MKsports",
        'register_info_channel1': "Advertising Channel",
        'register_info_channel2': "Promotion Channel",
        'register_info_cs1': "Official Customer Service 1",
        'register_info_cs2': "Official Customer Service 2",
        'register_info_cs3': "Official Customer Service 3",
        'register_info_qu_link_text': "quSports (Mainland China Users)",
        'register_info_mk_link_text': "MK Sports (Global Users)",
        'register_info_notice_prompt': "Please click the button below to register:",
        'register_info_download_notice': """
        📝 <b>Registration Notes</b>
        1️⃣ <b>Do Not Download the APP Directly</b>
        ‼<b>★ Important Reminder ★</b>‼ Please complete account registration first → Register for benefits with a specialist → Then download the APP

        2️⃣ <b>Registration Requires Real Name Information</b>
        We are a legitimate platform. To ensure smooth withdrawals, please use your real name for registration.

        3️⃣ <b>Mobile Number and Name Must Match</b>
        The registered mobile number must match the real name information.

        4️⃣ <b>Android APP cannot be opened</b>
        If you encounter problems, please contact a specialist for assistance.
        """,
        'download_app_qu_title': "quSports",
        'download_app_mk_title': "MK Sports",
        'game_qu_name': "quSports",
        'game_mk_name': "MK Sports",
        'welcome_text_html': "🎉 Hey, {user}! Welcome to quSports⚽️MKsports",
        
        # 新增: 自助注册的完整资讯
        'self_register_info_html': """🎉 Hey, {user}! Welcome to quSports⚽️MKsports
I'm your exclusive registration service assistant. Please choose the service you need below👇
 
🔥 Limited-Time Offer (30 days)
 💎 During the event, successfully register and top up
 🎁 You will receive a free VIP membership worth 398 CNY
 
📢 Advertising Channel
 👉 <a href="https://t.me/QTY18">https://t.me/QTY18</a>
 
📢 Promotion Channel
 👉 <a href="https://t.me/AISOUOO">https://t.me/AISOUOO</a>
 
💬 Official Customer Service
 1️⃣ <a href="https://t.me/QTY01">@QTY01</a>
 2️⃣ <a href="https://t.me/QTY15">@QTY15</a>
 3️⃣ <a href="https://t.me/QTY04">@QTY04</a>

📝 <b>Registration Notes</b>
 1️⃣ <b>Do Not Download the APP Directly</b>
 ‼<b>★ Important Reminder ★</b>‼ Please complete account registration first → Register for benefits with a specialist → Then download the APP

 2️⃣ <b>Registration Requires Real Name Information</b>
 We are a legitimate platform. To ensure smooth withdrawals, please use your real name for registration.

 3️⃣ <b>Mobile Number and Name Must Match</b>
 The registered mobile number must match the real name information.

 4️⃣ <b>Android APP cannot be opened</b>
 If you encounter problems, please contact a specialist for assistance.
"""
    },
    'th': {
        # New welcome message for the /start command
        'start_welcome_html': """🎉 สวัสดีครับ/ค่ะ {user}! ยินดีต้อนรับสู่ quSports⚽️MKsports
ฉันคือผู้ช่วยบริการลงทะเบียนพิเศษของคุณ กรุณาเลือกบริการที่คุณต้องการด้านล่าง👇
 
🔥 โปรโมชั่นพิเศษ (30 วัน)
 💎 ในช่วงกิจกรรม ลงทะเบียนและเติมเงินสำเร็จ
 🎁 คุณจะได้รับสมาชิก VIP มูลค่า 398 หยวนฟรี
 
📢 ช่องทางการโฆษณา
 👉 <a href="https://t.me/QTY18">https://t.me/QTY18</a>
 
📢 ช่องทางโปรโมชั่น
 👉 <a href="https://t.me/AISOUOO">https://t.me/AISOUOO</a>
 
💬 บริการลูกค้าอย่างเป็นทางการ
 1️⃣ <a href="https://t.me/QTY01">@QTY01</a>
 2️⃣ <a href="https://t.me/QTY15">@QTY15</a>
 3️⃣ <a href="https://t.me/QTY04">@QTY04</a>""",
        'welcome': "ยินดีต้อนรับสู่ quSports {user} คลิกที่เมนูด้านล่างเพื่อโต้ตอบ",
        'main_menu_prompt': "กรุณาเลือกตัวเลือกจากเมนูหลัก",
        'menu_account_info': "ลงทะเบียนบัญชี",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}เข้าสู่เกม",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}ช่องทางการโฆษณา",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}ช่องทางโปรโมชั่น",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}เชิญเพื่อน",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}บริการลูกค้า",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}ดาวน์โหลดแอป",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Language",
        'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}ลงทะเบียนด้วยตนเอง",
        'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}ผู้ใช้ในจีนแผ่นดินใหญ่",
        'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}ผู้ใช้ทั่วโลก",
        'live_customer_service_title': "กรุณาคลิกที่ผู้เชี่ยวชาญบริการลูกค้าด้านล่างเพื่อติดต่อ:",
        'customer_specialist_1': "ผู้เชี่ยวชาญ 1",
        'customer_specialist_2': "ผู้เชี่ยวชาญ 2",
        'customer_specialist_3': "ผู้เชี่ยวชาญ 3",
        'download_app_info': "คลิกปุ่มด้านล่างเพื่อดาวน์โหลดแอป:",
        'download_android': "ดาวน์โหลด Android",
        'download_ios': "ดาวน์โหลด iOS",
        'invite_title': "เชิญเพื่อนและรับเงินด้วยกัน!",
        'invite_message': "โดยการเชิญเพื่อนให้ลงทะเบียนผ่านลิงก์พิเศษของคุณ คุณจะได้รับรางวัลมากมาย!",
        'invite_link_heading': "ลิงก์เชิญ 🔗",
        'invite_link_qu': "quSports (ผู้ใช้ในจีน)\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
        'invite_link_mk': "MK Sports (ผู้ใช้ทั่วโลก)\nhttps://www.mk2001.com:9081/CHS",
        'language_selection': "กรุณาเลือกภาษาของคุณ:",
        'lang_changed': "เปลี่ยนภาษาเรียบร้อยแล้ว!",
        'welcome_to_sports': "ยินดีต้อนรับสู่ quSports!",
        'official_group_handle': "กลุ่มทางการ: @quyuyule",
        'official_channel_handle': "ช่องทางการ: @qu337",
        'customer_service_handle': "บริการลูกค้าทางการ: @maoyiyule",
        'account_info_title': "บัญชีของฉัน",
        'member_id': "ID สมาชิก: {user_id}",
        'member_account': "บัญชีสมาชิก: {username}",
        'balance': "ยอดคงเหลือในบัญชี: {balance:.2f}CNY",
        'vip_level': "ระดับ VIP: VIP{vip}",
        'advertising_channel_prompt': "คลิกปุ่มด้านล่างเพื่อเข้าสู่ช่องทางการโฆษณา:",
        'promotion_channel_prompt': "คลิกปุ่มด้านล่างเพื่อเข้าสู่ช่องทางโปรโมชั่น:",
        'play_game_choice_prompt': "กรุณาเลือกเกมที่คุณต้องการเข้า:",
        'register_info_title': "ยินดีต้อนรับสู่ quSports⚽️MKsports",
        'register_info_channel1': "ช่องทางการโฆษณา",
        'register_info_channel2': "ช่องทางโปรโมชั่น",
        'register_info_cs1': "บริการลูกค้า 1",
        'register_info_cs2': "บริการลูกค้า 2",
        'register_info_cs3': "บริการลูกค้า 3",
        'register_info_qu_link_text': "quSports (ผู้ใช้ในจีน)",
        'register_info_mk_link_text': "MK Sports (ผู้ใช้ทั่วโลก)",
        'register_info_notice_prompt': "กรุณาคลิกปุ่มด้านล่างเพื่อลงทะเบียน:",
        'register_info_download_notice': """
        📝 <b>ข้อควรทราบเกี่ยวกับการลงทะเบียน</b>
        1️⃣ <b>ห้ามดาวน์โหลดแอปโดยตรง</b>
        ‼<b>★ ข้อควรจำที่สำคัญ ★</b>‼ โปรดลงทะเบียนบัญชีให้เรียบร้อยก่อน → ลงทะเบียนรับสิทธิประโยชน์กับผู้เชี่ยวชาญ → จากนั้นจึงดาวน์โหลดแอป

        2️⃣ <b>การลงทะเบียนต้องใช้ชื่อจริง</b>
        เราเป็นแพลตฟอร์มที่ถูกต้องตามกฎหมาย เพื่อให้การถอนเงินเป็นไปอย่างราบรื่น โปรดใช้ชื่อจริงในการลงทะเบียน.

        3️⃣ <b>หมายเลขโทรศัพท์และชื่อจริงต้องตรงกัน</b>
        หมายเลขโทรศัพท์ที่ลงทะเบียนจะต้องตรงกับข้อมูลชื่อจริง.

        4️⃣ <b>ไม่สามารถเปิดแอป Android ได้</b>
        หากพบปัญหา โปรดติดต่อผู้เชี่ยวชาญเพื่อขอความช่วยเหลือ.
        """,
        'download_app_qu_title': "quSports",
        'download_app_mk_title': "MK Sports",
        'game_qu_name': "quSports",
        'game_mk_name': "MK Sports",
        'welcome_text_html': "🎉 สวัสดีครับ {user}! ยินดีต้อนรับสู่ quSports⚽️MKsports",
        
        # 新增: 自助注册的完整资讯
        'self_register_info_html': """🎉 สวัสดีครับ/ค่ะ {user}! ยินดีต้อนรับสู่ quSports⚽️MKsports
ฉันคือผู้ช่วยบริการลงทะเบียนพิเศษของคุณ กรุณาเลือกบริการที่คุณต้องการด้านล่าง👇
 
🔥 โปรโมชั่นพิเศษ (30 วัน)
 💎 ในช่วงกิจกรรม ลงทะเบียนและเติมเงินสำเร็จ
 🎁 คุณจะได้รับสมาชิก VIP มูลค่า 398 หยวนฟรี
 
📢 ช่องทางการโฆษณา
 👉 <a href="https://t.me/QTY18">https://t.me/QTY18</a>
 
📢 ช่องทางโปรโมชั่น
 👉 <a href="https://t.me/AISOUOO">https://t.me/AISOUOO</a>
 
💬 บริการลูกค้าอย่างเป็นทางการ
 1️⃣ <a href="https://t.me/QTY01">@QTY01</a>
 2️⃣ <a href="https://t.me/QTY15">@QTY15</a>
 3️⃣ <a href="https://t.me/QTY04">@QTY04</a>

📝 <b>ข้อควรทราบเกี่ยวกับการลงทะเบียน</b>
 1️⃣ <b>ห้ามดาวน์โหลดแอปโดยตรง</b>
 ‼<b>★ ข้อควรจำที่สำคัญ ★</b>‼ โปรดลงทะเบียนบัญชีให้เรียบร้อยก่อน → ลงทะเบียนรับสิทธิประโยชน์กับผู้เชี่ยวชาญ → จากนั้นจึงดาวน์โหลดแอป

 2️⃣ <b>การลงทะเบียนต้องใช้ชื่อจริง</b>
 เราเป็นแพลตฟอร์มที่ถูกต้องตามกฎหมาย เพื่อให้การถอนเงินเป็นไปอย่างราบรื่น โปรดใช้ชื่อจริงในการลงทะเบียน.

 3️⃣ <b>หมายเลขโทรศัพท์และชื่อจริงต้องตรงกัน</b>
 หมายเลขโทรศัพท์ที่ลงทะเบียนจะต้องตรงกับข้อมูลชื่อจริง.

 4️⃣ <b>ไม่สามารถเปิดแอป Android ได้</b>
 หากพบปัญหา โปรดติดต่อผู้เชี่ยวชาญเพื่อขอความช่วยเหลือ.
"""
    }
}


# 5. 定义命令处理器
# 在处理器中，我们会根据用户的语言设置动态生成键盘和文本

# /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 根据用户的语言代码取得相应的语言文本
    lang_code = update.effective_user.language_code
    lang_data = LANGUAGES.get(lang_code, LANGUAGES['zh-CN'])  # 默认为中文

    # 创建一个动态键盘
    keyboard = [
        [
            InlineKeyboardButton(lang_data['menu_account_info'], callback_data='register_info'),
            InlineKeyboardButton(lang_data['menu_play_game'], callback_data='play_game_choice'),
        ],
        [
            InlineKeyboardButton(lang_data['menu_recharge'], url=lang_data['advertising_channel_prompt']), # 使用 url 连接到频道
            InlineKeyboardButton(lang_data['menu_withdraw'], url=lang_data['promotion_channel_prompt']), # 使用 url 连接到频道
        ],
        [
            InlineKeyboardButton(lang_data['menu_invite_friend'], callback_data='invite_friends'),
            InlineKeyboardButton(lang_data['menu_customer_service'], callback_data='live_customer_service'),
        ],
        [
            InlineKeyboardButton(lang_data['menu_download_app'], callback_data='download_app'),
            InlineKeyboardButton(lang_data['menu_change_lang'], callback_data='change_lang'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 发送欢迎消息，并附上键盘
    await update.message.reply_html(
        lang_data['start_welcome_html'].format(user=update.effective_user.mention_html()),
        reply_markup=reply_markup,
        disable_web_page_preview=True # 禁用预览以保持格式整洁
    )


# 处理按钮回调的处理器
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lang_code = update.effective_user.language_code
    lang_data = LANGUAGES.get(lang_code, LANGUAGES['zh-CN'])  # 默认为中文

    callback_data = query.data

    if callback_data == 'change_lang':
        keyboard = [
            [
                InlineKeyboardButton("简体中文", callback_data='set_lang_zh-CN'),
                InlineKeyboardButton("English", callback_data='set_lang_en'),
                InlineKeyboardButton("ไทย", callback_data='set_lang_th'),
            ],
            [
                InlineKeyboardButton("返回", callback_data='start_menu'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(lang_data['language_selection'], reply_markup=reply_markup)
        
    elif callback_data.startswith('set_lang_'):
        new_lang_code = callback_data.split('_')[2]
        context.user_data['language'] = new_lang_code
        new_lang_data = LANGUAGES.get(new_lang_code, LANGUAGES['zh-CN'])
        await query.edit_message_text(new_lang_data['lang_changed'])
        
        # 显示主菜单
        keyboard = [
            [
                InlineKeyboardButton(new_lang_data['menu_account_info'], callback_data='register_info'),
                InlineKeyboardButton(new_lang_data['menu_play_game'], callback_data='play_game_choice'),
            ],
            [
                InlineKeyboardButton(new_lang_data['menu_recharge'], url=new_lang_data['advertising_channel_prompt']),
                InlineKeyboardButton(new_lang_data['menu_withdraw'], url=new_lang_data['promotion_channel_prompt']),
            ],
            [
                InlineKeyboardButton(new_lang_data['menu_invite_friend'], callback_data='invite_friends'),
                InlineKeyboardButton(new_lang_data['menu_customer_service'], callback_data='live_customer_service'),
            ],
            [
                InlineKeyboardButton(new_lang_data['menu_download_app'], callback_data='download_app'),
                InlineKeyboardButton(new_lang_data['menu_change_lang'], callback_data='change_lang'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_html(new_lang_data['start_welcome_html'].format(user=query.from_user.mention_html()),
                                       reply_markup=reply_markup,
                                       disable_web_page_preview=True)

    elif callback_data == 'start_menu':
        await start(update, context)

    # 处理自助注册按钮
    elif callback_data == 'register_info':
        # 处理语言选择
        lang_code = context.user_data.get('language', update.effective_user.language_code)
        lang_data = LANGUAGES.get(lang_code, LANGUAGES['zh-CN'])
        
        keyboard = [
            [
                InlineKeyboardButton(lang_data['menu_mainland_user'], url=GAME_URL_QU),
                InlineKeyboardButton(lang_data['menu_overseas_user'], url=GAME_URL_MK),
            ],
            [
                InlineKeyboardButton("返回", callback_data='start_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=lang_data['register_info_title'],
            reply_markup=reply_markup
        )

# 处理非命令消息
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 这里可以根据用户的消息内容，给予不同的回应。
    # 范例：如果用户发送了 "hello"，机器人回复 "Hi there!"
    if update.message.text.lower() == "hello":
        await update.message.reply_text("Hi there!")

# Lifespan 事件处理器用于在应用程序启动和关闭时执行代码
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    设置 Telegram 机器人的 Application 实例并在服务器启动时启动它。
    当服务器关闭时，它会停止应用程序。
    """
    global application

    # 创建应用程序实例
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .updater(None)
        .build()
    )

    # 注册所有处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # 在启动时设置 Webhook
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}{WEBHOOK_URL_PATH}")
    logger.info(f"Webhook 已设置到: {WEBHOOK_URL}{WEBHOOK_URL_PATH}")

    await application.initialize()
    await application.start()
    
    yield  # 代码执行到这里时，会等待 FastAPI 处理请求
    
    # 服务器关闭时执行的代码
    await application.stop()
    await application.shutdown()

# 将 FastAPI 应用与 lifespan 事件挂钩
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    """根路径，用于健康检查或欢迎信息"""
    return {"message": "Hello, I am a Telegram Bot running on FastAPI!"}

@app.post(WEBHOOK_URL_PATH)
async def telegram_webhook(request: Request):
    """
    接收 Telegram Webhook 更新的端点。
    `python-telegram-bot` 应用将会处理这些更新。
    """
    logger.info("接收到 Webhook 请求...")
    try:
        if application is None:
            logger.error("Telegram Application 实例尚未初始化。")
            return Response(status_code=500)
            
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"处理 Webhook 请求时发生错误: {e}")
        return Response(status_code=500)
