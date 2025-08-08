import logging
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# 1. 设置你的 Bot Token
# 注意：出于安全考虑，强烈建议将 Token 存储在环境变量中，而不是直接写在代码里。
BOT_TOKEN = '8142344692:AAHgq1MQjZ50K445Vh7WhWyopNVWiY1F4PI' 

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
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}招商频道",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}推单频道",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}邀请好友",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}人工客服",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}下载APP",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Language", 
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
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}ช่องทางการโฆษณา",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}ช่องทางโปรโมชั่น",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}เชิญเพื่อน",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}บริการลูกค้า",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}ดาวน์โหลดแอป",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}เปลี่ยนภาษา",
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
        'menu_recharge': f"{BUTTON_EMOJIS['menu_advertising_channel']}Kênh quảng cáo",
        'menu_withdraw': f"{BUTTON_EMOJIS['menu_promotion_channel']}Kênh khuyến mãi",
        'menu_invite_friend': f"{BUTTON_EMOJIS['menu_invite_friend']}Mời bạn bè",
        'menu_customer_service': f"{BUTTON_EMOJIS['menu_customer_service']}Dịch vụ khách hàng",
        'menu_download_app': f"{BUTTON_EMOJIS['menu_download_app']}Tải ứng dụng",
        'menu_change_lang': f"{BUTTON_EMOJIS['menu_change_lang']}Thay đổi ngôn ngữ",
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

# 5. 根据用户的语言获取文本
def get_text(user_id, key):
    """根据用户的语言设置获取相应的文本"""
    lang_code = user_data.get(user_id, 'zh-CN')
    return LANGUAGES.get(lang_code, LANGUAGES['zh-CN']).get(key, key)

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
    user = update.effective_user
    logger.info(f"User {user.first_name} started the bot.")
    user_id = user.id

    if user_id not in user_data:
        user_data[user_id] = 'zh-CN'

    new_welcome_text = (
        f"🎉 嗨，{user.mention_html()}！欢迎来到趣体育⚽️MKsports。我是您的专属服务助手，请在下方选择您需要的服务。\n\n"
        f"📢 招商频道： <a href='https://t.me/QTY18'>https://t.me/QTY18</a>\n"
        f"📢 推单频道： <a href='https://t.me/AISOUOO'>https://t.me/AISOUOO</a>\n\n"
        f"💬 官方客服：\n"
        f"1️⃣ <a href='https://t.me/QTY01'>@QTY01</a>\n"
        f"2️⃣ <a href='https://t.me/QTY15'>@QTY15</a>\n"
        f"3️⃣ <a href='https://t.me/dongba222'>@dongba222</a>"
    )

    await update.message.reply_html(
        new_welcome_text,
        reply_markup=get_main_menu_keyboard(user_id)
    )

# 10. 定义「招商频道」按钮的处理器
async def advertising_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「招商频道」按钮时调用"""
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
    message, user = get_message_and_user(update)
    if not message or not user: return
    user_id = user.id
    prompt_text = get_text(user_id, 'promotion_channel_prompt')
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'menu_withdraw'), url='https://t.me/AISOUOO')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text=prompt_text, reply_markup=reply_markup)

# 12. 定义「人工客服」按钮的处理器
async def customer_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「人工客服」按钮时调用"""
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

# 13. 定义「切换语言」按钮的处理器
async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「切换语言」按钮时调用"""
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

# 15. 定义「大陆用户」按钮的处理器
async def mainland_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """当用户点击「大陆用户」按钮时，发送一个可直接跳转趣体育注册页面的按钮"""
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
def main():
    """启动机器人"""
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册命令处理器，以便 M 菜单和手动输入命令都能工作
    application.add_handler(CommandHandler("start", start))
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
    application.bot.set_my_commands([
        BotCommand("start", "启动机器人"),
        BotCommand("change_language", "切换语言"),
        BotCommand("self_register", "自助注册"),
        BotCommand("mainland_user", "大陆用户"),
        BotCommand("overseas_user", "海外用户"),
        BotCommand("advertising_channel", "招商频道"),
        BotCommand("promotion_channel", "推单频道"),
        BotCommand("customer_service", "人工客服"),
    ])

    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

