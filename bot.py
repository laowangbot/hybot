# bot.py - 修正後的 Telegram 機器人程式碼，使用 FastAPI 框架

import asyncio
import logging
import os
from fastapi import FastAPI, Request, Response
import uvicorn
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# 1. 設定 Bot Token 和 Webhook URL
# 建議將這些值儲存在環境變數中
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8142344692:AAHgq1MQjZ50K445Vh7WhWyopNVWiY1F4PI')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# 2. 啟用日誌記錄
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. 定義遊戲的 URL 和客服句柄
GAME_URL_QU = "https://www.qu32.vip:30011/entry/register/?i_code=6944642"
GAME_URL_MK = "https://www.mk2001.com:9081/CHS"
CS_HANDLE = "@QTY18"

# 定義按鈕的表情符號
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

# 4. 準備多語言文本 (此處省略部分內容，與您提供的保持一致)
LANGUAGES = {
    'zh-CN': {
        'welcome': "欢迎来到 趣体育 {user}，点击下方菜单开始互动。",
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
    },
    'en': {
        # 英文文本...
        'welcome': "Welcome to quSports {user}, click on the menu below to interact.",
        'main_menu_prompt': "Please select an option from the main menu.",
        'menu_account_info': "Register Account",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}Play Game",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}Advertising Channel",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}Promotion Channel",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}Invite Friends",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}Customer Service",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}Download APP",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Change Language",
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
    },
    'th': {
        # 泰文文本...
        'welcome': "ยินดีต้อนรับสู่ quSports {user} คลิกที่เมนูด้านล่างเพื่อโต้ตอบ",
        'main_menu_prompt': "กรุณาเลือกตัวเลือกจากเมนูหลัก",
        'menu_account_info': "ลงทะเบียนบัญชี",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}เข้าสู่เกม",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}ช่องทางการโฆษณา",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}ช่องทางโปรโมชั่น",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}เชิญเพื่อน",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}บริการลูกค้า",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}ดาวน์โหลดแอป",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}เปลี่ยนภาษา",
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
    },
    'vi': {
        # 越南文文本...
        'welcome': "Chào mừng đến với quSports {user}, nhấp vào menu bên dưới để tương tác.",
        'main_menu_prompt': "Vui lòng chọn một tùy chọn từ menu chính.",
        'menu_account_info': "Đăng ký tài khoản",
        'menu_play_game': f"{BUTTON_EMOJIS['menu_play_game']}Vào trò chơi",
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}Kênh quảng cáo",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}Kênh khuyến mãi",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}Mời bạn bè",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}Dịch vụ khách hàng",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}Tải ứng dụng",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Thay đổi ngôn ngữ",
        'menu_self_register': f"{BUTTON_EMOJIS['menu_self_register']}Tự đăng ký",
        'menu_mainland_user': f"{BUTTON_EMOJIS['menu_mainland_user']}Người dùng Trung Quốc đại lục",
        'menu_overseas_user': f"{BUTTON_EMOJIS['menu_overseas_user']}Người dùng toàn cầu",
        'live_customer_service_title': "Vui lòng nhấp vào chuyên viên dịch vụ khách hàng dưới đây để liên hệ:",
        'customer_specialist_1': "Chuyên viên 1",
        'customer_specialist_2': "Chuyên viên 2",
        'customer_specialist_3': "Chuyên viên 3",
        'download_app_info': "Nhấp vào các nút dưới đây để tải ứng dụng:",
        'download_android': "Tải Android",
        'download_ios': "Tải iOS",
        'invite_title': "Mời bạn bè và kiếm tiền cùng nhau!",
        'invite_message': "Bằng cách mời bạn bè đăng ký thông qua liên kết độc quyền của bạn, bạn có thể nhận được phần thưởng phong phú!",
        'invite_link_heading': "Liên kết mời  ",
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
        'register_info_notice_prompt': "Vui lòng nhấp vào nút dưới đây để đăng ký:",
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

# 5. 儲存用戶語言設定的字典
user_data = {}

def get_text(user_id, key):
    """根據用戶的語言設定獲取相應的文本"""
    lang_code = user_data.get(user_id, 'zh-CN')
    return LANGUAGES.get(lang_code, LANGUAGES['zh-CN']).get(key, key)

def get_main_menu_keyboard(user_id):
    """返回主選單的鍵盤佈局"""
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
            KeyboardButton(get_text(user_id, 'menu_recharge')),
            KeyboardButton(get_text(user_id, 'menu_withdraw'))
        ],
        [
            KeyboardButton(get_text(user_id, 'menu_customer_service'))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_language_keyboard():
    """返回語言選擇的內嵌鍵盤"""
    keyboard = [
        [InlineKeyboardButton("简体中文🇨🇳", callback_data='lang_zh-CN')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("ไทย 🇹🇭", callback_data='lang_th')],
        [InlineKeyboardButton("Tiếng Việt 🇻 ", callback_data='lang_vi')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_message_and_user(update: Update):
    """從更新對象中提取消息和用戶對象"""
    if update.message:
        return update.message, update.effective_user
    elif update.callback_query and update.callback_query.message:
        return update.callback_query.message, update.effective_user
    return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶發送 /start 命令時調用"""
    user = update.effective_user
    logger.info(f"User {user.first_name} started the bot.")
    user_id = user.id
    if user_id not in user_data:
        user_data[user_id] = 'zh-CN'
    new_welcome_text = (
        f"🎉 嗨，{user.mention_html()}！歡迎來到趣體育⚽️MKsports。我是您的專屬服務助手，請在下方選擇您需要的服務。\n\n"
        f"📢 招商頻道： <a href='https://t.me/QTY18'>https://t.me/QTY18</a>\n"
        f"📢 推單頻道： <a href='https://t.me/AISOUOO'>https://t.me/AISOUOO</a>\n\n"
        f"💬 官方客服：\n"
        f"1️⃣ <a href='https://t.me/QTY01'>@QTY01</a>\n"
        f"2️⃣ <a href='https://t.me/QTY15'>@QTY15</a>\n"
        f"3️⃣ <a href='https://t.me/dongba222'>@dongba222</a>"
    )
    await update.message.reply_html(
        new_welcome_text,
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def advertising_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「招商頻道」按鈕時調用"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    prompt_text = get_text(user_id, 'advertising_channel_prompt')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'menu_recharge'), url='https://t.me/QTY18')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=prompt_text, reply_markup=reply_markup)

async def promotion_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「推單頻道」按鈕時調用"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    prompt_text = get_text(user_id, 'promotion_channel_prompt')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'menu_withdraw'), url='https://t.me/AISOUOO')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=prompt_text, reply_markup=reply_markup)

async def customer_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「人工客服」按鈕時調用"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    live_cs_title = get_text(user_id, 'live_customer_service_title')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_1'), url='https://t.me/QTY01')],
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_2'), url='https://t.me/QTY15')],
        [InlineKeyboardButton(get_text(user_id, 'customer_specialist_3'), url='https://t.me/dongba222')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_html(text=live_cs_title, reply_markup=reply_markup)

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「切換語言」按鈕或發送 /change_language 命令時調用"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    await message.reply_text(
        get_text(user_id, 'language_selection'),
        reply_markup=get_language_keyboard()
    )

async def self_register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「自助註冊」按鈕時調用"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    message_text = get_text(user_id, 'register_info_download_notice')
    welcome_message = (
        f"🎉 <b>{get_text(user_id, 'register_info_title')}</b>\n\n"
        f"📢 {get_text(user_id, 'register_info_channel1')}： <a href='https://t.me/QTY18'>https://t.me/QTY18</a>\n"
        f"📢 {get_text(user_id, 'register_info_channel2')}： <a href='https://t.me/AISOUOO'>https://t.me/AISOUOO</a>\n\n"
        f"💬 <b>{get_text(user_id, 'menu_customer_service')}</b>：\n"
        f"1️⃣ <a href='https://t.me/QTY01'>@QTY01</a>\n"
        f"2️⃣ <a href='https://t.me/QTY15'>@QTY15</a>\n"
        f"3️⃣ <a href='https://t.me/dongba222'>@dongba222</a>"
    )
    full_message = f"{welcome_message}\n{message_text}"
    await message.reply_html(text=full_message, reply_markup=get_main_menu_keyboard(user_id))

async def mainland_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「大陸用戶」按鈕時，發送註冊連結"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    qu_link_text = get_text(user_id, 'register_info_qu_link_text')
    keyboard = [
        [InlineKeyboardButton(qu_link_text, url=GAME_URL_QU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=get_text(user_id, 'register_info_notice_prompt'), reply_markup=reply_markup)

async def overseas_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """當用戶點擊「海外用戶」按鈕時，發送註冊連結"""
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    mk_link_text = get_text(user_id, 'register_info_mk_link_text')
    keyboard = [
        [InlineKeyboardButton(mk_link_text, url=GAME_URL_MK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=get_text(user_id, 'register_info_notice_prompt'), reply_markup=reply_markup)

async def handle_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理語言選擇內嵌按鈕的點擊事件"""
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

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一個通用的消息處理器，根據按鈕文本觸發對應的處理器"""
    message = update.message
    user_id = message.from_user.id
    text = message.text
    lang_code = user_data.get(user_id, 'zh-CN')
    texts = LANGUAGES[lang_code]
    
    if text == texts['menu_self_register']:
        await self_register_handler(update, context)
    elif text == texts['menu_mainland_user']:
        await mainland_user_handler(update, context)
    elif text == texts['menu_overseas_user']:
        await overseas_user_handler(update, context)
    elif text == texts['menu_recharge']:
        await advertising_channel_handler(update, context)
    elif text == texts['menu_withdraw']:
        await promotion_channel_handler(update, context)
    elif text == texts['menu_customer_service']:
        await customer_service(update, context)
    elif text == texts['menu_change_lang']:
        await change_language(update, context)
    else:
        await message.reply_text(texts['main_menu_prompt'], reply_markup=get_main_menu_keyboard(user_id))

# --- FastAPI 和 Telegram.ext 整合的核心修改部分 ---

# 建立 FastAPI 應用程式
app = FastAPI()

async def main():
    """主非同步函數，負責設定和啟動機器人"""
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL 環境變數未設定。無法以 Webhook 模式運行。")
        return

    # 建立 Telegram Application 實例
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 設置所有的處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change_language", change_language))
    application.add_handler(CommandHandler("self_register", self_register_handler))
    application.add_handler(CommandHandler("mainland_user", mainland_user_handler))
    application.add_handler(CommandHandler("overseas_user", overseas_user_handler))
    application.add_handler(CommandHandler("advertising_channel", advertising_channel_handler))
    application.add_handler(CommandHandler("promotion_channel", promotion_channel_handler))
    application.add_handler(CommandHandler("customer_service", customer_service))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(CallbackQueryHandler(handle_language_callback, pattern='^lang_'))
    logger.info("所有處理器已加載。")

    # 設定 bot 命令
    await application.bot.set_my_commands([
        BotCommand("start", "啟動機器人"),
        BotCommand("change_language", "切換語言"),
        BotCommand("self_register", "自助註冊"),
        BotCommand("mainland_user", "大陸用戶"),
        BotCommand("overseas_user", "海外用戶"),
        BotCommand("advertising_channel", "招商頻道"),
        BotCommand("promotion_channel", "推單頻道"),
        BotCommand("customer_service", "人工客服"),
    ])
    logger.info("機器人命令已設定。")

    # 使用 ptb 內建的 run_webhook 方法，讓它來管理 FastAPI
    port = int(os.environ.get('PORT', 5000))
    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        on_startup=None, # on_startup 參數會在這裡被呼叫
        on_shutdown=None, # on_shutdown 參數會在這裡被呼叫
        webhook_uri=f"/{BOT_TOKEN}"
    )

# 主程式入口
if __name__ == "__main__":
    # 使用 asyncio.run 啟動主非同步函數
    asyncio.run(main())
