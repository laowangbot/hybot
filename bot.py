import logging
import re
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# 添加测试输出
print("🚀 机器人启动中...")
print("📅 当前时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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

# 定义游戏的 URL
GAME_URL_QU = "https://www.qu32.vip:30011/entry/register/?i_code=6944642"
GAME_URL_MK = "https://www.mk2001.com:9081/CHS"
# 定义官方客服的 Telegram 句柄
CS_HANDLE = "@maoyiyule"

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
        'welcome_to_sports': "欢迎来到 qu体育！",
        'official_group_handle': "官方群组： @quyuyule",
        'official_channel_handle': "官方频道： @qu337",
        'customer_service_handle': "官方客服： @maoyiyule",
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
        'customer_specialist_1': "Chuyên viên 1",
        'customer_specialist_2': "Chuyên viên 2",
        'customer_specialist_3': "Chuyên viên 3",
        'download_app_info': "Nhấp vào các nút dưới đây để tải ứng dụng:",
        'download_android': "Tải Android",
        'download_ios': "Tải iOS",
        'invite_title': "Mời bạn bè và kiếm tiền cùng nhau!",
        'invite_message': "Bằng cách mời bạn bè đăng ký thông qua liên kết độc quyền của bạn, bạn có thể nhận được phần thưởng phong phú!",
        'invite_link_heading': "Liên kết mời  ",
        'invite_link_qu': "quSports (người dùng Trung Quốc)\nhttps://www.qu32.vip:30011/entry/register/?i_code=6944642",
        'invite_link_mk': "MK Sports (người dùng toàn cầu)\nhttps://www.mk2001.com:9081/CHS",
        'language_selection': "Vui lòng chọn ngôn ngữ của bạn:",
        'lang_changed': "Đã thay đổi ngôn ngữ thành công!",
        'welcome_to_sports': "Chào mừng đến với quSports!",
        'official_group_handle': "Nhóm chính thức: @quyuyule",
        'official_channel_handle': "Kênh chính thức: @qu337",
        'customer_service_handle': "Dịch vụ khách hàng chính thức: @maoyiyule",
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
    }
}

# 4. 建立一个字典来存储用户语言设置（这只是一个简单的示例，实际应用中应使用数据库）
user_data = {}

# 心跳激活相关变量
last_activity_time = datetime.now()
is_heartbeat_active = False

# 检查是否在Render环境中运行
IS_RENDER = os.environ.get('RENDER', False)

# 5. 根据用户的语言获取文本
def get_text(user_id, key):
    """根据用户的语言设置获取相应的文本"""
    lang_code = user_data.get(user_id, 'zh-CN')
    return LANGUAGES.get(lang_code, LANGUAGES['zh-CN']).get(key, key)

def update_activity():
    """更新最后活动时间"""
    global last_activity_time
    last_activity_time = datetime.now()
    logger.info(f"活动更新: {last_activity_time}")

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
    """心跳任务，每10分钟发送一次心跳信号"""
    global is_heartbeat_active
    
    while True:
        try:
            if is_heartbeat_active:
                # 发送心跳日志
                logger.info(f"💓 心跳信号 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查是否需要发送激活信号
                time_since_last_activity = datetime.now() - last_activity_time
                if time_since_last_activity > timedelta(minutes=10):
                    logger.info("⚠️ 检测到长时间无活动，发送激活信号")
                    # 这里可以添加其他激活逻辑，比如发送webhook请求等
                
            # 等待10分钟
            await asyncio.sleep(600)  # 600秒 = 10分钟
            
        except Exception as e:
            logger.error(f"心跳任务错误: {e}")
            await asyncio.sleep(60)  # 出错时等待1分钟后重试

async def start_heartbeat(application: Application):
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
            KeyboardButton(get_text(user_id, 'menu_customer_service'))
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
    logger.info(f"User {user.first_name} started the bot.")
    user_id = user.id

    if user_id not in user_data:
        user_data[user_id] = 'zh-CN'

    new_welcome_text = (
        f"限时免费赠送活动（30天）\n\n"
        f"🎁 活动福利\n"
        f"注册并充值成功，即获赠老湿永久VIP会员！\n"
        f"✅ 包含13个频道\n"
        f"✅ 超百万部精品视频\n"
        f"💰 价值 368 元 VIP 会员\n\n"
        f"💬 领取方式\n"
        f"注册充值成功后，请立即联系人工客服领取您的专属福利。\n\n"
        f"📢 趣体育官方招商\n"
        f" 👉 https://t.me/QTY18\n\n"
        f"📢 2026世界杯🏆足球篮球推单五大联赛\n"
        f" 👉 https://t.me/SJB33\n\n"
        f"💬 官方客服\n"
        f"1️⃣ @QTY01 (https://t.me/QTY01)\n"
        f"2️⃣ @QTY15 (https://t.me/QTY15)\n"
        f"3️⃣ @QTY04 (https://t.me/QTY04)"
    )

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
    live_cs_title = get_text(user_id, 'live_customer_service_title')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_1'), url='https://t.me/QTY01')],
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_2'), url='https://t.me/QTY15')],
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_3'), url='https://t.me/QTY04')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_html(text=live_cs_title, reply_markup=reply_markup)

# 13. 定义「切换语言」按钮的处理器
async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「切换语言」按钮时调用"""
    update_activity()  # 更新活动时间
    
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    
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
    
    welcome_message = (
        f"✨ <b>官方联盟老湿VIP会员</b> ✨\n"
        f"限时免费赠送活动（30天）\n\n"
        f"🎁 <b>活动福利</b>\n"
        f"注册并充值成功，即获赠老湿永久VIP会员！\n"
        f"✅ 包含13个频道\n"
        f"✅ 超百万部精品视频\n"
        f"💰 价值 368 元 VIP 会员\n\n"
        f"💬 <b>领取方式</b>\n"
        f"注册充值成功后，请立即联系人工客服领取您的专属福利。\n\n"
        f"📢 <b>趣体育官方招商</b>\n"
        f" 👉 https://t.me/QTY18\n\n"
        f"📢 <b>2026世界杯🏆足球篮球推单五大联赛</b>\n"
        f" 👉 https://t.me/SJB33\n\n"
        f"💬 <b>官方客服</b>\n"
        f"1️⃣ <a href='https://t.me/QTY01'>@QTY01</a>\n"
        f"2️⃣ <a href='https://t.me/QTY15'>@QTY15</a>\n"
        f"3️⃣ <a href='https://t.me/QTY04'>@QTY04</a>"
    )
    
    full_message = f"{welcome_message}\n{message_text}"

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

# 18. 新增一个通用的文本消息处理器来处理所有主菜单按钮
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一个通用的消息处理器，根据当前语言动态匹配按钮文本"""
    update_activity()  # 更新活动时间
    
    message = update.message
    user_id = message.from_user.id
    text = message.text
    
    # 获取当前用户的语言代码
    lang_code = user_data.get(user_id, 'zh-CN')
    texts = LANGUAGES[lang_code]
    
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
    elif text == texts['menu_change_lang']:
        await change_language(update, context)
    else:
        # 如果消息不是预期的按钮文本，提供主菜单作为回复
        await message.reply_text(texts['main_menu_prompt'], reply_markup=get_main_menu_keyboard(user_id))

# 19. 主函数：运行机器人
async def main():
    """启动机器人"""
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册命令处理器，以便 M 菜单和手动输入命令都能工作
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping_handler))  # 新增ping命令
    application.add_handler(CommandHandler("change_language", change_language))
    application.add_handler(CommandHandler("self_register", self_register_handler))
    application.add_handler(CommandHandler("mainland_user", mainland_user_handler))
    application.add_handler(CommandHandler("overseas_user", overseas_user_handler))
    application.add_handler(CommandHandler("advertising_channel", advertising_channel_handler))
    application.add_handler(CommandHandler("promotion_channel", promotion_channel_handler))
    application.add_handler(CommandHandler("customer_service", customer_service))
    
    # 注册一个通用的文本消息处理器来处理所有按钮点击
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # 仅为语言切换保留 CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(handle_language_callback, pattern='^lang_'))

    # 设置 M 菜单中的命令
    await application.bot.set_my_commands([
        BotCommand("start", "启动机器人"),
        BotCommand("ping", "检查机器人状态"),
        BotCommand("change_language", "切换语言"),
        BotCommand("self_register", "自助注册"),
        BotCommand("mainland_user", "大陆用户"),
        BotCommand("overseas_user", "海外用户"),
        BotCommand("advertising_channel", "招商频道"),
        BotCommand("promotion_channel", "推单频道"),
        BotCommand("customer_service", "人工客服"),
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
        
        # 启动web服务器
        await web._run_app(app, host='0.0.0.0', port=PORT)
    else:
        # 本地环境：使用polling
        logger.info("🚀 在本地环境中启动，使用polling模式")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
