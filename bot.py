import logging
import re
import asyncio
import os
import json
from datetime import datetime, timedelta
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# 添加测试输出
print("🚀 机器人启动中...")
print("🐍 Python版本:", os.sys.version)

# 强制测试 - 如果这里出错，说明代码有问题
try:
    print("🔧 测试基本导入...")
    import sys
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print("✅ 基本导入测试通过")
except Exception as e:
    print(f"❌ 基本导入测试失败: {e}")
    sys.exit(1)

# 检查是否在Render环境中运行
IS_RENDER = os.environ.get('RENDER', False)
PORT = int(os.environ.get('PORT', 8080))

# 添加调试信息
print(f"🔍 调试信息:")
print(f"   IS_RENDER: {IS_RENDER}")
print(f"   PORT: {PORT}")
print(f"   BOT_TOKEN: {'已设置' if os.environ.get('BOT_TOKEN') else '未设置'}")
print(f"   RENDER_EXTERNAL_HOSTNAME: {os.environ.get('RENDER_EXTERNAL_HOSTNAME', '未设置')}")

# 如果在Render环境中，导入web相关模块
if IS_RENDER:
    try:
        print("🔄 尝试导入aiohttp...")
        from aiohttp import web
        WEB_AVAILABLE = True
        print("✅ aiohttp 导入成功，webhook模式可用")
        logging.info("✅ aiohttp 导入成功，webhook模式可用")
    except ImportError as e:
        WEB_AVAILABLE = False
        print(f"⚠️ aiohttp 导入失败: {e}，webhook模式已禁用")
        print("将使用polling模式运行")
        logging.warning(f"⚠️ aiohttp 导入失败: {e}，webhook模式已禁用")
        logging.warning("将使用polling模式运行")
else:
    WEB_AVAILABLE = False
    print("🌐 本地环境，使用polling模式")
    logging.info("🌐 本地环境，使用polling模式")

print("🔧 继续初始化...")

# 这些函数将在后面定义

# 1. 设置你的 Bot Token
# 注意：出于安全考虑，强烈建议将 Token 存储在环境变量中，而不是直接写在代码里。
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8142344692:AAHgq1MQjZ50K445Vh7WhWyopNVWiY1F4PI')

# 检查BOT_TOKEN是否设置
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logging.error("请设置BOT_TOKEN环境变量或在代码中设置正确的token！")
    if IS_RENDER:
        exit(1) 

# 2. 启用日志记录，方便调试
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 多机器人配置
BOT_CONFIGS = {
    'bot1': {
        'BOT_ID': 'bot1',
        'BOT_NAME': '趣体育机器人1',
        'CS_HANDLE': '@QTY01',
        'CUSTOMER_SERVICE_USERS': [5079390159],  # @QTY01 的真实用户ID
        'MK_URL': 'https://www.mk2144.com:9153/entry/register46620/?i_code=91262507',  # 机器人1的MK体育链接
        'WELCOME_IMAGE': None,  # 欢迎图片URL，如果不需要图片请设为None
        'REGISTER_IMAGE': None,  # 自助注册图片URL，如果不需要图片请设为None
    },
    'bot2': {
        'BOT_ID': 'bot2',
        'BOT_NAME': '趣体育机器人2',
        'CS_HANDLE': '@QTY15',
        'CUSTOMER_SERVICE_USERS': [7951964655],  # @QTY15 的真实用户ID
        'MK_URL': 'https://www.mk2144.com:9153/entry/register22993/?i_code=77201329',  # 机器人2的MK体育链接
        'WELCOME_IMAGE': None,  # 欢迎图片URL，如果不需要图片请设为None
        'REGISTER_IMAGE': None,  # 自助注册图片URL，如果不需要图片请设为None
    },
    'bot3': {
        'BOT_ID': 'bot3',
        'BOT_NAME': '趣体育机器人3',
        'CS_HANDLE': '@qty772',
        'CUSTOMER_SERVICE_USERS': [8075220391],  # @qty772 的真实用户ID
        'MK_URL': 'https://www.mk2144.com:9153/entry/register86237/?i_code=60150868',  # 机器人3的MK体育链接
        'WELCOME_IMAGE': None,  # 欢迎图片URL，如果不需要图片请设为None
        'REGISTER_IMAGE': None,  # 自助注册图片URL，如果不需要图片请设为None
    }
}

# 获取当前机器人配置
BOT_ID = os.environ.get('BOT_ID', 'bot1')
CURRENT_BOT_CONFIG = BOT_CONFIGS.get(BOT_ID, BOT_CONFIGS['bot1'])

# 定义游戏的 URL
GAME_URL_QU = "https://www.qu32.vip:30011/entry/register/?i_code=6944642"
GAME_URL_MK = CURRENT_BOT_CONFIG['MK_URL']  # 从当前机器人配置中获取MK体育链接

# 使用当前机器人配置
CS_HANDLE = CURRENT_BOT_CONFIG['CS_HANDLE']
CUSTOMER_SERVICE_USERS = CURRENT_BOT_CONFIG['CUSTOMER_SERVICE_USERS']

# 超级管理员配置（可以管理所有机器人）
SUPER_ADMIN_USERNAME = "wzm1984"  # 超级管理员用户名（不带@）
SUPER_ADMIN_ID = None  # 会在运行时自动识别并设置

# 用户名到用户ID的映射
USERNAME_TO_ID = {
    "QTY01": 5079390159,  # @QTY01 对应的用户ID
    "QTY15": 7951964655,  # @QTY15 对应的用户ID
    "qty772": 8075220391,  # @qty772 对应的用户ID
}

# 双向联系会话管理
user_customer_service_sessions = {}
message_mapping = {}

# 图片设置状态管理
user_image_setting_state = {}  # {user_id: {'type': 'WELCOME_IMAGE'/'REGISTER_IMAGE', 'bot_id': 'bot1/bot2/bot3'}}

# 广播状态管理
broadcast_state = {}  # {user_id: {'step': 'idle'/'editing_text'/'editing_photo'/'editing_buttons', 'text': None, 'photo_file_id': None, 'buttons': []}}

# 所有用户列表管理
all_users = set()  # 存储所有与机器人交互过的用户ID

# 会话超时设置
SESSION_TIMEOUT_SECONDS = 30  # 30秒无活动自动结束会话
session_timeout_task = None  # 会话超时检查任务

# 时区设置
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(pytz.UTC)
    beijing_time = utc_now.astimezone(BEIJING_TZ)
    return beijing_time

def check_and_set_super_admin(user):
    """检查并自动设置超级管理员"""
    global SUPER_ADMIN_ID
    if user and user.username:
        username = user.username.lower()
        if username == SUPER_ADMIN_USERNAME.lower() and SUPER_ADMIN_ID is None:
            SUPER_ADMIN_ID = user.id
            logger.info(f"✅ 自动识别超级管理员: @{user.username} (ID: {user.id})")
            return True
    return False

def is_super_admin(user_id):
    """检查用户是否是超级管理员"""
    return SUPER_ADMIN_ID is not None and user_id == SUPER_ADMIN_ID

def can_manage_images(user_id):
    """检查用户是否有权限管理图片"""
    return is_super_admin(user_id) or user_id in CUSTOMER_SERVICE_USERS

def can_broadcast(user_id):
    """检查用户是否有权限发送广播"""
    return is_super_admin(user_id) or user_id in CUSTOMER_SERVICE_USERS

# 图片配置文件路径
IMAGE_CONFIG_FILE = 'bot_images_config.json'

def load_image_config():
    """从文件加载图片配置"""
    try:
        if os.path.exists(IMAGE_CONFIG_FILE):
            with open(IMAGE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 更新到 BOT_CONFIGS
                for bot_id, bot_config in BOT_CONFIGS.items():
                    if bot_id in config:
                        if 'WELCOME_IMAGE' in config[bot_id]:
                            bot_config['WELCOME_IMAGE'] = config[bot_id]['WELCOME_IMAGE']
                        if 'REGISTER_IMAGE' in config[bot_id]:
                            bot_config['REGISTER_IMAGE'] = config[bot_id]['REGISTER_IMAGE']
                logger.info("图片配置加载成功")
    except Exception as e:
        logger.error(f"加载图片配置失败: {e}")

def save_image_config(bot_id, image_type, file_id):
    """保存图片配置到文件"""
    try:
        # 读取现有配置
        config = {}
        if os.path.exists(IMAGE_CONFIG_FILE):
            with open(IMAGE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 更新配置
        if bot_id not in config:
            config[bot_id] = {}
        config[bot_id][image_type] = file_id
        
        # 保存到文件
        with open(IMAGE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 同时更新内存中的配置
        if bot_id in BOT_CONFIGS:
            BOT_CONFIGS[bot_id][image_type] = file_id
        
        logger.info(f"图片配置已保存: {bot_id} - {image_type}")
        return True
    except Exception as e:
        logger.error(f"保存图片配置失败: {e}")
        return False

# 启动时加载图片配置
load_image_config()

# 定义按钮的表情符号
BUTTON_EMOJIS = {
    'menu_account_info': '🏠',
    'menu_play_game': '▶️',
    'menu_advertising_channel': '📣',
    'menu_promotion_channel': '📢',
    'menu_invite_friend': '🎁',
    'menu_customer_service': '👥',
    'menu_download_app': '📱',
    'menu_change_lang': '🌐',
    'menu_self_register': '📝',  # 新增自助注册的表情
    'menu_mainland_user': '🇨🇳',  # 新增大陆用户的表情
    'menu_overseas_user': '🌍',  # 新增海外用户的表情
    'menu_bidirectional_contact': '💬',  # 双向联系的表情
}

# 3. 准备多语言文本
LANGUAGES = {
    'zh-CN': {
        'welcome': "欢迎来到 qu体育 {user}，点击下方菜单开始互动。", # 此处已不再使用，但保留作为其他语言的模板
        'main_menu_prompt': "请从主菜单中选择一个选项。",
        'menu_account_info': "注册账号",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}进入游戏",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}趣体育官方招商",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}2026世界杯🏆足球篮球推单五大联赛",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}邀请好友",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}人工客服",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}下载APP",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}LANGUAGE", 
        'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}自助注册", # 新增
        'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}大陆用户", # 新增
        'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}海外用户", # 新增
        'live_customer_service_title': "请点击以下客服专员联系：",
        'customer_specialist_1': "官方客服 @QTY01",
        'download_app_info': "点击下方按钮下载应用程序：",
        'download_android': "安卓下载",
        'download_ios': "苹果下载",
        'invite_title': "❤️邀请好友注册赚取奖金",
        'invite_message': "👉邀请您的好友，联系客服专员获取您的奖金!",
        'invite_link_heading': "邀请链接 🔗",
        'invite_link_qu': "趣体育（大陆用户）\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
        'invite_link_mk': f"MK体育（全球用户）\n{GAME_URL_MK}",
        'language_selection': "请选择您的语言：",
        'lang_changed': "语言已成功切换！",
        'welcome_to_sports': "欢迎来到 qu体育！",
        'official_group_handle': "官方群组： @quyuyule",
        'official_channel_handle': "官方频道： @qu337",
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
        'register_info_notice_prompt': "请点击下方按钮前往注册：", # 新增
                 'register_info_download_notice': """
📝 <b>注册注意事项</b>
1️⃣ <b>请勿直接下载APP</b>
‼️<b>★ 重要提醒 ★</b>‼️ 请先完成账号注册 → 由专员登记福利 → 再下载APP

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
        'welcome_visitor': "🎉 欢迎您！您是第 {count} 位访客",
        'activity_title': "限时免费赠送活动（30天）",
        'activity_benefits': "🎁 活动福利",
        'activity_description': "注册并充值成功，即获赠老湿永久VIP会员！",
        'benefit_1': "✅ 包含18个SVIP频道",
        'benefit_2': "✅ 超百万部精品视频",
        'benefit_3': "💰 价值 368 元 VIP 会员",
        'claim_method': "💬 领取方式",
        'claim_description': "注册充值成功后，请立即联系人工客服领取您的专属福利。",
        'investment_channel': "📢 趣体育官方招商",
        'investment_link': "👉 https://t.me/QTY18",
        'promotion_channel': "📢 2026世界杯🏆足球篮球推单五大联赛",
        'promotion_link': "👉 https://t.me/SJB33",
        'customer_service_title': "💬 官方客服",
        'registration_prompt_title': "🌍 注册提示",
        'mainland_user_prompt': "🇨🇳 大陆用户请点击大陆用户按钮注册",
        'overseas_user_prompt': "🌍 海外用户请点击海外按钮注册",
        'vip_member_title': "✨ 官方联盟老湿VIP会员 ✨",
        'menu_bidirectional_contact': f"{BUTTON_EMOJIS['menu_bidirectional_contact']}双向联系",
        'start_cs_session': "✅ 客服会话已启动\n\n现在您可以发送消息，我会转发给客服。\n发送 /endcs 结束会话。",
        'end_cs_session': "✅ 客服会话已结束",
        'cs_session_timeout': "⏰ 客服会话已因超时自动结束（30秒无活动）。\n如需继续联系客服，请重新发起会话。",
        'cs_message_sent': "✅ 消息已转发给客服，请等待回复",
        'cs_reply_received': "💬 客服回复\n客服: {cs_handle}\n时间: {time}\n\n{message}",
        'new_cs_session_notification': "🆕 新的客服会话\n用户: {user_name} (ID: {user_id})\n时间: {time}",
        'cs_session_ended_notification': "🔚 客服会话结束\n用户: {user_name} (ID: {user_id})\n时间: {time}",
        'get_user_id_info': "📋 用户信息\n用户ID: {user_id}\n用户名: @{username}\n姓名: {first_name}\n\n请将用户ID发送给管理员配置到机器人中。",
    },
         'en': {
         'welcome': "Welcome to quSports {user}, click on the menu below to interact.",
         'main_menu_prompt': "Please select an option from the main menu.",
         'menu_account_info': "Register Account",
         'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}Play Game",
         'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}QTY Official Investment",
         'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}2026 World Cup🏆Football Basketball Picks Five Major Leagues",
         'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}Invite Friends",
         'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}Customer Service",
         'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}Download APP",
         'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}LANGUAGE",
         'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}Self-Registration", # New
         'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}Mainland User", # New
         'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}Overseas User", # New
         'live_customer_service_title': "Please click on a customer service specialist to contact:",
         'customer_specialist_1': "Official Customer Service @QTY01",
         'download_app_info': "Click the buttons below to download the app:",
         'download_android': "Android Download",
         'download_ios': "iOS Download",
         'invite_title': "Invite friends and earn money together!",
         'invite_message': "By inviting friends to register through your exclusive link, you can get rich rewards!",
         'invite_link_heading': "Your invitation link  ",
         'invite_link_qu': "quSports (Mainland China Users)\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
         'invite_link_mk': f"MK Sports (Global Users)\n{GAME_URL_MK}",
         'language_selection': "Please select your language:",
         'lang_changed': "Language switched successfully!",
         'welcome_to_sports': "Welcome to quSports!",
         'official_group_handle': "Official Group: @quyuyule",
         'official_channel_handle': "Official Channel: @qu337",
         'customer_service_handle': "Official Customer Service: @QTY01",
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
         'register_info_notice_prompt': "Please click the button below to register:", # 新增
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
         'welcome_visitor': "🎉 Welcome! You are the {count}th visitor",
         'activity_title': "Limited Time Free Gift Event (30 days)",
         'activity_benefits': "🎁 Event Benefits",
         'activity_description': "Register and recharge successfully to receive permanent VIP membership!",
         'benefit_1': "✅ Includes 15 SVIP channels",
         'benefit_2': "✅ Over 1 million premium videos",
         'benefit_3': "💰 Worth 368 yuan VIP membership",
         'claim_method': "💬 How to claim",
         'claim_description': "After successful registration and recharge, please contact customer service immediately to claim your exclusive benefits.",
         'investment_channel': "📢 QTY Official Investment",
         'investment_link': "👉 https://t.me/QTY18",
         'promotion_channel': "📢 2026 World Cup🏆Football Basketball Picks Five Major Leagues",
         'promotion_link': "👉 https://t.me/SJB33",
         'customer_service_title': "💬 Official Customer Service",
         'registration_prompt_title': "🌍 Registration Notice",
         'mainland_user_prompt': "🇨🇳 Mainland users please click the Mainland User button to register",
         'overseas_user_prompt': "🌍 Overseas users please click the Overseas User button to register",
         'vip_member_title': "✨ Official Alliance VIP Membership ✨",
         'menu_bidirectional_contact': f"{BUTTON_EMOJIS['menu_bidirectional_contact']}Bidirectional Contact",
         'start_cs_session': "✅ Customer service session started\n\nYou can now send messages, I will forward them to customer service.\nSend /endcs to end the session.",
         'end_cs_session': "✅ Customer service session ended",
         'cs_session_timeout': "⏰ Customer service session automatically ended due to timeout (30 seconds of inactivity).\nPlease start a new session if you need to contact customer service again.",
         'cs_message_sent': "✅ Message forwarded to customer service, please wait for reply",
         'cs_reply_received': "💬 Customer Service Reply\nService: {cs_handle}\nTime: {time}\n\n{message}",
         'new_cs_session_notification': "🆕 New customer service session\nUser: {user_name} (ID: {user_id})\nTime: {time}",
         'cs_session_ended_notification': "🔚 Customer service session ended\nUser: {user_name} (ID: {user_id})\nTime: {time}",
         'get_user_id_info': "📋 User Information\nUser ID: {user_id}\nUsername: @{username}\nName: {first_name}\n\nPlease send the User ID to the administrator to configure in the bot.",
     },
         'th': {
         'welcome': "ยินดีต้อนรับสู่ quSports {user} คลิกที่เมนูด้านล่างเพื่อโต้ตอบ",
         'main_menu_prompt': "กรุณาเลือกตัวเลือกจากเมนูหลัก",
         'menu_account_info': "ลงทะเบียนบัญชี",
         'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}เข้าสู่เกม",
         'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}QTY ช่องทางการลงทุนอย่างเป็นทางการ",
         'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}ฟุตบอลบาสเกตบอล 2026 ฟุตบอลโลก🏆เลือกห้าลีกใหญ่",
         'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}เชิญเพื่อน",
         'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}บริการลูกค้า",
         'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}ดาวน์โหลดแอป",
         'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}ภาษา", 
         'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}ลงทะเบียนด้วยตนเอง", # New
         'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}ผู้ใช้ในจีนแผ่นดินใหญ่", # New
         'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}ผู้ใช้ทั่วโลก", # New
         'live_customer_service_title': "กรุณาคลิกที่ผู้เชี่ยวชาญบริการลูกค้าด้านล่างเพื่อติดต่อ:",
         'customer_specialist_1': "บริการลูกค้าอย่างเป็นทางการ @QTY01",
         'download_app_info': "คลิกปุ่มด้านล่างเพื่อดาวน์โหลดแอป:",
         'download_android': "ดาวน์โหลด Android",
         'download_ios': "ดาวน์โหลด iOS",
         'invite_title': "เชิญเพื่อนและรับเงินด้วยกัน!",
         'invite_message': "โดยการเชิญเพื่อนให้ลงทะเบียนผ่านลิงก์พิเศษของคุณ คุณจะได้รับรางวัลมากมาย!",
         'invite_link_heading': "ลิงก์เชิญ 🔗",
         'invite_link_qu': "quSports (ผู้ใช้ในจีน)\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
         'invite_link_mk': f"MK Sports (ผู้ใช้ทั่วโลก)\n{GAME_URL_MK}",
         'language_selection': "กรุณาเลือกภาษาของคุณ:",
         'lang_changed': "เปลี่ยนภาษาเรียบร้อยแล้ว!",
         'welcome_to_sports': "ยินดีต้อนรับสู่ quSports!",
         'official_group_handle': "กลุ่มทางการ: @quyuyule",
         'official_channel_handle': "ช่องทางการ: @qu337",
         'customer_service_handle': "บริการลูกค้าทางการ: @QTY01",
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
         'register_info_notice_prompt': "กรุณาคลิกปุ่มด้านล่างเพื่อลงทะเบียน:", # 新增
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
         'welcome_visitor': "🎉 ยินดีต้อนรับ! คุณเป็นผู้เยี่ยมชมคนที่ {count}",
         'activity_title': "กิจกรรมแจกฟรีเป็นเวลาจำกัด (30 วัน)",
         'activity_benefits': "🎁 สิทธิประโยชน์กิจกรรม",
         'activity_description': "ลงทะเบียนและเติมเงินสำเร็จ รับสมาชิก VIP ถาวรทันที!",
         'benefit_1': "✅ รวม 15 ช่อง SVIP",
         'benefit_2': "✅ วิดีโอคุณภาพสูงกว่า 1 ล้านเรื่อง",
         'benefit_3': "💰 สมาชิก VIP มูลค่า 368 หยวน",
         'claim_method': "💬 วิธีรับสิทธิประโยชน์",
         'claim_description': "หลังจากลงทะเบียนและเติมเงินสำเร็จ โปรดติดต่อบริการลูกค้าทันทีเพื่อรับสิทธิประโยชน์พิเศษของคุณ",
         'investment_channel': "📢 QTY ช่องทางการลงทุนอย่างเป็นทางการ",
         'investment_link': "👉 https://t.me/QTY18",
         'promotion_channel': "📢 ฟุตบอลบาสเกตบอล 2026 ฟุตบอลโลก🏆เลือกห้าลีกใหญ่",
         'promotion_link': "👉 https://t.me/SJB33",
         'customer_service_title': "💬 บริการลูกค้าอย่างเป็นทางการ",
         'registration_prompt_title': "🌍 ข้อแนะนำการลงทะเบียน",
         'mainland_user_prompt': "🇨🇳 ผู้ใช้ในจีนแผ่นดินใหญ่กรุณาคลิกปุ่มผู้ใช้ในจีนแผ่นดินใหญ่เพื่อลงทะเบียน",
         'overseas_user_prompt': "🌍 ผู้ใช้ทั่วโลกกรุณาคลิกปุ่มผู้ใช้ทั่วโลกเพื่อลงทะเบียน",
         'vip_member_title': "✨ สมาชิก VIP พันธมิตรอย่างเป็นทางการ ✨",
         'menu_bidirectional_contact': f"{BUTTON_EMOJIS['menu_bidirectional_contact']}ติดต่อสองทาง",
         'start_cs_session': "✅ เซสชันบริการลูกค้าเริ่มแล้ว\n\nตอนนี้คุณสามารถส่งข้อความได้ ฉันจะส่งต่อให้กับบริการลูกค้า\nส่ง /endcs เพื่อจบเซสชัน",
         'end_cs_session': "✅ เซสชันบริการลูกค้าจบแล้ว",
         'cs_session_timeout': "⏰ เซสชันบริการลูกค้าจบอัตโนมัติเนื่องจากหมดเวลา (30 วินาทีไม่มีกิจกรรม)\nกรุณาเริ่มเซสชันใหม่หากต้องการติดต่อบริการลูกค้าอีกครั้ง",
         'cs_message_sent': "✅ ส่งข้อความไปยังบริการลูกค้าแล้ว กรุณารอการตอบกลับ",
         'cs_reply_received': "💬 คำตอบจากบริการลูกค้า\nบริการ: {cs_handle}\nเวลา: {time}\n\n{message}",
         'new_cs_session_notification': "🆕 เซสชันบริการลูกค้าใหม่\nผู้ใช้: {user_name} (ID: {user_id})\nเวลา: {time}",
         'cs_session_ended_notification': "🔚 เซสชันบริการลูกค้าจบแล้ว\nผู้ใช้: {user_name} (ID: {user_id})\nเวลา: {time}",
         'get_user_id_info': "📋 ข้อมูลผู้ใช้\nID ผู้ใช้: {user_id}\nชื่อผู้ใช้: @{username}\nชื่อ: {first_name}\n\nกรุณาส่ง ID ผู้ใช้ให้ผู้ดูแลระบบเพื่อกำหนดค่าในบอท",
     },
    'vi': {
        'welcome': "Chào mừng đến với quSports {user}, nhấp vào menu bên dưới để tương tác.",
        'main_menu_prompt': "Vui lòng chọn một tùy chọn từ menu chính.",
        'menu_account_info': "Đăng ký tài khoản",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}Vào trò chơi",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}QTY Kênh đầu tư chính thức",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}Bóng đá Bóng rổ 2026 World Cup🏆Chọn năm giải đấu lớn",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}Mời bạn bè",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}Dịch vụ khách hàng",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}Tải ứng dụng",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}NGÔN NGỮ",
        'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}Tự đăng ký", # New
        'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}Người dùng Trung Quốc đại lục", # New
        'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}Người dùng toàn cầu", # New
        'live_customer_service_title': "Vui lòng nhấp vào chuyên viên dịch vụ khách hàng dưới đây để liên hệ:",
        'customer_specialist_1': "Dịch vụ khách hàng chính thức @QTY01",
        'download_app_info': "Nhấp vào các nút dưới đây để tải ứng dụng:",
        'download_android': "Tải Android",
        'download_ios': "Tải iOS",
        'invite_title': "Mời bạn bè và kiếm tiền cùng nhau!",
        'invite_message': "Bằng cách mời bạn bè đăng ký thông qua liên kết độc quyền của bạn, bạn có thể nhận được phần thưởng phong phú!",
        'invite_link_heading': "Liên kết mời ",
        'invite_link_qu': "quSports (người dùng Trung Quốc)\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
        'invite_link_mk': f"MK Sports (người dùng toàn cầu)\n{GAME_URL_MK}",
        'language_selection': "Vui lòng chọn ngôn ngữ của bạn:",
        'lang_changed': "Đã thay đổi ngôn ngữ thành công!",
        'welcome_to_sports': "Chào mừng đến với quSports!",
        'official_group_handle': "Nhóm chính thức: @quyuyule",
        'official_channel_handle': "Kênh chính thức: @qu337",
        'customer_service_handle': "Dịch vụ khách hàng chính thức: @QTY01",
        'account_info_title': "Tài khoản của tôi",
        'member_id': "ID thành viên: {user_id}",
        'member_account': "Tài khoản thành viên: {username}",
        'balance': "Số dư tài khoản: {balance:.2f}CNY",
        'vip_level': "Cấp độ VIP: VIP{vip}",
        'advertising_channel_prompt': "Nhấp vào nút dưới đây để vào kênh quảng cáo:",
        'promotion_channel_prompt': "Nhấp vào nút dưới đây để vào kênh khuyến mãi:",
        'play_game_choice_prompt': "Vui lòng chọn trò chơi bạn muốn vào:",
        'register_info_title': "Chào mừng đến với quSports⚽️MKsports",
        'register_info_channel1': "Kênh quảng cáo",
        'register_info_channel2': "Kênh khuyến mãi",
        'register_info_cs1': "Dịch vụ khách hàng 1",
        'register_info_cs2': "Dịch vụ khách hàng 2",
        'register_info_cs3': "Dịch vụ khách hàng 3",
        'register_info_qu_link_text': "quSports (người dùng Trung Quốc)",
        'register_info_mk_link_text': "MK Sports (người dùng toàn cầu)",
        'register_info_notice_prompt': "Vui lòng nhấp vào nút dưới đây để đăng ký:", # 新增
        'register_info_download_notice': """
        📝 <b>Lưu ý khi đăng ký</b>
        1️⃣ <b>Không được tải ứng dụng trực tiếp</b>
        ‼<b>★ Lưu ý quan trọng ★</b>‼ Vui lòng hoàn thành đăng ký tài khoản trước → Đăng ký nhận ưu đãi với chuyên viên → Sau đó mới tải ứng dụng

        2️⃣ <b>Đăng ký yêu cầu thông tin tên thật</b>
        Chúng tôi là nền tảng hợp pháp. Để đảm bảo việc rút tiền diễn ra suôn sẻ, vui lòng sử dụng tên thật khi đăng ký.

        3️⃣ <b>Số điện thoại và tên thật phải khớp nhau</b>
        Số điện thoại đăng ký phải khớp với thông tin tên thật.

        4️⃣ <b>Không thể mở ứng dụng Android</b>
        Nếu gặp sự cố, vui lòng liên hệ với chuyên viên để được hỗ trợ.
        """,
        'download_app_qu_title': "quSports",
        'download_app_mk_title': "MK Sports",
        'game_qu_name': "quSports",
        'game_mk_name': "MK Sports",
        'welcome_visitor': "🎉 Chào mừng! Bạn là khách thăm thứ {count}",
        'activity_title': "Sự kiện tặng miễn phí có thời hạn (30 ngày)",
        'activity_benefits': "🎁 Lợi ích sự kiện",
        'activity_description': "Đăng ký và nạp tiền thành công, nhận ngay thành viên VIP vĩnh viễn!",
        'benefit_1': "✅ Bao gồm 15 kênh SVIP",
        'benefit_2': "✅ Hơn 1 triệu video chất lượng cao",
        'benefit_3': "💰 Thành viên VIP trị giá 368 nhân dân tệ",
        'claim_method': "💬 Cách nhận",
        'claim_description': "Sau khi đăng ký và nạp tiền thành công, vui lòng liên hệ ngay với dịch vụ khách hàng để nhận lợi ích độc quyền của bạn.",
        'investment_channel': "📢 QTY Kênh đầu tư chính thức",
        'investment_link': "👉 https://t.me/QTY18",
        'promotion_channel': "📢 Bóng đá Bóng rổ 2026 World Cup🏆Chọn năm giải đấu lớn",
        'promotion_link': "👉 https://t.me/SJB33",
        'customer_service_title': "💬 Dịch vụ khách hàng chính thức",
        'registration_prompt_title': "🌍 Hướng dẫn đăng ký",
        'mainland_user_prompt': "🇨🇳 Người dùng Trung Quốc đại lục vui lòng nhấp vào nút Người dùng Trung Quốc đại lục để đăng ký",
        'overseas_user_prompt': "🌍 Người dùng toàn cầu vui lòng nhấp vào nút Người dùng toàn cầu để đăng ký",
        'vip_member_title': "✨ Thành viên VIP liên minh chính thức ✨",
        'menu_bidirectional_contact': f"{BUTTON_EMOJIS['menu_bidirectional_contact']}Liên hệ hai chiều",
        'start_cs_session': "✅ Phiên dịch vụ khách hàng đã bắt đầu\n\nBây giờ bạn có thể gửi tin nhắn, tôi sẽ chuyển tiếp cho dịch vụ khách hàng.\nGửi /endcs để kết thúc phiên.",
        'end_cs_session': "✅ Phiên dịch vụ khách hàng đã kết thúc",
        'cs_session_timeout': "⏰ Phiên dịch vụ khách hàng tự động kết thúc do hết thời gian (30 giây không hoạt động).\nVui lòng bắt đầu phiên mới nếu bạn cần liên hệ dịch vụ khách hàng lại.",
        'cs_message_sent': "✅ Tin nhắn đã được chuyển tiếp cho dịch vụ khách hàng, vui lòng chờ phản hồi",
        'cs_reply_received': "💬 Phản hồi từ dịch vụ khách hàng\nDịch vụ: {cs_handle}\nThời gian: {time}\n\n{message}",
        'new_cs_session_notification': "🆕 Phiên dịch vụ khách hàng mới\nNgười dùng: {user_name} (ID: {user_id})\nThời gian: {time}",
        'cs_session_ended_notification': "🔚 Phiên dịch vụ khách hàng đã kết thúc\nNgười dùng: {user_name} (ID: {user_id})\nThời gian: {time}",
        'get_user_id_info': "📋 Thông tin người dùng\nID người dùng: {user_id}\nTên người dùng: @{username}\nTên: {first_name}\n\nVui lòng gửi ID người dùng cho quản trị viên để cấu hình trong bot.",
    }
}

# 4. 建立一个字典来存储用户语言设置（这只是一个简单的示例，实际应用中应使用数据库）
user_data = {}

# Firebase配置
FIREBASE_CONFIG = {
    'type': os.environ.get('FIREBASE_TYPE', 'service_account'),
    'project_id': os.environ.get('FIREBASE_PROJECT_ID', ''),
    'private_key_id': os.environ.get('FIREBASE_PRIVATE_KEY_ID', ''),
    'private_key': os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
    'client_email': os.environ.get('FIREBASE_CLIENT_EMAIL', ''),
    'client_id': os.environ.get('FIREBASE_CLIENT_ID', ''),
    'auth_uri': os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
    'token_uri': os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
    'auth_provider_x509_cert_url': os.environ.get('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
    'client_x509_cert_url': os.environ.get('FIREBASE_CLIENT_X509_CERT_URL', '')
}

# 机器人标识符 - 用于区分不同机器人的数据
BOT_ID = os.environ.get('BOT_ID', 'hybot')  # 默认标识符

# 访客统计相关变量
visitor_stats = {
    'total_visitors': 0,
    'daily_stats': {},
    'unique_visitors': set()
}

# Firebase初始化标志
firebase_initialized = False
firebase_db = None

# 心跳激活相关变量
last_activity_time = get_beijing_time()
is_heartbeat_active = False
heartbeat_monitor_task = None
last_heartbeat_time = get_beijing_time()

# 检查是否在Render环境中运行
IS_RENDER = os.environ.get('RENDER', False)

# 5. 根据用户的语言获取文本
def get_text(user_id, key):
    """根据用户的语言设置获取相应的文本"""
    lang_code = user_data.get(user_id, 'zh-CN')
    return LANGUAGES.get(lang_code, LANGUAGES['zh-CN']).get(key, key)

def initialize_firebase():
    """初始化Firebase连接"""
    global firebase_initialized, firebase_db
    
    try:
        # 检查Firebase配置是否完整
        if not all([FIREBASE_CONFIG['project_id'], FIREBASE_CONFIG['private_key'], FIREBASE_CONFIG['client_email']]):
            logger.warning("Firebase配置不完整，将使用本地存储")
            return False
        
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # 创建Firebase凭证
        cred = credentials.Certificate(FIREBASE_CONFIG)
        
        # 初始化Firebase应用
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        # 获取Firestore数据库实例
        firebase_db = firestore.client()
        firebase_initialized = True
        
        logger.info("✅ Firebase初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ Firebase初始化失败: {e}")
        firebase_initialized = False
        return False

def update_activity():
    """更新最后活动时间"""
    global last_activity_time
    last_activity_time = get_beijing_time()
    logger.info(f"活动更新: {last_activity_time}")

def update_visitor_stats(user_id):
    """更新访客统计（增强日志版）"""
    global visitor_stats, all_users
    
    today = get_beijing_time().strftime('%Y-%m-%d')
    
    # 详细记录更新过程
    logger.info(f"🔄 开始更新访客统计: 用户 {user_id}, 日期 {today}")
    print(f"🔄 开始更新访客统计: 用户 {user_id}, 日期 {today}")
    logger.info(f"📊 更新前状态: 总访客={visitor_stats['total_visitors']}, 今日访客={len(visitor_stats['daily_stats'].get(today, {}).get('visitors', set()))}")
    
    # 更新本地统计
    if user_id not in visitor_stats['unique_visitors']:
        visitor_stats['unique_visitors'].add(user_id)
        visitor_stats['total_visitors'] += 1
        logger.info(f"✅ 新增唯一访客: {user_id}, 总访客数: {visitor_stats['total_visitors']}")
        print(f"✅ 新增唯一访客: {user_id}, 总访客数: {visitor_stats['total_visitors']}")
    
    # 添加到所有用户列表
    all_users.add(user_id)
    
    # 更新每日统计
    if today not in visitor_stats['daily_stats']:
        visitor_stats['daily_stats'][today] = {
            'visitors': set(),
            'total_actions': 0
        }
        logger.info(f"📅 创建新日期记录: {today}")
        print(f"📅 创建新日期记录: {today}")
    
    # 记录今日访客
    visitor_stats['daily_stats'][today]['visitors'].add(user_id)
    visitor_stats['daily_stats'][today]['total_actions'] += 1
    logger.info(f"📈 今日统计更新: 访客={len(visitor_stats['daily_stats'][today]['visitors'])}, 操作={visitor_stats['daily_stats'][today]['total_actions']}")
    print(f"📈 今日统计更新: 访客={len(visitor_stats['daily_stats'][today]['visitors'])}, 操作={visitor_stats['daily_stats'][today]['total_actions']}")
    
    # 异步更新Firebase
    if firebase_initialized and firebase_db:
        logger.info(f"🌐 准备更新Firebase: 机器人ID={BOT_ID}")
        print(f"🌐 准备更新Firebase: 机器人ID={BOT_ID}")
        try:
            asyncio.create_task(_async_update_firebase(user_id, today))
            logger.info(f"✅ Firebase异步任务已创建")
            print(f"✅ Firebase异步任务已创建")
        except Exception as e:
            logger.error(f"❌ 创建Firebase异步任务失败: {e}")
            print(f"❌ 创建Firebase异步任务失败: {e}")
    else:
        logger.warning(f"⚠️ Firebase未初始化或不可用: initialized={firebase_initialized}, db={firebase_db is not None}")
        print(f"⚠️ Firebase未初始化或不可用: initialized={firebase_initialized}, db={firebase_db is not None}")
    
    logger.info(f"✅ 访客统计更新完成: 用户 {user_id}, 日期 {today}")
    print(f"✅ 访客统计更新完成: 用户 {user_id}, 日期 {today}")

async def _async_update_firebase(user_id, today):
    """异步更新Firebase数据（增强日志版）"""
    try:
        logger.info(f"🌐 开始Firebase异步更新: 用户 {user_id}, 日期 {today}")
        print(f"🌐 开始Firebase异步更新: 用户 {user_id}, 日期 {today}")
        
        # 更新总访客数
        stats_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('visitor_stats')
        await asyncio.get_event_loop().run_in_executor(None, lambda: stats_ref.set({
            'total_visitors': visitor_stats['total_visitors'],
            'last_updated': get_beijing_time(),
            'bot_id': BOT_ID,
            'bot_name': '会员机器人'
        }, merge=True))
        
        logger.info(f"✅ 总访客数更新成功: {visitor_stats['total_visitors']}")
        print(f"✅ 总访客数更新成功: {visitor_stats['total_visitors']}")
        
        # 更新每日统计
        daily_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('daily_stats').collection('dates').document(today)
        await asyncio.get_event_loop().run_in_executor(None, lambda: daily_ref.set({
            'visitors': list(visitor_stats['daily_stats'][today]['visitors']),
            'total_actions': visitor_stats['daily_stats'][today]['total_actions'],
            'last_updated': get_beijing_time(),
            'bot_id': BOT_ID
        }, merge=True))
        
        logger.info(f"✅ 每日统计更新成功: 访客={len(visitor_stats['daily_stats'][today]['visitors'])}, 操作={visitor_stats['daily_stats'][today]['total_actions']}")
        print(f"✅ 每日统计更新成功: 访客={len(visitor_stats['daily_stats'][today]['visitors'])}, 操作={visitor_stats['daily_stats'][today]['total_actions']}")
        
        logger.info(f"✅ Firebase异步更新完成: 用户 {user_id}, 日期 {today}")
        print(f"✅ Firebase异步更新完成: 用户 {user_id}, 日期 {today}")
        
    except Exception as e:
        error_msg = f"❌ Firebase异步更新失败: 用户 {user_id}, 日期 {today}, 错误: {e}"
        logger.error(error_msg)
        print(error_msg)

async def get_all_user_ids():
    """获取所有用户ID列表"""
    global all_users
    
    # 优先从内存获取
    if all_users:
        logger.info(f"📋 从内存获取用户列表: {len(all_users)} 个用户")
        return list(all_users)
    
    # 如果内存为空,从Firebase恢复
    if firebase_initialized and firebase_db:
        try:
            logger.info("🔄 内存用户列表为空,从Firebase恢复...")
            
            # 从Firebase获取所有日期的访客数据
            all_firebase_users = set()
            
            # 获取最近90天的数据
            for i in range(90):
                date = (get_beijing_time() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('daily_stats').collection('dates').document(date)
                daily_doc = daily_ref.get()
                
                if daily_doc.exists:
                    daily_data = daily_doc.to_dict()
                    visitors_list = daily_data.get('visitors', [])
                    all_firebase_users.update(visitors_list)
            
            # 更新本地用户列表
            all_users.update(all_firebase_users)
            
            logger.info(f"✅ 从Firebase恢复用户列表: {len(all_users)} 个用户")
            return list(all_users)
            
        except Exception as e:
            logger.error(f"❌ 从Firebase恢复用户列表失败: {e}")
            return []
    else:
        logger.warning("⚠️ Firebase不可用,无法恢复用户列表")
        return []

def get_visitor_stats():
    """获取访客统计信息（增强版）"""
    global visitor_stats
    
    today = get_beijing_time().strftime('%Y-%m-%d')
    
    # 如果本地数据为空，强制恢复
    if visitor_stats['total_visitors'] == 0:
        logger.warning("⚠️ 本地统计数据为空，尝试恢复...")
        print("⚠️ 本地统计数据为空，尝试恢复...")
        
        # 同步恢复数据
        if firebase_initialized and firebase_db:
            try:
                # 先恢复最近7天的数据，收集所有唯一访客
                all_unique_visitors = set()
                
                for i in range(7):
                    date = (get_beijing_time() - timedelta(days=i)).strftime('%Y-%m-%d')
                    daily_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('daily_stats').collection('dates').document(date)
                    daily_doc = daily_ref.get()
                    
                    if daily_doc.exists:
                        daily_data = daily_doc.to_dict()
                        visitors_list = daily_data.get('visitors', [])
                        total_actions = daily_data.get('total_actions', 0)
                        
                        visitors_set = set(visitors_list)
                        visitor_stats['daily_stats'][date] = {
                            'visitors': visitors_set,
                            'total_actions': total_actions
                        }
                        
                        # 收集所有唯一访客
                        all_unique_visitors.update(visitors_set)
                        
                        logger.info(f"✅ 同步恢复日期 {date}: {len(visitors_set)} 访客, {total_actions} 操作")
                        print(f"✅ 同步恢复日期 {date}: {len(visitors_set)} 访客, {total_actions} 操作")
                
                # 更新唯一访客集合和总访客数
                visitor_stats['unique_visitors'].update(all_unique_visitors)
                visitor_stats['total_visitors'] = len(visitor_stats['unique_visitors'])
                
                # 恢复总访客数（如果Firebase中有记录，使用较大的值）
                stats_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('visitor_stats')
                stats_doc = stats_ref.get()
                
                if stats_doc.exists:
                    stats_data = stats_doc.to_dict()
                    firebase_total = stats_data.get('total_visitors', 0)
                    
                    # 使用较大的值，确保数据完整性
                    if firebase_total > visitor_stats['total_visitors']:
                        visitor_stats['total_visitors'] = firebase_total
                        logger.info(f"✅ 使用Firebase记录的总访客数: {visitor_stats['total_visitors']}")
                        print(f"✅ 使用Firebase记录的总访客数: {visitor_stats['total_visitors']}")
                    else:
                        logger.info(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
                        print(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
                else:
                    logger.info(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
                    print(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
                    
            except Exception as e:
                logger.error(f"❌ 同步数据恢复失败: {e}")
                print(f"❌ 同步数据恢复失败: {e}")
    
    # 获取今日统计
    today_stats = visitor_stats['daily_stats'].get(today, {'visitors': set(), 'total_actions': 0})
    today_visitors = len(today_stats['visitors'])
    today_actions = today_stats['total_actions']
    
    # 获取最近7天统计
    recent_stats = {}
    for i in range(7):
        date = (get_beijing_time() - timedelta(days=i)).strftime('%Y-%m-%d')
        if date in visitor_stats['daily_stats']:
            recent_stats[date] = {
                'visitors': len(visitor_stats['daily_stats'][date]['visitors']),
                'actions': visitor_stats['daily_stats'][date]['total_actions']
            }
    
    result = {
        'total_visitors': visitor_stats['total_visitors'],
        'today_visitors': today_visitors,
        'today_actions': today_actions,
        'recent_stats': recent_stats
    }
    
    logger.info(f"📊 获取统计结果: {result}")
    return result
    
    # 获取今日统计
    today_stats = visitor_stats['daily_stats'].get(today, {'visitors': set(), 'total_actions': 0})
    today_visitors = len(today_stats['visitors'])
    today_actions = today_stats['total_actions']
    
    # 获取最近7天统计
    recent_stats = {}
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        if date in visitor_stats['daily_stats']:
            recent_stats[date] = {
                'visitors': len(visitor_stats['daily_stats'][date]['visitors']),
                'actions': visitor_stats['daily_stats'][date]['total_actions']
            }
    
    return {
        'total_visitors': visitor_stats['total_visitors'],
        'today_visitors': today_visitors,
        'today_actions': today_actions,
        'recent_stats': recent_stats
    }

# 健康检查端点
async def health_check(request):
    """健康检查端点，用于Render平台监控"""
    update_activity()
    return web.Response(text="OK", status=200)

# Webhook处理函数
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

async def heartbeat_task(application: Application):
    """心跳任务，每10分钟发送一次心跳信号（增强版+自动恢复）"""
    global is_heartbeat_active
    
    logger.info("💓 心跳任务开始运行")
    print("💓 心跳任务开始运行")
    heartbeat_count = 0
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while True:
        try:
            # 检查心跳状态
            if not is_heartbeat_active:
                print(f"🔴 心跳任务被停止，尝试重新激活...")
                is_heartbeat_active = True
                logger.warning("心跳任务被停止，已重新激活")
            
            heartbeat_count += 1
            current_time = get_beijing_time()
            
            # 每次心跳都在控制台显示详细信息
            print(f"\n{'='*60}")
            print(f"💓 心跳信号 #{heartbeat_count} - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查活动状态
            time_since_last_activity = current_time - last_activity_time
            activity_minutes = time_since_last_activity.total_seconds() / 60
            
            print(f"📊 距离上次活动: {activity_minutes:.1f} 分钟")
            
            if time_since_last_activity > timedelta(minutes=10):
                print(f"⚠️  长时间无活动: {activity_minutes:.1f} 分钟")
                logger.warning(f"⚠️ 长时间无活动: {activity_minutes:.1f}分钟")
            else:
                print(f"✅ 活动正常: {activity_minutes:.1f} 分钟")
                logger.info(f"✅ 活动正常: {activity_minutes:.1f}分钟")
            
            # 显示系统状态
            print(f"🌐 运行环境: {'Render' if IS_RENDER else '本地'}")
            print(f"🔧 Firebase状态: {'✅ 已连接' if firebase_initialized else '❌ 未连接'}")
            print(f"💻 心跳状态: {'🟢 活跃' if is_heartbeat_active else '🔴 停止'}")
            print(f"🔄 连续错误: {consecutive_errors}/{max_consecutive_errors}")
            
            # 显示心跳统计
            print(f"📈 心跳统计: 总次数={heartbeat_count}, 运行时长={activity_minutes:.1f}分钟")
            print(f"{'='*60}\n")
            
            # 同时记录到日志
            logger.info(f"💓 心跳信号 #{heartbeat_count} - {current_time.strftime('%Y-%m-%d %H:%M:%S')} - 活动状态: {'正常' if activity_minutes < 10 else '需要关注'}")
            
            # 强制更新活动时间，防止机器人停止
            update_activity()
            
            # 更新心跳监控时间
            global last_heartbeat_time
            last_heartbeat_time = current_time
            
            # 重置错误计数
            consecutive_errors = 0
            
            # 等待10分钟
            await asyncio.sleep(600)  # 600秒 = 10分钟
                
        except Exception as e:
            consecutive_errors += 1
            error_msg = f"❌ 心跳任务错误 #{consecutive_errors}: {e}"
            print(f"\n{'='*60}")
            print(error_msg)
            print(f"⏰ 错误时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🔄 连续错误: {consecutive_errors}/{max_consecutive_errors}")
            print(f"{'='*60}\n")
            logger.error(f"心跳任务错误 #{consecutive_errors}: {e}")
            
            # 如果连续错误过多，尝试重启心跳
            if consecutive_errors >= max_consecutive_errors:
                print(f"🚨 连续错误过多，尝试重启心跳任务...")
                logger.critical(f"连续错误过多，重启心跳任务")
                is_heartbeat_active = False
                await asyncio.sleep(5)  # 等待5秒
                is_heartbeat_active = True
                consecutive_errors = 0
            
            # 等待时间根据错误次数调整
            wait_time = min(60 * consecutive_errors, 300)  # 最多等待5分钟
            print(f"⏳ 等待 {wait_time} 秒后重试...")
            await asyncio.sleep(wait_time)

async def start_heartbeat(application: Application):
    """启动心跳任务（增强版+监控）"""
    global is_heartbeat_active, heartbeat_monitor_task
    
    try:
        # 设置心跳状态为活跃
        is_heartbeat_active = True
        
        # 在控制台显示启动信息
        print(f"\n{'='*60}")
        print("🚀 心跳任务启动中...")
        print(f"⏰ 启动时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💓 心跳状态: {'🟢 活跃' if is_heartbeat_active else '🔴 停止'}")
        print(f"🌐 运行环境: {'Render' if IS_RENDER else '本地'}")
        print(f"{'='*60}\n")
        
        logger.info("🚀 心跳任务已启动")
        
        # 启动心跳监控任务
        if heartbeat_monitor_task is None:
            heartbeat_monitor_task = asyncio.create_task(heartbeat_monitor(application))
            print("✅ 心跳监控任务已启动")
        
        # 直接启动心跳任务，不使用create_task
        await heartbeat_task(application)
        
    except Exception as e:
        error_msg = f"❌ 心跳任务启动失败: {e}"
        print(f"\n{'='*60}")
        print(error_msg)
        print(f"⏰ 错误时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        logger.error(f"心跳任务启动失败: {e}")
        is_heartbeat_active = False

async def check_session_timeout(application: Application):
    """定期检查客服会话超时并自动结束"""
    logger.info("🕐 会话超时检查任务启动")
    print("✅ 会话超时检查任务已启动，每10秒检查一次")
    
    while True:
        try:
            current_time = get_beijing_time()
            expired_sessions = []
            
            # 检查所有会话
            for user_id, session_info in list(user_customer_service_sessions.items()):
                last_activity = session_info.get('last_activity')
                if last_activity:
                    time_since_activity = (current_time - last_activity).total_seconds()
                    
                    # 如果超过30秒无活动
                    if time_since_activity > SESSION_TIMEOUT_SECONDS:
                        expired_sessions.append(user_id)
                        logger.info(f"🕐 会话超时: 用户 {user_id}, 无活动时间 {time_since_activity:.0f} 秒")
            
            # 结束过期会话
            for user_id in expired_sessions:
                try:
                    # 获取用户信息
                    session_info = user_customer_service_sessions.get(user_id)
                    if session_info:
                        # 删除会话
                        del user_customer_service_sessions[user_id]
                        
                        # 通知用户会话已超时结束
                        timeout_message = get_text(user_id, 'cs_session_timeout')
                        if not timeout_message:
                            timeout_message = "⏰ 客服会话已因超时自动结束（30秒无活动）。\n如需继续联系客服，请重新发起会话。"
                        
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=timeout_message
                        )
                        
                        # 通知客服
                        end_notification = f"⏰ 会话超时结束\n用户ID: {user_id}\n时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n原因: 超过{SESSION_TIMEOUT_SECONDS}秒无活动"
                        
                        for cs_id in CUSTOMER_SERVICE_USERS:
                            try:
                                await application.bot.send_message(
                                    chat_id=cs_id,
                                    text=end_notification
                                )
                            except Exception as e:
                                logger.error(f"通知客服会话超时失败: {e}")
                        
                        logger.info(f"✅ 已自动结束超时会话: 用户 {user_id}")
                        
                except Exception as e:
                    logger.error(f"结束超时会话失败: {e}")
            
            # 等待10秒后再次检查
            await asyncio.sleep(10)
                    
        except Exception as e:
            logger.error(f"会话超时检查任务错误: {e}")
            await asyncio.sleep(10)

async def heartbeat_monitor(application: Application):
    """心跳监控任务，检测心跳是否正常"""
    global last_heartbeat_time, is_heartbeat_active
    
    print("🔍 心跳监控任务启动")
    logger.info("🔍 心跳监控任务启动")
    
    while True:
        try:
            current_time = get_beijing_time()
            time_since_last_heartbeat = current_time - last_heartbeat_time
            
            # 如果超过15分钟没有心跳，尝试重启
            if time_since_last_heartbeat > timedelta(minutes=15):
                print(f"🚨 心跳监控警告: 超过15分钟没有心跳信号")
                print(f"⏰ 最后心跳: {last_heartbeat_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏰ 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏰ 间隔时间: {time_since_last_heartbeat.total_seconds()/60:.1f} 分钟")
                
                logger.warning(f"心跳监控: 超过15分钟没有心跳，尝试重启")
                
                # 尝试重启心跳
                is_heartbeat_active = False
                await asyncio.sleep(5)
                is_heartbeat_active = True
                
                print("🔄 心跳任务已重启")
                logger.info("心跳任务已重启")
            
            # 每5分钟检查一次
            await asyncio.sleep(300)
            
        except Exception as e:
            print(f"❌ 心跳监控错误: {e}")
            logger.error(f"心跳监控错误: {e}")
            await asyncio.sleep(60)

async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理ping请求，用于保持机器人活跃"""
    update_activity()
    
    # 计算运行时间
    uptime = get_beijing_time() - last_activity_time
    
    await update.message.reply_text(
        "🏓 Pong! 机器人正在运行中...\n\n"
        f"⏰ <b>时间信息</b>\n"
        f"• 当前时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"• 最后活动: {last_activity_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"• 运行时长: {uptime.total_seconds()/60:.1f} 分钟\n\n"
        f"💓 <b>心跳状态</b>\n"
        f"• 状态: {'🟢 活跃' if is_heartbeat_active else '🔴 停止'}\n"
        f"• 环境: {'🌐 Render' if IS_RENDER else '💻 本地'}\n"
        f"• 端口: {PORT}\n\n"
        f"🔧 <b>系统状态</b>\n"
        f"• Firebase: {'✅ 已连接' if firebase_initialized else '❌ 未连接'}\n"
        f"• 数据库: {FIREBASE_CONFIG['project_id'] if FIREBASE_CONFIG['project_id'] else '未配置'}"
    )

async def heartbeat_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理心跳状态检查请求"""
    update_activity()
    
    try:
        # 计算运行时间
        uptime = get_beijing_time() - last_activity_time
        
        # 构建详细的心跳状态报告
        status_report = (
            "💓 <b>心跳状态详细报告</b>\n\n"
            f"⏰ <b>时间信息</b>\n"
            f"• 当前时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• 最后活动: {last_activity_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• 运行时长: {uptime.total_seconds()/60:.1f} 分钟\n\n"
            f"💓 <b>心跳系统状态</b>\n"
            f"• 心跳状态: {'🟢 活跃' if is_heartbeat_active else '🔴 停止'}\n"
            f"• 运行环境: {'🌐 Render' if IS_RENDER else '💻 本地'}\n"
            f"• 监听端口: {PORT}\n\n"
            f"🔧 <b>服务状态</b>\n"
            f"• Firebase: {'✅ 已连接' if firebase_initialized else '❌ 未连接'}\n"
            f"• 数据库: {FIREBASE_CONFIG['project_id'] if FIREBASE_CONFIG['project_id'] else '未配置'}\n"
            f"• Webhook: {'✅ 可用' if IS_RENDER and WEB_AVAILABLE else '❌ 不可用'}\n\n"
            f"📊 <b>活动监控</b>\n"
            f"• 距离上次活动: {uptime.total_seconds()/60:.1f} 分钟\n"
            f"• 活动状态: {'🟢 正常' if uptime.total_seconds() < 600 else '🟡 需要关注'}\n"
            f"• 建议: {'✅ 系统运行正常' if uptime.total_seconds() < 600 else '⚠️ 建议检查系统状态'}"
        )
        
        await update.message.reply_html(status_report)
        logger.info(f"✅ 心跳状态检查成功，用户: {update.effective_user.id}")
        
    except Exception as e:
        error_msg = f"❌ 心跳状态检查失败: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.error(f"心跳状态检查错误: {e}")

async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """测试命令处理器"""
    try:
        await update.message.reply_text("🧪 测试命令工作正常！")
        logger.info(f"✅ 测试命令成功，用户: {update.effective_user.id}")
    except Exception as e:
        await update.message.reply_text(f"❌ 测试命令失败: {str(e)}")
        logger.error(f"测试命令错误: {e}")

async def set_welcome_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置欢迎图片命令处理器"""
    update_activity()
    user = update.effective_user
    
    # 自动识别超级管理员
    check_and_set_super_admin(user)
    
    user_id = user.id
    
    # 检查权限
    if not can_manage_images(user_id):
        await update.message.reply_text("❌ 抱歉，只有管理员和客服人员可以设置图片。")
        return
    
    # 如果是超级管理员，显示机器人选择菜单
    if is_super_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("机器人1 (@QTY01)", callback_data="set_img_welcome_bot1")],
            [InlineKeyboardButton("机器人2 (@QTY15)", callback_data="set_img_welcome_bot2")],
            [InlineKeyboardButton("机器人3 (@qty772)", callback_data="set_img_welcome_bot3")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📸 <b>设置欢迎图片</b>\n\n"
            "请选择要设置图片的机器人：",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        logger.info(f"超级管理员 {user_id} 开始设置欢迎图片")
    else:
        # 普通客服只能设置当前机器人
        user_image_setting_state[user_id] = {'type': 'WELCOME_IMAGE', 'bot_id': BOT_ID}
        
        await update.message.reply_text(
            "📸 <b>设置欢迎图片</b>\n\n"
            "请发送一张图片，这张图片将用于欢迎信息（/start 命令）。\n\n"
            "💡 提示：\n"
            "• 支持 JPG、PNG 等常见格式\n"
            "• 建议图片尺寸：800x600 或更高\n"
            "• 图片会自动保存并应用到当前机器人\n\n"
            "发送图片后，系统会自动设置。",
            parse_mode='HTML'
        )
        logger.info(f"客服 {user_id} 开始为 {BOT_ID} 设置欢迎图片")

async def set_register_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置注册图片命令处理器"""
    update_activity()
    user = update.effective_user
    
    # 自动识别超级管理员
    check_and_set_super_admin(user)
    
    user_id = user.id
    
    # 检查权限
    if not can_manage_images(user_id):
        await update.message.reply_text("❌ 抱歉，只有管理员和客服人员可以设置图片。")
        return
    
    # 如果是超级管理员，显示机器人选择菜单
    if is_super_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("机器人1 (@QTY01)", callback_data="set_img_register_bot1")],
            [InlineKeyboardButton("机器人2 (@QTY15)", callback_data="set_img_register_bot2")],
            [InlineKeyboardButton("机器人3 (@qty772)", callback_data="set_img_register_bot3")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📸 <b>设置注册图片</b>\n\n"
            "请选择要设置图片的机器人：",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        logger.info(f"超级管理员 {user_id} 开始设置注册图片")
    else:
        # 普通客服只能设置当前机器人
        user_image_setting_state[user_id] = {'type': 'REGISTER_IMAGE', 'bot_id': BOT_ID}
        
        await update.message.reply_text(
            "📸 <b>设置注册图片</b>\n\n"
            "请发送一张图片，这张图片将用于自助注册功能。\n\n"
            "💡 提示：\n"
            "• 支持 JPG、PNG 等常见格式\n"
            "• 建议图片尺寸：800x600 或更高\n"
            "• 图片会自动保存并应用到当前机器人\n\n"
            "发送图片后，系统会自动设置。",
            parse_mode='HTML'
        )
        logger.info(f"客服 {user_id} 开始为 {BOT_ID} 设置注册图片")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户发送的图片"""
    update_activity()
    user_id = update.effective_user.id
    
    # 检查用户是否在广播编辑状态
    if user_id in broadcast_state and broadcast_state[user_id]['step'] == 'editing_photo':
        try:
            # 获取图片 file_id（选择最大尺寸的图片）
            photo = update.message.photo[-1]
            file_id = photo.file_id
            
            # 保存图片到广播状态
            broadcast_state[user_id]['photo_file_id'] = file_id
            broadcast_state[user_id]['step'] = 'idle'
            
            await update.message.reply_text(
                "✅ <b>广播图片设置成功！</b>\n\n"
                "图片已保存，现在返回广播控制面板。",
                parse_mode='HTML'
            )
            
            # 返回广播控制面板
            await show_broadcast_panel(user_id, context)
            
            logger.info(f"用户 {user_id} 设置了广播图片")
            return
            
        except Exception as e:
            await update.message.reply_text(f"❌ 处理广播图片时出错: {str(e)}")
            logger.error(f"处理广播图片错误: {e}")
            return
    
    # 检查用户是否正在设置图片
    if user_id not in user_image_setting_state:
        return  # 如果不是在设置图片状态，忽略
    
    # 检查权限
    if not can_manage_images(user_id):
        await update.message.reply_text("❌ 抱歉，只有管理员和客服人员可以设置图片。")
        return
    
    try:
        # 获取图片 file_id（选择最大尺寸的图片）
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        # 获取设置信息
        setting_info = user_image_setting_state[user_id]
        image_type = setting_info['type']
        target_bot_id = setting_info['bot_id']
        
        # 保存图片配置
        if save_image_config(target_bot_id, image_type, file_id):
            image_type_name = "欢迎图片" if image_type == 'WELCOME_IMAGE' else "注册图片"
            bot_name = BOT_CONFIGS[target_bot_id]['BOT_NAME']
            await update.message.reply_text(
                f"✅ <b>{image_type_name}设置成功！</b>\n\n"
                f"图片已保存并应用到 {bot_name}。\n"
                f"用户将在相应功能中看到这张图片。",
                parse_mode='HTML'
            )
            logger.info(f"用户 {user_id} 成功为 {target_bot_id} 设置了 {image_type}")
        else:
            await update.message.reply_text("❌ 保存图片配置失败，请稍后重试。")
        
        # 清除状态
        del user_image_setting_state[user_id]
        
    except Exception as e:
        await update.message.reply_text(f"❌ 处理图片时出错: {str(e)}")
        logger.error(f"处理图片错误: {e}")
        # 清除状态
        if user_id in user_image_setting_state:
            del user_image_setting_state[user_id]

async def handle_image_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理图片设置的回调（超级管理员选择机器人）"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # 检查是否是超级管理员
    if not is_super_admin(user_id):
        await query.edit_message_text("❌ 只有超级管理员可以使用此功能。")
        return
    
    # 解析回调数据：set_img_welcome_bot1 或 set_img_register_bot1
    data = query.data
    if data.startswith('set_img_welcome_'):
        image_type = 'WELCOME_IMAGE'
        image_type_name = "欢迎图片"
        bot_id = data.replace('set_img_welcome_', '')
    elif data.startswith('set_img_register_'):
        image_type = 'REGISTER_IMAGE'
        image_type_name = "注册图片"
        bot_id = data.replace('set_img_register_', '')
    else:
        return
    
    # 设置状态
    user_image_setting_state[user_id] = {'type': image_type, 'bot_id': bot_id}
    
    bot_name = BOT_CONFIGS[bot_id]['BOT_NAME']
    
    await query.edit_message_text(
        f"📸 <b>设置{image_type_name}</b>\n\n"
        f"目标机器人：{bot_name}\n\n"
        f"请发送一张图片，这张图片将用于该机器人的{image_type_name}。\n\n"
        f"💡 提示：\n"
        f"• 支持 JPG、PNG 等常见格式\n"
        f"• 建议图片尺寸：800x600 或更高\n"
        f"• 图片会自动保存并应用\n\n"
        f"发送图片后，系统会自动设置。",
        parse_mode='HTML'
    )
    logger.info(f"超级管理员 {user_id} 选择为 {bot_id} 设置 {image_type}")

async def performance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """性能监控命令"""
    try:
        start_time = get_beijing_time()
        update_activity()
        
        # 测试基本响应速度
        response_time = (get_beijing_time() - start_time).total_seconds() * 1000
        
        # 构建性能报告
        performance_report = (
            "⚡ <b>性能监控报告</b>\n\n"
            f"🕐 <b>响应时间</b>\n"
            f"• 命令处理: {response_time:.2f} ms\n"
            f"• 当前时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"💓 <b>系统状态</b>\n"
            f"• 心跳状态: {'🟢 活跃' if is_heartbeat_active else '🔴 停止'}\n"
            f"• Firebase: {'✅ 已连接' if firebase_initialized else '❌ 未连接'}\n"
            f"• 运行环境: {'🌐 Render' if IS_RENDER else '💻 本地'}\n\n"
            f"📊 <b>性能指标</b>\n"
            f"• 响应状态: {'🟢 正常' if response_time < 1000 else '🟡 较慢' if response_time < 5000 else '🔴 很慢'}\n"
            f"• 建议: {'✅ 性能良好' if response_time < 1000 else '⚠️ 建议优化' if response_time < 5000 else '🚨 需要立即优化'}"
        )
        
        await update.message.reply_html(performance_report)
        logger.info(f"✅ 性能监控成功，响应时间: {response_time:.2f}ms")
        
    except Exception as e:
        await update.message.reply_text(f"❌ 性能监控失败: {str(e)}")
        logger.error(f"性能监控错误: {e}")

async def broadcast_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """广播命令处理器"""
    update_activity()
    
    user = update.effective_user
    user_id = user.id
    
    # 检查权限
    if not can_broadcast(user_id):
        await update.message.reply_text("❌ 抱歉，只有管理员和客服人员可以使用广播功能。")
        return
    
    # 初始化广播状态
    broadcast_state[user_id] = {
        'step': 'idle',
        'text': None,
        'photo_file_id': None,
        'buttons': []
    }
    
    # 显示广播控制面板
    await show_broadcast_panel(user_id, context, update.message)
    
    logger.info(f"用户 {user_id} 开始使用广播功能")

async def show_broadcast_panel(user_id, context, message=None, edit=True):
    """显示广播控制面板"""
    try:
        # 获取用户数量
        user_count = len(await get_all_user_ids())
        
        # 获取当前广播状态
        current_state = broadcast_state.get(user_id, {})
        text_status = "✅已设置" if current_state.get('text') else "未设置"
        photo_status = "✅已设置" if current_state.get('photo_file_id') else "未设置"
        buttons_status = "✅已设置" if current_state.get('buttons') else "未设置"
        
        # 构建面板文本
        panel_text = (
            "📢 <b>广播控制面板</b>\n\n"
            f"<b>当前状态:</b>\n"
            f"📝 文本: {text_status}\n"
            f"🖼️ 图片: {photo_status}\n"
            f"🔘 按钮: {buttons_status}\n\n"
            f"📊 <b>目标用户: {user_count} 人</b>"
        )
        
        # 构建按钮
        keyboard = [
            [InlineKeyboardButton("📝 设置文本内容", callback_data="bc_set_text")],
            [
                InlineKeyboardButton(f"🖼️ 设置图片 [{photo_status}]", callback_data="bc_set_photo"),
                InlineKeyboardButton(f"🔘 设置按钮 [{buttons_status}]", callback_data="bc_set_buttons")
            ],
            [InlineKeyboardButton("👁️ 预览广播", callback_data="bc_preview")],
            [
                InlineKeyboardButton("📤 发送广播", callback_data="bc_send_confirm") if current_state.get('text') else InlineKeyboardButton("📤 发送广播 [需先设置文本]", callback_data="bc_disabled"),
                InlineKeyboardButton("❌ 取消", callback_data="bc_cancel")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 尝试编辑消息，如果失败则发送新消息
        if edit and message:
            try:
                await message.edit_text(panel_text, parse_mode='HTML', reply_markup=reply_markup)
            except Exception as edit_error:
                # 如果编辑失败，发送新消息
                logger.warning(f"编辑消息失败，发送新消息: {edit_error}")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=panel_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=panel_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"显示广播控制面板失败: {e}")
        # 发送简单的错误消息
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ 显示控制面板失败: {str(e)}"
            )
        except Exception as send_error:
            logger.error(f"发送错误消息也失败: {send_error}")

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理管理员统计请求，显示访客统计信息（隐藏命令）"""
    update_activity()
    
    # 检查是否为管理员（这里可以根据需要设置管理员ID）
    user_id = update.effective_user.id
    # 可以在这里添加管理员ID检查，例如：
    # if user_id not in [ADMIN_ID_1, ADMIN_ID_2]:
    #     await update.message.reply_text("❌ 权限不足，此命令仅限管理员使用。")
    #     return
    
    # 获取当前机器人统计信息
    stats = get_visitor_stats()
    
    # 构建统计报告
    report = f"🔐 <b>管理员统计报告</b>\n\n"
    report += f"🤖 <b>机器人信息</b>\n"
    report += f"• 机器人ID: {BOT_ID}\n"
    report += f"• 机器人名称: {CURRENT_BOT_CONFIG['BOT_NAME']}\n"
    report += f"• 数据库: {FIREBASE_CONFIG['project_id'] if FIREBASE_CONFIG['project_id'] else '未配置'}\n\n"
    
    report += f"👥 <b>总体统计</b>\n"
    report += f"• 总访客数: {stats['total_visitors']}\n"
    report += f"• 今日访客: {stats['today_visitors']}\n"
    report += f"• 今日操作: {stats['today_actions']}\n\n"
    
    report += f"📅 <b>最近7天统计</b>\n"
    for date, data in sorted(stats['recent_stats'].items(), reverse=True):
        report += f"• {date}: {data['visitors']} 访客, {data['actions']} 操作\n"
    
    # 如果Firebase可用，尝试获取所有机器人统计
    if firebase_initialized and firebase_db:
        try:
            # 获取所有机器人列表
            bots_ref = firebase_db.collection('bots')
            bots_docs = bots_ref.stream()
            
            all_bots_stats = []
            for bot_doc in bots_docs:
                bot_id = bot_doc.id
                bot_stats_ref = bot_doc.reference.collection('stats').document('visitor_stats')
                bot_stats_doc = bot_stats_ref.get()
                
                if bot_stats_doc.exists:
                    bot_data = bot_stats_doc.to_dict()
                    all_bots_stats.append({
                        'id': bot_id,
                        'name': bot_data.get('bot_name', bot_id),
                        'visitors': bot_data.get('total_visitors', 0),
                        'last_updated': bot_data.get('last_updated', '未知')
                    })
            
            if all_bots_stats:
                report += f"\n🤖 <b>所有机器人统计</b>\n"
                for bot in all_bots_stats:
                    report += f"• {bot['name']} ({bot['id']}): {bot['visitors']} 访客\n"
                
        except Exception as e:
            logger.error(f"获取所有机器人统计失败: {e}")
    
    report += f"\n⏰ 统计时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}"
    report += f"\n👤 查询用户: {update.effective_user.first_name} (ID: {user_id})"
    
    await update.message.reply_html(report)

# 6. 定义主菜单按钮 (常规键盘)
def get_main_menu_keyboard(user_id):
    """返回主菜单的键盘布局，根据用户的语言设置生成"""
    keyboard = [
        [
            KeyboardButton(get_text(user_id, 'menu_change_lang')),
            KeyboardButton(get_text(user_id, 'menu_self_register'))
        ],
        [
            KeyboardButton(get_text(user_id, 'menu_mainland_user')),
            KeyboardButton(get_text(user_id, 'menu_overseas_user'))
        ],
        [
            KeyboardButton(get_text(user_id, 'menu_recharge')), # 招商频道
            KeyboardButton(get_text(user_id, 'menu_withdraw')) # 推单频道
        ],
        [
            KeyboardButton(get_text(user_id, 'menu_customer_service')),
            KeyboardButton(get_text(user_id, 'menu_bidirectional_contact'))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# 7. 定义语言选择菜单按钮 (内嵌键盘)
def get_language_keyboard():
    """返回语言选择的内嵌键盘"""
    keyboard = [
        [InlineKeyboardButton("简体中文🇨🇳", callback_data='lang_zh-CN')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("ไทย 🇹🇭", callback_data='lang_th')],
        [InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data='lang_vi')]
    ]
    return InlineKeyboardMarkup(keyboard)

# 8. 辅助函数：处理不同类型的更新，获取消息和用户对象
def get_message_and_user(update: Update):
    """从更新对象中提取消息和用户对象，无论是来自消息还是回调查询"""
    if update.message:
        return update.message, update.effective_user
    elif update.callback_query and update.callback_query.message:
        return update.callback_query.message, update.effective_user
    return None, None

# 9. 定义 /start 命令的处理器
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户发送 /start 命令时调用"""
    update_activity()  # 更新活动时间
    
    user = update.effective_user
    
    # 自动识别超级管理员
    check_and_set_super_admin(user)
    
    logger.info(f"User {user.first_name} started the bot.")
    user_id = user.id
    
    # 更新访客统计
    update_visitor_stats(user_id)

    if user_id not in user_data:
        user_data[user_id] = 'zh-CN'

    # 获取访客统计信息
    stats = get_visitor_stats()
    display_visitor_count = stats['total_visitors'] + 15941  # 显示数量 = 实际数量 + 15941
    
    new_welcome_text = (
        f"{get_text(user_id, 'welcome_visitor').format(count=display_visitor_count)}\n\n"
        f"{get_text(user_id, 'activity_title')}\n\n"
        f"{get_text(user_id, 'activity_benefits')}\n"
        f"{get_text(user_id, 'activity_description')}\n"
        f"{get_text(user_id, 'benefit_1')}\n"
        f"{get_text(user_id, 'benefit_2')}\n"
        f"{get_text(user_id, 'benefit_3')}\n\n"
        f"{get_text(user_id, 'claim_method')}\n"
        f"{get_text(user_id, 'claim_description')}\n\n"
        f"{get_text(user_id, 'investment_channel')}\n"
        f" {get_text(user_id, 'investment_link')}\n\n"
        f"{get_text(user_id, 'promotion_channel')}\n"
        f" {get_text(user_id, 'promotion_link')}\n\n"
        f"{get_text(user_id, 'customer_service_title')}\n"
        f"{CS_HANDLE}"
    )

    # 检查是否有欢迎图片
    welcome_image = CURRENT_BOT_CONFIG.get('WELCOME_IMAGE')
    if welcome_image:
        # 如果有图片，发送图片和文字
        await update.message.reply_photo(
            photo=welcome_image,
            caption=new_welcome_text,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    else:
        # 如果没有图片，只发送文字
        await update.message.reply_html(
            new_welcome_text,
            reply_markup=get_main_menu_keyboard(user_id)
        )

# 10. 定义「招商频道」按钮的处理器
async def advertising_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「招商频道」按钮时调用"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    # 更新访客统计
    update_visitor_stats(user_id)
    prompt_text = get_text(user_id, 'advertising_channel_prompt')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'menu_recharge'), url='https://t.me/QTY18')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=prompt_text, reply_markup=reply_markup)

# 11. 定义「推单频道」按钮的处理器
async def promotion_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「推单频道」按钮时调用"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    # 更新访客统计
    update_visitor_stats(user_id)
    prompt_text = get_text(user_id, 'promotion_channel_prompt')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'menu_withdraw'), url='https://t.me/SJB33')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=prompt_text, reply_markup=reply_markup)

# 12. 定义「人工客服」按钮的处理器
async def customer_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「人工客服」按钮时调用"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    # 更新访客统计
    update_visitor_stats(user_id)
    live_cs_title = get_text(user_id, 'live_customer_service_title')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_1'), url=f'https://t.me/{CS_HANDLE[1:]}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_html(text=live_cs_title, reply_markup=reply_markup)

# 12.1 定义「双向联系」按钮的处理器
async def start_customer_service_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动客服会话"""
    update_activity()
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    user_name = user.first_name or "Unknown"
    
    # 更新访客统计
    update_visitor_stats(user_id)
    
    # 记录会话开始
    user_customer_service_sessions[user_id] = {
        'status': 'active',
        'start_time': get_beijing_time(),
        'last_activity': get_beijing_time()
    }
    
    # 通知客服有新会话
    notification_text = get_text(user_id, 'new_cs_session_notification').format(
        user_name=user_name,
        user_id=user_id,
        time=get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    for cs_id in CUSTOMER_SERVICE_USERS:
        try:
            await context.bot.send_message(chat_id=cs_id, text=notification_text)
        except Exception as e:
            logger.error(f"通知客服失败: {e}")
    
    # 回复用户
    await message.reply_text(get_text(user_id, 'start_cs_session'))

# 12.2 结束客服会话
async def end_customer_service_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """结束客服会话"""
    update_activity()
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    user_name = user.first_name or "Unknown"
    
    if user_id in user_customer_service_sessions:
        del user_customer_service_sessions[user_id]
        
        # 通知客服会话结束
        end_notification = get_text(user_id, 'cs_session_ended_notification').format(
            user_name=user_name,
            user_id=user_id,
            time=get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        for cs_id in CUSTOMER_SERVICE_USERS:
            try:
                await context.bot.send_message(chat_id=cs_id, text=end_notification)
            except Exception as e:
                logger.error(f"通知客服会话结束失败: {e}")
        
        await message.reply_text(get_text(user_id, 'end_cs_session'))
    else:
        await message.reply_text(get_text(user_id, 'end_cs_session'))

# 12.3 转发用户消息给客服
async def forward_user_message_to_cs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """将用户消息转发给客服"""
    update_activity()
    
    message = update.message
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"
    
    # 构建转发消息
    forward_text = f"👤 用户消息\n用户: {user_name} (ID: {user_id})\n时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n\n{message.text}"
    
    # 发送给客服
    for cs_id in CUSTOMER_SERVICE_USERS:
        try:
            sent_message = await context.bot.send_message(
                chat_id=cs_id,
                text=forward_text
            )
            # 记录消息映射
            message_mapping[sent_message.message_id] = {
                'user_id': user_id,
                'direction': 'to_cs',
                'timestamp': get_beijing_time()
            }
        except Exception as e:
            logger.error(f"转发用户消息到客服失败: {e}")
    
    # 确认消息已收到
    await message.reply_text(get_text(user_id, 'cs_message_sent'))
    
    # 更新会话活动时间
    if user_id in user_customer_service_sessions:
        user_customer_service_sessions[user_id]['last_activity'] = get_beijing_time()

# 12.4 处理客服回复的消息
async def handle_customer_service_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理客服回复的消息"""
    update_activity()
    
    message = update.message
    cs_id = message.from_user.id
    text = message.text
    
    # 检查是否是回复消息
    if message.reply_to_message:
        original_message = message.reply_to_message
        if original_message.message_id in message_mapping:
            target_user_id = message_mapping[original_message.message_id]['user_id']
            
            # 构建回复消息
            reply_text = get_text(target_user_id, 'cs_reply_received').format(
                cs_handle=CS_HANDLE,
                time=get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'),
                message=message.text
            )
            
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=reply_text
                )
                await message.reply_text("✅ 回复已发送给用户")
                
                # 更新会话活动时间
                if target_user_id in user_customer_service_sessions:
                    user_customer_service_sessions[target_user_id]['last_activity'] = get_beijing_time()
            except Exception as e:
                logger.error(f"转发客服回复失败: {e}")
                await message.reply_text("❌ 转发失败，用户可能已屏蔽机器人")
        else:
            await message.reply_text("❌ 无法找到对应的用户消息")
    else:
        # 检查是否是菜单功能按钮
        user_id = cs_id
        lang_code = user_data.get(user_id, 'zh-CN')
        texts = LANGUAGES[lang_code]
        
        # 如果是菜单按钮，让handle_text_messages处理
        if text in [texts['menu_self_register'], texts['menu_mainland_user'], texts['menu_overseas_user'], 
                   texts['menu_recharge'], texts['menu_withdraw'], texts['menu_customer_service'], 
                   texts['menu_bidirectional_contact'], texts['menu_change_lang']]:
            # 让handle_text_messages处理菜单按钮
            await handle_text_messages(update, context)
            return
        
        # 如果不是回复消息，直接转发给所有活跃会话的用户
        if user_customer_service_sessions:
            broadcast_text = f"📢 客服广播消息\n客服: {CS_HANDLE}\n时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n\n{message.text}"
            
            for user_id in list(user_customer_service_sessions.keys()):
                try:
                    await context.bot.send_message(chat_id=user_id, text=broadcast_text)
                except Exception as e:
                    logger.error(f"广播消息到用户 {user_id} 失败: {e}")
            
            await message.reply_text(f"✅ 广播消息已发送给 {len(user_customer_service_sessions)} 个活跃会话")
        else:
            await message.reply_text("❌ 当前没有活跃的客服会话")

# 12.5 获取用户ID命令
async def get_user_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """获取用户ID的命令"""
    update_activity()
    
    user = update.effective_user
    
    # 自动识别超级管理员
    is_new_super_admin = check_and_set_super_admin(user)
    
    user_id = user.id
    username = user.username or "无用户名"
    first_name = user.first_name or "未知"
    
    # 获取用户语言设置
    lang_code = user_data.get(user_id, 'zh-CN')
    texts = LANGUAGES[lang_code]
    
    # 构建用户信息
    user_info = texts['get_user_id_info'].format(
        user_id=user_id,
        username=username,
        first_name=first_name
    )
    
    # 如果是超级管理员，添加特殊标识
    if is_super_admin(user_id):
        user_info += f"\n\n👑 <b>超级管理员权限</b>\n✅ 您可以管理所有3个机器人的图片设置"
        if is_new_super_admin:
            user_info += f"\n🎉 已自动识别并授予超级管理员权限！"
    
    await update.message.reply_html(user_info)
    
    # 如果是客服用户，自动更新配置
    expected_username = CS_HANDLE[1:] if CS_HANDLE.startswith('@') else CS_HANDLE
    
    if username == expected_username:
        # 自动更新客服用户ID
        global CUSTOMER_SERVICE_USERS, USERNAME_TO_ID, CURRENT_BOT_CONFIG
        if user_id not in CUSTOMER_SERVICE_USERS:
            CUSTOMER_SERVICE_USERS.append(user_id)
        USERNAME_TO_ID[expected_username] = user_id
        
        # 通知配置已更新
        config_updated = f"✅ 客服配置已自动更新\n{CS_HANDLE} 的用户ID: {user_id}\n双向联系功能已激活！"
        await update.message.reply_text(config_updated)
        
        logger.info(f"✅ 自动更新客服配置: {CS_HANDLE} -> {user_id}")

# 12.6 管理员命令：查看客服配置
async def admin_cs_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员查看客服配置的命令"""
    update_activity()
    
    user = update.effective_user
    user_id = user.id
    
    # 检查是否是管理员（这里可以添加管理员权限检查）
    # 暂时允许所有用户查看，实际使用时应该限制权限
    
    config_info = f"📋 客服配置信息\n\n"
    config_info += f"机器人ID: {BOT_ID}\n"
    config_info += f"机器人名称: {CURRENT_BOT_CONFIG['BOT_NAME']}\n"
    config_info += f"客服句柄: {CS_HANDLE}\n"
    config_info += f"客服用户ID列表: {CUSTOMER_SERVICE_USERS}\n"
    config_info += f"用户名映射: {USERNAME_TO_ID}\n"
    config_info += f"活跃会话数: {len(user_customer_service_sessions)}\n"
    config_info += f"消息映射数: {len(message_mapping)}\n"
    
    if user_customer_service_sessions:
        config_info += f"\n活跃会话用户:\n"
        for uid, session in user_customer_service_sessions.items():
            config_info += f"- 用户ID: {uid}, 开始时间: {session['start_time'].strftime('%H:%M:%S')}\n"
    
    await update.message.reply_text(config_info)

# 13. 定义「切换语言」按钮的处理器
async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「切换语言」按钮时调用"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    # 更新访客统计
    update_visitor_stats(user_id)
    
    await message.reply_text(
        get_text(user_id, 'language_selection'),
        reply_markup=get_language_keyboard()
    )

# 14. 定义「自助注册」按钮的处理器
async def self_register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「自助注册」按钮时调用，发送新的注册信息"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    message_text = get_text(user_id, 'register_info_download_notice')
    
    # 获取访客统计信息
    stats = get_visitor_stats()
    display_visitor_count = stats['total_visitors'] + 15941  # 显示数量 = 实际数量 + 15941
    
    welcome_message = (
        f"{get_text(user_id, 'welcome_visitor').format(count=display_visitor_count)}\n\n"
        f"✨ <b>{get_text(user_id, 'vip_member_title')}</b> ✨\n"
        f"{get_text(user_id, 'activity_title')}\n\n"
        f"🎁 <b>{get_text(user_id, 'activity_benefits')}</b>\n"
        f"{get_text(user_id, 'activity_description')}\n"
        f"{get_text(user_id, 'benefit_1')}\n"
        f"{get_text(user_id, 'benefit_2')}\n"
        f"{get_text(user_id, 'benefit_3')}\n\n"
        f"💬 <b>{get_text(user_id, 'claim_method')}</b>\n"
        f"{get_text(user_id, 'claim_description')}\n\n"
        f"📢 <b>{get_text(user_id, 'investment_channel')}</b>\n"
        f" {get_text(user_id, 'investment_link')}\n\n"
        f"📢 <b>{get_text(user_id, 'promotion_channel')}</b>\n"
        f" {get_text(user_id, 'promotion_link')}\n\n"
        f"💬 <b>{get_text(user_id, 'customer_service_title')}</b>\n"
        f"<a href='https://t.me/{CS_HANDLE[1:]}'>{CS_HANDLE}</a>\n\n"
        f"<b>{get_text(user_id, 'registration_prompt_title')}</b>\n"
        f"{get_text(user_id, 'mainland_user_prompt')}\n"
        f"{get_text(user_id, 'overseas_user_prompt')}"
    )
    
    full_message = f"{welcome_message}\n{message_text}"

    # 检查是否有自助注册图片
    register_image = CURRENT_BOT_CONFIG.get('REGISTER_IMAGE')
    if register_image:
        # 如果有图片，发送图片和文字
        await message.reply_photo(
            photo=register_image,
            caption=full_message,
            parse_mode='HTML',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    else:
        # 如果没有图片，只发送文字
        await message.reply_html(text=full_message, reply_markup=get_main_menu_keyboard(user_id))

# 15. 定义「大陆用户」按钮的处理器
async def mainland_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「大陆用户」按钮时，发送一个可直接跳转趣体育注册页面的按钮"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    qu_link_text = get_text(user_id, 'register_info_qu_link_text')
    
    keyboard = [
        [InlineKeyboardButton(qu_link_text, url=GAME_URL_QU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(text=get_text(user_id, 'register_info_notice_prompt'), reply_markup=reply_markup)

# 16. 定义「海外用户」按钮的处理器
async def overseas_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「海外用户」按钮时，发送一个可直接跳转MK体育注册页面的按钮"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
    mk_link_text = get_text(user_id, 'register_info_mk_link_text')
    
    keyboard = [
        [InlineKeyboardButton(mk_link_text, url=GAME_URL_MK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(text=get_text(user_id, 'register_info_notice_prompt'), reply_markup=reply_markup)

# 17. 定义内嵌按钮回调的处理器
async def handle_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理内嵌键盘按钮点击事件"""
    update_activity()  # 更新活动时间
    
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id
    language_code = query.data.split('_')[1]
    user_data[user_id] = language_code
    await query.message.reply_text(
        get_text(user_id, 'lang_changed'),
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def handle_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理广播相关回调"""
    update_activity()
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # 检查权限
    if not can_broadcast(user_id):
        await query.edit_message_text("❌ 抱歉，只有管理员和客服人员可以使用广播功能。")
        return
    
    # 检查用户是否有广播状态
    if user_id not in broadcast_state:
        await query.edit_message_text("❌ 广播会话已过期，请重新使用 /broadcast 命令。")
        return
    
    callback_data = query.data
    
    if callback_data == "bc_set_text":
        # 设置文本
        broadcast_state[user_id]['step'] = 'editing_text'
        await query.edit_message_text(
            "📝 <b>设置广播文本</b>\n\n"
            "请发送您要广播的文本内容。\n"
            "支持HTML格式，可以使用以下标签：\n"
            "• <b>粗体</b>\n"
            "• <i>斜体</i>\n"
            "• <a href='链接'>链接文字</a>\n\n"
            "发送文本后，系统会自动设置并返回控制面板。",
            parse_mode='HTML'
        )
        
    elif callback_data == "bc_set_photo":
        # 设置图片
        broadcast_state[user_id]['step'] = 'editing_photo'
        await query.edit_message_text(
            "🖼️ <b>设置广播图片</b>\n\n"
            "请发送一张图片，这将作为广播的图片内容。\n"
            "支持 JPG、PNG 等常见格式。\n\n"
            "💡 提示：\n"
            "• 如果不想要图片，可以稍后在控制面板中删除\n"
            "• 发送图片后，系统会自动设置并返回控制面板",
            parse_mode='HTML'
        )
        
    elif callback_data == "bc_set_buttons":
        # 设置按钮
        broadcast_state[user_id]['step'] = 'editing_buttons'
        await query.edit_message_text(
            "🔘 <b>设置广播按钮</b>\n\n"
            "请发送按钮配置，格式如下：\n"
            "按钮文字1|链接1\n"
            "按钮文字2|链接2\n\n"
            "示例：\n"
            "注册账号|https://example.com\n"
            "联系我们|https://t.me/example\n\n"
            "💡 提示：\n"
            "• 每行一个按钮\n"
            "• 按钮文字和链接用 | 分隔\n"
            "• 如果不想要按钮，发送 '无' 或 'none'",
            parse_mode='HTML'
        )
        
    elif callback_data == "bc_preview":
        # 预览广播
        await show_broadcast_preview(query, context)
        
    elif callback_data == "bc_send_confirm":
        # 发送确认
        await show_send_confirmation(query, context)
        
    elif callback_data == "bc_send_execute":
        # 执行发送
        await execute_broadcast_send(query, context)
        
    elif callback_data == "bc_cancel":
        # 取消广播
        if user_id in broadcast_state:
            del broadcast_state[user_id]
        await query.edit_message_text(
            "❌ 广播已取消\n\n"
            "如需重新开始，请使用 /broadcast 命令。"
        )
        
    elif callback_data == "bc_disabled":
        # 禁用按钮点击
        await query.answer("请先设置文本内容", show_alert=True)
        
    elif callback_data == "bc_back":
        # 返回控制面板
        await show_broadcast_panel(user_id, context, query.message)

async def show_broadcast_preview(query, context):
    """显示广播预览"""
    user_id = query.from_user.id
    current_state = broadcast_state.get(user_id, {})
    
    # 检查是否有文本内容
    if not current_state.get('text'):
        await query.edit_message_text("❌ 请先设置文本内容才能预览。")
        return
    
    # 构建预览消息
    preview_text = current_state['text']
    photo_file_id = current_state.get('photo_file_id')
    buttons = current_state.get('buttons', [])
    
    # 构建按钮
    reply_markup = None
    if buttons:
        keyboard = []
        for button in buttons:
            keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 添加预览标识
    preview_header = "👁️ <b>广播预览</b>\n\n"
    full_preview_text = preview_header + preview_text
    
    try:
        if photo_file_id:
            # 发送带图片的预览
            await context.bot.send_photo(
                chat_id=user_id,
                photo=photo_file_id,
                caption=full_preview_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            # 发送纯文本预览
            await context.bot.send_message(
                chat_id=user_id,
                text=full_preview_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        
        # 显示返回按钮
        keyboard = [[InlineKeyboardButton("🔙 返回控制面板", callback_data="bc_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                "✅ 预览已发送\n\n"
                "这就是用户将收到的广播内容。",
                reply_markup=reply_markup
            )
        except Exception as edit_error:
            # 如果编辑失败，发送新消息
            logger.warning(f"编辑预览消息失败，发送新消息: {edit_error}")
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ 预览已发送\n\n这就是用户将收到的广播内容。",
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"发送广播预览失败: {e}")
        await query.edit_message_text(f"❌ 预览发送失败: {str(e)}")

async def show_send_confirmation(query, context):
    """显示发送确认"""
    user_id = query.from_user.id
    current_state = broadcast_state.get(user_id, {})
    
    # 检查是否有文本内容
    if not current_state.get('text'):
        await query.edit_message_text("❌ 请先设置文本内容才能发送。")
        return
    
    # 获取用户数量
    user_count = len(await get_all_user_ids())
    
    # 构建确认消息
    confirmation_text = (
        f"📤 <b>确认发送广播</b>\n\n"
        f"📊 <b>目标用户:</b> {user_count} 人\n\n"
        f"📝 <b>内容预览:</b>\n"
        f"文本: {'✅' if current_state.get('text') else '❌'}\n"
        f"图片: {'✅' if current_state.get('photo_file_id') else '❌'}\n"
        f"按钮: {'✅' if current_state.get('buttons') else '❌'}\n\n"
        f"⚠️ <b>注意:</b> 广播发送后无法撤回，请确认无误后再发送。"
    )
    
    # 构建确认按钮
    keyboard = [
        [
            InlineKeyboardButton("✅ 确认发送", callback_data="bc_send_execute"),
            InlineKeyboardButton("❌ 取消", callback_data="bc_cancel")
        ],
        [InlineKeyboardButton("🔙 返回控制面板", callback_data="bc_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(
            confirmation_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as edit_error:
        # 如果编辑失败，发送新消息
        logger.warning(f"编辑确认消息失败，发送新消息: {edit_error}")
        await context.bot.send_message(
            chat_id=user_id,
            text=confirmation_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def execute_broadcast_send(query, context):
    """执行广播发送"""
    user_id = query.from_user.id
    current_state = broadcast_state.get(user_id, {})
    
    # 获取所有用户列表
    all_user_ids = await get_all_user_ids()
    total_users = len(all_user_ids)
    
    if total_users == 0:
        await query.edit_message_text("❌ 没有找到可发送的用户。")
        return
    
    # 构建广播消息内容
    broadcast_text = current_state['text']
    photo_file_id = current_state.get('photo_file_id')
    buttons = current_state.get('buttons', [])
    
    # 构建按钮
    reply_markup = None
    if buttons:
        keyboard = []
        for button in buttons:
            keyboard.append([InlineKeyboardButton(button['text'], url=button['url'])])
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 显示开始发送消息
    start_message = f"📤 开始发送广播...\n\n📊 目标用户: {total_users} 人"
    progress_message = await query.edit_message_text(start_message)
    
    # 发送统计
    success_count = 0
    failed_count = 0
    failed_users = []
    
    # 每5秒更新一次进度
    last_update_time = get_beijing_time()
    update_interval = 5  # 5秒
    
    for i, target_user_id in enumerate(all_user_ids):
        try:
            if photo_file_id:
                # 发送带图片的广播
                await context.bot.send_photo(
                    chat_id=target_user_id,
                    photo=photo_file_id,
                    caption=broadcast_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                # 发送纯文本广播
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=broadcast_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            failed_users.append(target_user_id)
            logger.error(f"发送广播到用户 {target_user_id} 失败: {e}")
        
        # 每5秒或发送完成时更新进度
        current_time = get_beijing_time()
        if (current_time - last_update_time).total_seconds() >= update_interval or i == total_users - 1:
            progress = i + 1
            percentage = (progress / total_users) * 100
            
            # 计算预计剩余时间
            if progress > 0:
                elapsed_time = (current_time - last_update_time).total_seconds()
                avg_time_per_user = elapsed_time / progress
                remaining_users = total_users - progress
                estimated_remaining = remaining_users * avg_time_per_user
                remaining_minutes = int(estimated_remaining / 60)
                remaining_seconds = int(estimated_remaining % 60)
                time_estimate = f"约{remaining_minutes}分{remaining_seconds}秒" if remaining_minutes > 0 else f"约{remaining_seconds}秒"
            else:
                time_estimate = "计算中..."
            
            progress_text = (
                f"📤 广播发送中...\n\n"
                f"📊 进度: {progress}/{total_users} ({percentage:.1f}%)\n"
                f"✅ 成功: {success_count}\n"
                f"❌ 失败: {failed_count}\n\n"
                f"⏰ 预计剩余时间: {time_estimate}"
            )
            
            try:
                await progress_message.edit_text(progress_text)
                last_update_time = current_time
            except Exception as e:
                logger.error(f"更新进度消息失败: {e}")
                # 如果编辑失败，尝试发送新消息
                try:
                    progress_message = await context.bot.send_message(
                        chat_id=user_id,
                        text=progress_text
                    )
                except Exception as send_error:
                    logger.error(f"发送新进度消息也失败: {send_error}")
        
        # 避免发送过快
        await asyncio.sleep(0.1)
    
    # 发送完成，显示最终结果
    final_text = (
        f"✅ <b>广播发送完成</b>\n\n"
        f"📊 <b>发送结果:</b>\n"
        f"• 总用户: {total_users} 人\n"
        f"• 成功: {success_count} 人\n"
        f"• 失败: {failed_count} 人\n\n"
        f"⏰ 完成时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if failed_users:
        final_text += f"\n\n❌ <b>失败用户ID:</b>\n"
        # 只显示前10个失败用户ID
        display_failed = failed_users[:10]
        final_text += "\n".join([f"• {uid}" for uid in display_failed])
        if len(failed_users) > 10:
            final_text += f"\n• ... 还有 {len(failed_users) - 10} 个用户"
    
    try:
        await progress_message.edit_text(final_text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"更新最终结果失败: {e}")
        # 如果编辑失败，发送新消息
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=final_text,
                parse_mode='HTML'
            )
        except Exception as send_error:
            logger.error(f"发送最终结果消息也失败: {send_error}")
    
    # 清除广播状态
    if user_id in broadcast_state:
        del broadcast_state[user_id]
    
    logger.info(f"广播发送完成: 用户 {user_id}, 成功 {success_count}, 失败 {failed_count}")

# 18. 新增一个通用的文本消息处理器来处理所有主菜单按钮
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一个通用的消息处理器，根据当前语言动态匹配按钮文本"""
    update_activity()  # 更新活动时间
    
    message = update.message
    user_id = message.from_user.id
    text = message.text
    
    # 获取当前用户的语言代码（需要在最前面获取）
    lang_code = user_data.get(user_id, 'zh-CN')
    texts = LANGUAGES[lang_code]
    
    # 检查用户是否在广播编辑状态
    if user_id in broadcast_state:
        current_state = broadcast_state[user_id]
        
        if current_state['step'] == 'editing_text':
            # 处理广播文本设置
            broadcast_state[user_id]['text'] = text
            broadcast_state[user_id]['step'] = 'idle'
            
            await message.reply_text(
                "✅ <b>广播文本设置成功！</b>\n\n"
                "文本已保存，现在返回广播控制面板。",
                parse_mode='HTML'
            )
            
            # 返回广播控制面板
            await show_broadcast_panel(user_id, context)
            return
            
        elif current_state['step'] == 'editing_buttons':
            # 处理广播按钮设置
            if text.lower() in ['无', 'none', '取消', 'cancel']:
                broadcast_state[user_id]['buttons'] = []
            else:
                # 解析按钮配置
                buttons = []
                lines = text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            button_text = parts[0].strip()
                            button_url = parts[1].strip()
                            if button_text and button_url:
                                buttons.append({
                                    'text': button_text,
                                    'url': button_url
                                })
                
                broadcast_state[user_id]['buttons'] = buttons
            
            broadcast_state[user_id]['step'] = 'idle'
            
            button_count = len(broadcast_state[user_id]['buttons'])
            if button_count > 0:
                await message.reply_text(
                    f"✅ <b>广播按钮设置成功！</b>\n\n"
                    f"已设置 {button_count} 个按钮，现在返回广播控制面板。",
                    parse_mode='HTML'
                )
            else:
                await message.reply_text(
                    "✅ <b>广播按钮已清除</b>\n\n"
                    "现在返回广播控制面板。",
                    parse_mode='HTML'
                )
            
            # 返回广播控制面板
            await show_broadcast_panel(user_id, context)
            return
    
    # 检查是否是客服用户
    if user_id in CUSTOMER_SERVICE_USERS:
        # 检查是否是菜单功能按钮
        if text in [texts['menu_self_register'], texts['menu_mainland_user'], texts['menu_overseas_user'], 
                   texts['menu_recharge'], texts['menu_withdraw'], texts['menu_customer_service'], 
                   texts['menu_bidirectional_contact'], texts['menu_change_lang']]:
            # 直接处理菜单按钮，不调用handle_customer_service_message避免递归
            pass  # 继续执行下面的菜单处理逻辑
        else:
            # 非菜单消息，调用客服处理函数
            await handle_customer_service_message(update, context)
            return
    
    # 检查是否在客服会话中
    if user_id in user_customer_service_sessions:
        # 检查是否是结束会话命令
        if text == '/endcs':
            await end_customer_service_session(update, context)
            return
        else:
            # 检查是否是菜单按钮，如果是则先结束会话再处理
            if text in [texts['menu_self_register'], texts['menu_mainland_user'], texts['menu_overseas_user'], 
                       texts['menu_recharge'], texts['menu_withdraw'], texts['menu_customer_service'], 
                       texts['menu_bidirectional_contact'], texts['menu_change_lang']]:
                await end_customer_service_session(update, context)
            else:
                # 转发消息给客服
                await forward_user_message_to_cs(update, context)
                return
    
    # 根据消息文本调用相应的处理器
    if text == texts['menu_self_register']:
        await self_register_handler(update, context)
    elif text == texts['menu_mainland_user']:
        await mainland_user_handler(update, context)
    elif text == texts['menu_overseas_user']:
        await overseas_user_handler(update, context)
    elif text == texts['menu_recharge']: # 招商频道
        await advertising_channel_handler(update, context)
    elif text == texts['menu_withdraw']: # 推单频道
        await promotion_channel_handler(update, context)
    elif text == texts['menu_customer_service']:
        await customer_service(update, context)
    elif text == texts['menu_bidirectional_contact']:
        await start_customer_service_session(update, context)
    elif text == texts['menu_change_lang']:
        await change_language(update, context)
    else:
        # 如果消息不是预期的按钮文本，提供主菜单作为回复
        await message.reply_text(texts['main_menu_prompt'], reply_markup=get_main_menu_keyboard(user_id))

# 19. 主函数：运行机器人
async def main():
    """启动机器人"""
    global session_timeout_task
    
    print("🚀 机器人启动中...")
    print(f"📅 当前时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 初始化Firebase
    print("🔧 初始化Firebase...")
    initialize_firebase()
    
    # 2. 强制恢复数据（重要！）
    print("🔄 恢复访客数据...")
    restore_success = await force_restore_firebase_data()
    
    if restore_success:
        print(f"✅ 数据恢复成功: 总访客={visitor_stats['total_visitors']}")
    else:
        print("⚠️ 数据恢复失败，使用默认值")
    
    # 3. 创建Application
    print("🔧 创建机器人应用...")
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册命令处理器，以便 M 菜单和手动输入命令都能工作
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping_handler))  # 新增ping命令
    application.add_handler(CommandHandler("heartbeat", heartbeat_status_handler))  # 心跳状态检查
    application.add_handler(CommandHandler("test", test_handler))  # 测试命令
    application.add_handler(CommandHandler("performance", performance_handler))  # 性能监控
    application.add_handler(CommandHandler("change_language", change_language))
    application.add_handler(CommandHandler("self_register", self_register_handler))
    application.add_handler(CommandHandler("mainland_user", mainland_user_handler))
    application.add_handler(CommandHandler("overseas_user", overseas_user_handler))
    application.add_handler(CommandHandler("advertising_channel", advertising_channel_handler))
    application.add_handler(CommandHandler("promotion_channel", promotion_channel_handler))
    application.add_handler(CommandHandler("customer_service", customer_service))
    
    # 隐藏的管理员命令（不在菜单中显示）
    application.add_handler(CommandHandler("admin_stats", admin_stats_handler))  # 管理员统计命令
    application.add_handler(CommandHandler("getid", get_user_id_command))  # 获取用户ID命令
    application.add_handler(CommandHandler("cs_config", admin_cs_config_command))  # 查看客服配置命令
    application.add_handler(CommandHandler("set_welcome_image", set_welcome_image_handler))  # 设置欢迎图片
    application.add_handler(CommandHandler("set_register_image", set_register_image_handler))  # 设置注册图片
    application.add_handler(CommandHandler("endcs", end_customer_service_session))  # 结束客服会话
    
    # 广播功能命令（隐藏）
    application.add_handler(CommandHandler("broadcast", broadcast_command_handler))  # 广播命令
    
    # 注册图片消息处理器
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    # 注册一个通用的文本消息处理器来处理所有按钮点击
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # 注册 CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(handle_language_callback, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(handle_image_setting_callback, pattern='^set_img_'))
    application.add_handler(CallbackQueryHandler(handle_broadcast_callback, pattern='^bc_'))

    # 设置 M 菜单中的命令
    await application.bot.set_my_commands([
        BotCommand("start", "启动机器人"),
        BotCommand("ping", "检查机器人状态"),
        BotCommand("heartbeat", "心跳状态检查"),
        BotCommand("change_language", "切换语言"),
        BotCommand("self_register", "自助注册"),
        BotCommand("mainland_user", "大陆用户"),
        BotCommand("overseas_user", "海外用户"),
        BotCommand("advertising_channel", "招商频道"),
        BotCommand("promotion_channel", "推单频道"),
        BotCommand("customer_service", "人工客服"),
        BotCommand("getid", "获取用户ID"),
        # 注意：admin_stats 和 cs_config 命令不在菜单中显示，仅限管理员使用
    ])

    if IS_RENDER and WEB_AVAILABLE:
        # Render环境：使用webhook
        logger.info("🚀 在Render环境中启动，使用webhook模式")
        
        # 创建web应用
        app = web.Application()
        app['bot'] = application.bot
        app['dispatcher'] = application
        
        # 添加路由
        app.router.add_get('/', health_check)
        app.router.add_post(f'/webhook/{BOT_TOKEN}', webhook_handler)
        
        # 初始化Application（webhook模式必需）
        await application.initialize()
        
        # 设置webhook
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook/{BOT_TOKEN}"
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook已设置: {webhook_url}")
        
        # 启动心跳任务（在web服务器启动前）
        print("🔄 准备启动心跳任务...")
        try:
            # 使用asyncio.create_task启动心跳，不阻塞主流程
            heartbeat_task_obj = asyncio.create_task(start_heartbeat(application))
            print("✅ 心跳任务已创建")
        except Exception as e:
            print(f"❌ 心跳任务创建失败: {e}")
            logger.error(f"心跳任务创建失败: {e}")
        
        # 启动会话超时检查任务
        print("🕐 准备启动会话超时检查任务...")
        try:
            session_timeout_task = asyncio.create_task(check_session_timeout(application))
            print("✅ 会话超时检查任务已创建")
        except Exception as e:
            print(f"❌ 会话超时检查任务创建失败: {e}")
            logger.error(f"会话超时检查任务创建失败: {e}")
        
        # 启动web服务器
        await web._run_app(app, host='0.0.0.0', port=PORT)
    else:
        # 本地环境：使用polling
        logger.info("🚀 在本地环境中启动，使用polling模式")
        
        # 启动心跳任务（在polling启动前）
        print("🔄 准备启动心跳任务...")
        try:
            # 使用asyncio.create_task启动心跳，不阻塞主流程
            heartbeat_task_obj = asyncio.create_task(start_heartbeat(application))
            print("✅ 心跳任务已创建")
        except Exception as e:
            print(f"❌ 心跳任务创建失败: {e}")
            logger.error(f"心跳任务创建失败: {e}")
        
        # 启动会话超时检查任务
        print("🕐 准备启动会话超时检查任务...")
        try:
            session_timeout_task = asyncio.create_task(check_session_timeout(application))
            print("✅ 会话超时检查任务已创建")
        except Exception as e:
            print(f"❌ 会话超时检查任务创建失败: {e}")
            logger.error(f"会话超时检查任务创建失败: {e}")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)

async def force_restore_firebase_data():
    """强制从Firebase恢复所有数据"""
    global visitor_stats
    
    if not firebase_initialized or not firebase_db:
        logger.warning("⚠️ Firebase不可用，跳过数据恢复")
        print("⚠️ Firebase不可用，跳过数据恢复")
        return False
    
    try:
        logger.info("🔄 强制恢复Firebase数据...")
        print("🔄 强制恢复Firebase数据...")
        
        # 清空本地数据，强制重新加载
        visitor_stats = {
            'total_visitors': 0,
            'daily_stats': {},
            'unique_visitors': set()
        }
        
        # 先恢复所有日期的数据，收集所有唯一访客
        all_unique_visitors = set()
        
        # 恢复最近30天的数据
        for i in range(30):
            date = (get_beijing_time() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('daily_stats').collection('dates').document(date)
            daily_doc = daily_ref.get()
            
            if daily_doc.exists:
                daily_data = daily_doc.to_dict()
                visitors_list = daily_data.get('visitors', [])
                total_actions = daily_data.get('total_actions', 0)
                
                # 转换为set
                visitors_set = set(visitors_list)
                
                visitor_stats['daily_stats'][date] = {
                    'visitors': visitors_set,
                    'total_actions': total_actions
                }
                
                # 收集所有唯一访客
                all_unique_visitors.update(visitors_set)
                
                logger.info(f"✅ 恢复日期 {date}: {len(visitors_set)} 访客, {total_actions} 操作")
                print(f"✅ 恢复日期 {date}: {len(visitors_set)} 访客, {total_actions} 操作")
        
        # 更新唯一访客集合和总访客数
        visitor_stats['unique_visitors'] = all_unique_visitors
        visitor_stats['total_visitors'] = len(all_unique_visitors)
        
        # 恢复总访客数（如果Firebase中有记录，使用较大的值）
        stats_ref = firebase_db.collection('bots').document(BOT_ID).collection('stats').document('visitor_stats')
        stats_doc = stats_ref.get()
        
        if stats_doc.exists:
            stats_data = stats_doc.to_dict()
            firebase_total = stats_data.get('total_visitors', 0)
            
            # 使用较大的值，确保数据完整性
            if firebase_total > visitor_stats['total_visitors']:
                visitor_stats['total_visitors'] = firebase_total
                logger.info(f"✅ 使用Firebase记录的总访客数: {visitor_stats['total_visitors']}")
                print(f"✅ 使用Firebase记录的总访客数: {visitor_stats['total_visitors']}")
            else:
                logger.info(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
                print(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
        else:
            logger.info(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
            print(f"✅ 使用计算得出的总访客数: {visitor_stats['total_visitors']}")
        
        logger.info(f"✅ 数据恢复完成: 总访客={visitor_stats['total_visitors']}, 唯一访客={len(visitor_stats['unique_visitors'])}")
        print(f"✅ 数据恢复完成: 总访客={visitor_stats['total_visitors']}, 唯一访客={len(visitor_stats['unique_visitors'])}")
        
        return True
        
    except Exception as e:
        error_msg = f"❌ 数据恢复失败: {e}"
        logger.error(error_msg)
        print(error_msg)
        return False

if __name__ == "__main__":
    asyncio.run(main())
