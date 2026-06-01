import asyncio
import aiohttp
import uuid
import sqlite3
import random
import hashlib
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, BotCommand, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, CONFIG_URL, PREMIUM_URL, ADMIN_ID, SUBGRAM_API_KEY, SUBGRAM_CHECK_URL, PLATEGA_MERCHANT_ID, PLATEGA_SECRET, PLATEGA_API_URL
from utils import (
    bot, send_photo, edit_photo, get_sponsors,
    load_proxies, add_user, get_user_count, get_all_users,
    disable_ads, enable_ads, is_ads_disabled, disable_ads_all, enable_ads_all,
    set_language, get_language, set_plan, get_plan, get_user_joined_date,
    activate_premium, disable_premium, get_premium_until, check_premium_active,
    save_payment_info, get_user_payment_id, get_balance, add_balance, deduct_balance,
    get_referral_code, get_referrer, set_referrer, add_referral_reward, get_referral_stats, get_referral_list,
    set_captcha_passed, is_captcha_passed, disable_expired_premiums_async,
    get_or_create_subscription_token
)

dp = Dispatcher()

# ========== ВСЕ ССЫЛКИ НА КАРТИНКИ (iili.io) ==========
IMAGES = {
    "welcome": "https://iili.io/C3I10Tx.png",
    "subscribe": "https://iili.io/C3I1zhl.png",
    "choosedevice": "https://iili.io/C3IlE9j.jpg",
    "profile": "https://iili.io/C3I0m7a.png",
    "profile_en": "https://iili.io/C3I0iXV.png",
    "documents": "https://iili.io/C3I0dle.png",
    "documents_en": "https://iili.io/C3IlZHG.png",
    "chooserate": "https://iili.io/C3IlNKF.png",
    "chooserate_en": "https://iili.io/C3IlhMP.png",
    "payment": "https://iili.io/C3I08ge.png",
    "payment_en": "https://iili.io/C3I0wzl.png",
    "differences": "https://iili.io/C3IlLSs.png",
    "differences_en": "https://iili.io/C3IlUtp.png",
    "replenish": "https://iili.io/C3I1B7s.jpg",
    "replenish_en": "https://iili.io/C3I1KrX.jpg",
    "referral_program": "https://iili.io/C3I1dLN.jpg",
    "referral_program_en": "https://iili.io/C3I1JXp.jpg",
    "iphone": "https://iili.io/C3I01ft.jpg",
    "android": "https://iili.io/C3Illcu.jpg",
    "laptop": "https://iili.io/C3I0Ggn.jpg",
    "tv": "https://iili.io/C3I1akb.png",
    "notwork": "https://iili.io/C3I0Xef.png",
    "en_notwork": "https://iili.io/C3I0CxV.png",
    "en_subscribe": "https://iili.io/C3I07bR.png",
}

user_data = {}
broadcast_mode = False
pending_broadcast = {}
payment_data = {}
replenish_data = {}
user_replenish_mode = {}

captcha_data = {}

ALL_EMOJIS = [
    "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍒",
    "🥝", "🥥", "🥑", "🍆", "🥔", "🥕", "🌽", "🌶️", "🥒", "🥬",
    "🥦", "🧄", "🧅", "🍄", "🥜", "🌰", "🍞", "🥐", "🥖", "🫓",
    "🥨", "🥯", "🥞", "🧇", "🍖", "🍗", "🥩", "🥓", "🍔", "🍟",
    "🍕", "🌭", "🥪", "🌮", "🌯", "🫔", "🥙", "🧆", "🥚", "🍳",
    "🥘", "🍲", "🫕", "🥣", "🥗", "🍿", "🧈", "🧂", "🥫", "🍱",
    "🍘", "🍙", "🍚", "🍛", "🍜", "🍝", "🍠", "🍢", "🍣", "🍤",
    "🍥", "🥮", "🍡", "🥟", "🥠", "🥡", "🍦", "🍧", "🍨", "🍩",
    "🍪", "🎂", "🍰", "🧁", "🥧", "🍫", "🍬", "🍭", "🍮", "🍯",
    "🥛", "☕", "🍵", "🧃", "🔪", "🔧", "🔨", "🧰", "🔌", "💡",
    "📱", "💻", "🖥️", "⌨️", "🖱️", "📷", "🎥", "📺", "🎮", "🧹",
    "🧺", "🧻", "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑",
    "🚒", "🚜", "🛵", "🚲", "🛴", "🚀", "🛸", "⚓", "⛽", "🚦",
    "🚥", "🗿", "⚱️", "🏺", "⚡", "🐀", "🐶", "🐱", "🐭", "🐹",
    "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸",
    "🐒", "🐔", "🐧", "🐦", "🐤", "🐴", "🐺", "🦋", "🐌", "🐝",
    "🐛", "🦟", "🦗", "🕷️", "🦂", "🐢", "🐍", "🦎", "🐙", "🦑",
    "🦐", "🦞", "🐠", "🐟", "🐡", "🐬", "🐳", "🐋", "🦈", "🐊"
]

TASKS_DB = {
    "🍎": {"ru": "яблоко", "ru_form": "яблока", "en": "apple"},
    "🍐": {"ru": "грушу", "ru_form": "груши", "en": "pear"},
    "🍊": {"ru": "апельсин", "ru_form": "апельсина", "en": "orange"},
    "🍋": {"ru": "лимон", "ru_form": "лимона", "en": "lemon"},
    "🍌": {"ru": "банан", "ru_form": "банана", "en": "banana"},
    "🍉": {"ru": "арбуз", "ru_form": "арбуза", "en": "watermelon"},
    "🍇": {"ru": "виноград", "ru_form": "винограда", "en": "grapes"},
    "🍓": {"ru": "клубнику", "ru_form": "клубники", "en": "strawberry"},
    "🫐": {"ru": "чернику", "ru_form": "черники", "en": "blueberry"},
    "🍒": {"ru": "вишню", "ru_form": "вишни", "en": "cherry"},
    "🥝": {"ru": "киви", "ru_form": "киви", "en": "kiwi"},
    "🥥": {"ru": "кокос", "ru_form": "кокоса", "en": "coconut"},
    "🥑": {"ru": "авокадо", "ru_form": "авокадо", "en": "avocado"},
    "🍆": {"ru": "баклажан", "ru_form": "баклажана", "en": "eggplant"},
    "🥔": {"ru": "картошку", "ru_form": "картошки", "en": "potato"},
    "🥕": {"ru": "морковь", "ru_form": "моркови", "en": "carrot"},
    "🌽": {"ru": "кукурузу", "ru_form": "кукурузы", "en": "corn"},
    "🌶️": {"ru": "перец", "ru_form": "переца", "en": "pepper"},
    "🥒": {"ru": "огурец", "ru_form": "огурца", "en": "cucumber"},
    "🥬": {"ru": "салат", "ru_form": "салата", "en": "lettuce"},
    "🥦": {"ru": "брокколи", "ru_form": "брокколи", "en": "broccoli"},
    "🧄": {"ru": "чеснок", "ru_form": "чеснока", "en": "garlic"},
    "🧅": {"ru": "лук", "ru_form": "лука", "en": "onion"},
    "🍄": {"ru": "гриб", "ru_form": "гриба", "en": "mushroom"},
    "🥜": {"ru": "арахис", "ru_form": "арахиса", "en": "peanut"},
    "🌰": {"ru": "каштан", "ru_form": "каштана", "en": "chestnut"},
    "🍞": {"ru": "хлеб", "ru_form": "хлеба", "en": "bread"},
    "🥐": {"ru": "круассан", "ru_form": "круассана", "en": "croissant"},
    "🥖": {"ru": "багет", "ru_form": "багета", "en": "baguette"},
    "🫓": {"ru": "лаваш", "ru_form": "лаваша", "en": "flatbread"},
    "🥨": {"ru": "крендель", "ru_form": "кренделя", "en": "pretzel"},
    "🥯": {"ru": "бублик", "ru_form": "бублика", "en": "bagel"},
    "🥞": {"ru": "блин", "ru_form": "блина", "en": "pancake"},
    "🧇": {"ru": "вафлю", "ru_form": "вафли", "en": "waffle"},
    "🍖": {"ru": "мясо", "ru_form": "мяса", "en": "meat"},
    "🍗": {"ru": "курицу", "ru_form": "курицы", "en": "chicken"},
    "🥩": {"ru": "стейк", "ru_form": "стейка", "en": "steak"},
    "🥓": {"ru": "бекон", "ru_form": "бекона", "en": "bacon"},
    "🍔": {"ru": "бургер", "ru_form": "бургера", "en": "burger"},
    "🍟": {"ru": "картошку фри", "ru_form": "картошки фри", "en": "fries"},
    "🍕": {"ru": "пиццу", "ru_form": "пиццы", "en": "pizza"},
    "🌭": {"ru": "хот-дог", "ru_form": "хот-дога", "en": "hot dog"},
    "🥪": {"ru": "сэндвич", "ru_form": "сэндвича", "en": "sandwich"},
    "🌮": {"ru": "тако", "ru_form": "тако", "en": "taco"},
    "🌯": {"ru": "буррито", "ru_form": "буррито", "en": "burrito"},
    "🫔": {"ru": "тамале", "ru_form": "тамале", "en": "tamale"},
    "🥙": {"ru": "шаурму", "ru_form": "шаурмы", "en": "shawarma"},
    "🧆": {"ru": "фалафель", "ru_form": "фалафеля", "en": "falafel"},
    "🥚": {"ru": "яйцо", "ru_form": "яйца", "en": "egg"},
    "🍳": {"ru": "яичницу", "ru_form": "яичницы", "en": "fried egg"},
    "🥘": {"ru": "паэлью", "ru_form": "паэльи", "en": "paella"},
    "🍲": {"ru": "суп", "ru_form": "супа", "en": "soup"},
    "🫕": {"ru": "фондю", "ru_form": "фондю", "en": "fondue"},
    "🥣": {"ru": "миску с едой", "ru_form": "миски с едой", "en": "bowl"},
    "🥗": {"ru": "салат", "ru_form": "салата", "en": "salad"},
    "🍿": {"ru": "попкорн", "ru_form": "попкорна", "en": "popcorn"},
    "🧈": {"ru": "масло", "ru_form": "масла", "en": "butter"},
    "🧂": {"ru": "соль", "ru_form": "соли", "en": "salt"},
    "🥫": {"ru": "консервы", "ru_form": "консервов", "en": "canned food"},
    "🍱": {"ru": "бенто", "ru_form": "бенто", "en": "bento"},
    "🍘": {"ru": "рисовый крекер", "ru_form": "рисового крекера", "en": "rice cracker"},
    "🍙": {"ru": "онигири", "ru_form": "онигири", "en": "onigiri"},
    "🍚": {"ru": "рис", "ru_form": "риса", "en": "rice"},
    "🍛": {"ru": "карри", "ru_form": "карри", "en": "curry"},
    "🍜": {"ru": "лапшу", "ru_form": "лапши", "en": "noodles"},
    "🍝": {"ru": "спагетти", "ru_form": "спагетти", "en": "spaghetti"},
    "🍠": {"ru": "батат", "ru_form": "батата", "en": "sweet potato"},
    "🍢": {"ru": "оден", "ru_form": "одена", "en": "oden"},
    "🍣": {"ru": "суши", "ru_form": "суши", "en": "sushi"},
    "🍤": {"ru": "темпуру", "ru_form": "темпуры", "en": "tempura"},
    "🍥": {"ru": "наруто", "ru_form": "наруто", "en": "narutomaki"},
    "🥮": {"ru": "лунный пряник", "ru_form": "лунного пряника", "en": "mooncake"},
    "🍡": {"ru": "данго", "ru_form": "данго", "en": "dango"},
    "🥟": {"ru": "димсам", "ru_form": "димсама", "en": "dumpling"},
    "🥠": {"ru": "печенье с предсказанием", "ru_form": "печенья с предсказанием", "en": "fortune cookie"},
    "🥡": {"ru": "контейнер для еды", "ru_form": "контейнера для еды", "en": "takeout box"},
    "🍦": {"ru": "мороженое", "ru_form": "мороженого", "en": "ice cream"},
    "🍧": {"ru": "ледяную стружку", "ru_form": "ледяной стружки", "en": "shaved ice"},
    "🍨": {"ru": "мороженое в стаканчике", "ru_form": "мороженого в стаканчике", "en": "ice cream cup"},
    "🍩": {"ru": "пончик", "ru_form": "пончика", "en": "doughnut"},
    "🍪": {"ru": "печенье", "ru_form": "печенья", "en": "cookie"},
    "🎂": {"ru": "торт", "ru_form": "торта", "en": "birthday cake"},
    "🍰": {"ru": "кусок торта", "ru_form": "куска торта", "en": "cake slice"},
    "🧁": {"ru": "капкейк", "ru_form": "капкейка", "en": "cupcake"},
    "🥧": {"ru": "пирог", "ru_form": "пирога", "en": "pie"},
    "🍫": {"ru": "шоколад", "ru_form": "шоколада", "en": "chocolate"},
    "🍬": {"ru": "конфету", "ru_form": "конфеты", "en": "candy"},
    "🍭": {"ru": "леденец", "ru_form": "леденца", "en": "lollipop"},
    "🍮": {"ru": "пудинг", "ru_form": "пудинга", "en": "pudding"},
    "🍯": {"ru": "мёд", "ru_form": "мёда", "en": "honey"},
    "🥛": {"ru": "стакан молока", "ru_form": "стакана молока", "en": "glass of milk"},
    "☕": {"ru": "чашку кофе", "ru_form": "чашки кофе", "en": "cup of coffee"},
    "🍵": {"ru": "чашку чая", "ru_form": "чашки чая", "en": "cup of tea"},
    "🧃": {"ru": "сок", "ru_form": "сока", "en": "juice"},
    "🔪": {"ru": "нож", "ru_form": "ножа", "en": "knife"},
    "🔧": {"ru": "гаечный ключ", "ru_form": "гаечного ключа", "en": "wrench"},
    "🔨": {"ru": "молоток", "ru_form": "молотка", "en": "hammer"},
    "🧰": {"ru": "ящик с инструментами", "ru_form": "ящика с инструментами", "en": "toolbox"},
    "🔌": {"ru": "вилку", "ru_form": "вилки", "en": "plug"},
    "💡": {"ru": "лампочку", "ru_form": "лампочки", "en": "light bulb"},
    "📱": {"ru": "телефон", "ru_form": "телефона", "en": "phone"},
    "💻": {"ru": "ноутбук", "ru_form": "ноутбука", "en": "laptop"},
    "🖥️": {"ru": "компьютер", "ru_form": "компьютера", "en": "computer"},
    "⌨️": {"ru": "клавиатуру", "ru_form": "клавиатуры", "en": "keyboard"},
    "🖱️": {"ru": "мышь", "ru_form": "мыши", "en": "mouse"},
    "📷": {"ru": "фотоаппарат", "ru_form": "фотоаппарата", "en": "camera"},
    "🎥": {"ru": "видеокамеру", "ru_form": "видеокамеры", "en": "video camera"},
    "📺": {"ru": "телевизор", "ru_form": "телевизора", "en": "tv"},
    "🎮": {"ru": "игровую приставку", "ru_form": "игровой приставки", "en": "game console"},
    "🧹": {"ru": "метлу", "ru_form": "метлы", "en": "broom"},
    "🧺": {"ru": "корзину", "ru_form": "корзины", "en": "basket"},
    "🧻": {"ru": "рулон бумаги", "ru_form": "рулона бумаги", "en": "toilet paper"},
    "🚗": {"ru": "машину", "ru_form": "машины", "en": "car"},
    "🚕": {"ru": "такси", "ru_form": "такси", "en": "taxi"},
    "🚙": {"ru": "внедорожник", "ru_form": "внедорожника", "en": "suv"},
    "🚌": {"ru": "автобус", "ru_form": "автобуса", "en": "bus"},
    "🚎": {"ru": "троллейбус", "ru_form": "троллейбуса", "en": "trolleybus"},
    "🏎️": {"ru": "гоночную машину", "ru_form": "гоночной машины", "en": "race car"},
    "🚓": {"ru": "полицейскую машину", "ru_form": "полицейской машины", "en": "police car"},
    "🚑": {"ru": "скорую помощь", "ru_form": "скорой помощи", "en": "ambulance"},
    "🚒": {"ru": "пожарную машину", "ru_form": "пожарной машины", "en": "fire truck"},
    "🚜": {"ru": "трактор", "ru_form": "трактора", "en": "tractor"},
    "🛵": {"ru": "мотороллер", "ru_form": "мотороллера", "en": "scooter"},
    "🚲": {"ru": "велосипед", "ru_form": "велосипеда", "en": "bicycle"},
    "🛴": {"ru": "самокат", "ru_form": "самоката", "en": "kick scooter"},
    "🚀": {"ru": "ракету", "ru_form": "ракеты", "en": "rocket"},
    "🛸": {"ru": "НЛО", "ru_form": "НЛО", "en": "ufo"},
    "⚓": {"ru": "якорь", "ru_form": "якоря", "en": "anchor"},
    "⛽": {"ru": "бензоколонку", "ru_form": "бензоколонки", "en": "fuel pump"},
    "🚦": {"ru": "светофор", "ru_form": "светофора", "en": "traffic light"},
    "🚥": {"ru": "светофор горизонтальный", "ru_form": "светофора горизонтального", "en": "horizontal traffic light"},
    "🗿": {"ru": "моаи", "ru_form": "моаи", "en": "moai"},
    "⚱️": {"ru": "погребальную урну", "ru_form": "погребальной урны", "en": "funeral urn"},
    "🏺": {"ru": "амфору", "ru_form": "амфоры", "en": "amphora"},
    "⚡": {"ru": "молнию", "ru_form": "молнии", "en": "lightning"},
    "🐀": {"ru": "крысу", "ru_form": "крысы", "en": "rat"},
    "🐶": {"ru": "собаку", "ru_form": "собаки", "en": "dog"},
    "🐱": {"ru": "кошку", "ru_form": "кошки", "en": "cat"},
    "🐭": {"ru": "мышь", "ru_form": "мыши", "en": "mouse"},
    "🐹": {"ru": "хомяка", "ru_form": "хомяка", "en": "hamster"},
    "🐰": {"ru": "кролика", "ru_form": "кролика", "en": "rabbit"},
    "🦊": {"ru": "лису", "ru_form": "лисы", "en": "fox"},
    "🐻": {"ru": "медведя", "ru_form": "медведя", "en": "bear"},
    "🐼": {"ru": "панду", "ru_form": "панды", "en": "panda"},
    "🐨": {"ru": "коалу", "ru_form": "коалы", "en": "koala"},
    "🐯": {"ru": "тигра", "ru_form": "тигра", "en": "tiger"},
    "🦁": {"ru": "льва", "ru_form": "льва", "en": "lion"},
    "🐮": {"ru": "корову", "ru_form": "коровы", "en": "cow"},
    "🐷": {"ru": "свинью", "ru_form": "свиньи", "en": "pig"},
    "🐸": {"ru": "лягушку", "ru_form": "лягушки", "en": "frog"},
    "🐒": {"ru": "обезьяну", "ru_form": "обезьяны", "en": "monkey"},
    "🐔": {"ru": "курицу", "ru_form": "курицы", "en": "chicken"},
    "🐧": {"ru": "пингвина", "ru_form": "пингвина", "en": "penguin"},
    "🐦": {"ru": "птицу", "ru_form": "птицы", "en": "bird"},
    "🐤": {"ru": "цыплёнка", "ru_form": "цыплёнка", "en": "chick"},
    "🐴": {"ru": "лошадь", "ru_form": "лошади", "en": "horse"},
    "🐺": {"ru": "волка", "ru_form": "волка", "en": "wolf"},
    "🦋": {"ru": "бабочку", "ru_form": "бабочки", "en": "butterfly"},
    "🐌": {"ru": "улитку", "ru_form": "улитки", "en": "snail"},
    "🐝": {"ru": "пчелу", "ru_form": "пчелы", "en": "bee"},
    "🐛": {"ru": "гусеницу", "ru_form": "гусеницы", "en": "caterpillar"},
    "🦟": {"ru": "комара", "ru_form": "комара", "en": "mosquito"},
    "🦗": {"ru": "сверчка", "ru_form": "сверчка", "en": "cricket"},
    "🕷️": {"ru": "паука", "ru_form": "паука", "en": "spider"},
    "🦂": {"ru": "скорпиона", "ru_form": "скорпиона", "en": "scorpion"},
    "🐢": {"ru": "черепаху", "ru_form": "черепахи", "en": "turtle"},
    "🐍": {"ru": "змею", "ru_form": "змеи", "en": "snake"},
    "🦎": {"ru": "ящерицу", "ru_form": "ящерицы", "en": "lizard"},
    "🐙": {"ru": "осьминога", "ru_form": "осьминога", "en": "octopus"},
    "🦑": {"ru": "кальмара", "ru_form": "кальмара", "en": "squid"},
    "🦐": {"ru": "креветку", "ru_form": "креветки", "en": "shrimp"},
    "🦞": {"ru": "лобстера", "ru_form": "лобстера", "en": "lobster"},
    "🐠": {"ru": "рыбку", "ru_form": "рыбки", "en": "tropical fish"},
    "🐟": {"ru": "рыбу", "ru_form": "рыбы", "en": "fish"},
    "🐡": {"ru": "рыбу фугу", "ru_form": "рыбы фугу", "en": "blowfish"},
    "🐬": {"ru": "дельфина", "ru_form": "дельфина", "en": "dolphin"},
    "🐳": {"ru": "кита", "ru_form": "кита", "en": "whale"},
    "🐋": {"ru": "кита", "ru_form": "кита", "en": "whale"},
    "🦈": {"ru": "акулу", "ru_form": "акулы", "en": "shark"},
    "🐊": {"ru": "крокодила", "ru_form": "крокодила", "en": "crocodile"}
}

HEART_MESSAGE_EFFECT_ID = "5159385139981059251"

ROCKET_EMOJI_ID = "6005570495603282482"
HELP_EMOJI_ID = "5775887550262546277"
SATELLITE_EMOJI_ID = "5931472654660800739"
STREAM_EMOJI_ID = "5994750571041525522"
BOLT_EMOJI_ID = "5935795874251674052"
LOCK_EMOJI_ID = "5879895758202735862"
UNLOCK_EMOJI_ID = "6034962180875490251"
CHECK_EMOJI_ID = "5825794181183836432"
WARNING_EMOJI_ID = "5881702736843511327"
CLICK_EMOJI_ID = "5888645706096319818"
NUMBER_1_ID = "5794182096603847292"
NUMBER_2_ID = "5794303034292968945"
NUMBER_3_ID = "5794031944547178894"
STATS_EMOJI_ID = "5994378914636500516"
MAIL_EMOJI_ID = "5771695636411847302"
QUESTION_EMOJI_ID = "5884510167986343350"
CHECK_MARK_EMOJI_ID = "5776375003280838798"
CROSS_EMOJI_ID = "5778527486270770928"
BROADCAST_START_EMOJI_ID = "5771868281212245617"
MANUAL_EMOJI_ID = "5956561916573782596"
URL_EMOJI_ID = "6021344879689341042"
HELP_WARNING_EMOJI_ID = "6019508188464814176"
HELP_SATELLITE_EMOJI_ID = "5933629020301169337"
CLICK_DOWN_EMOJI_ID = "6030400221232501136"
IPHONE_EMOJI_ID = "5818920837645867167"
ANDROID_EMOJI_ID = "5819078828017849357"
MACOS_EMOJI_ID = "6019118553326689234"
WINDOWS_EMOJI_ID = "5818956713507689486"
ANDROIDTV_EMOJI_ID = "6019110203910265775"
HOME_EMOJI_ID = "6042137469204303531"
LANG_EMOJI_ID = "5776233299424843260"
USA_EMOJI_ID = "5202021044105257611"
RUS_EMOJI_ID = "5449408995691341691"
HEART_EMOJI_ID = "6023852792697854544"
SIGNAL_EMOJI_ID = "6021472208289799416"
DONATE_EMOJI_ID = "6030462253445160459"
KEY_EMOJI_ID = "6005570495603282482"
WARNING_NEW_EMOJI_ID = "5775887550262546277"
SIGNAL_NEW_EMOJI_ID = "5931472654660800739"
TECH_SUPPORT_EMOJI_ID = "6021798595739523148"
ID_CARD_EMOJI_ID = "6039630677182254664"
MAN_EMOJI_ID = "5904630315946611415"
MONEY_EMOJI_ID = "6030462253445160459"
LOCK_DOC_EMOJI_ID = "5778570255555105942"
NOTE_EMOJI_ID = "6006038041448156880"
ID_SYMBOL_EMOJI_ID = "5884366771913233289"
HOURGLASS_EMOJI_ID = "5983150113483134607"
ENVELOPE_EMOJI_ID = "6028435952299413210"
CLICK_DOWN_NEW_EMOJI_ID = "6023566962624306038"
FREE_EMOJI_ID = "6032644646587338669"
CROWN_EMOJI_ID = "6021428854889913572"
QUESTION_ABOUT_EMOJI_ID = "6030848053177486888"
CHECK_EMOJI_NEW_ID = "5774022692642492953"
RELOAD_EMOJI_ID = "5116468787377341336"
MONEY_FLY_EMOJI_ID = "5890848474563352982"
GLOBE_EMOJI_ID = "5776233299424843260"
MONEY_BAG_EMOJI_ID = "5904462880941545555"
ID_CARD_PAY_EMOJI_ID = "5884366771913233289"
CLICK_PAY_EMOJI_ID = "6023566962624306038"
HOURGLASS_PAY_EMOJI_ID = "5116468787377341336"
CARD_EMOJI_ID = "5386752951920393980"
CHECK_PAY_EMOJI_ID = "5825794181183836432"
CROSS_PAY_EMOJI_ID = "5774077015388852135"
CHECK_OK_EMOJI_ID = "5774022692642492953"
PEOPLE_EMOJI_ID = "6034969813032374911"
GIFT_EMOJI_ID = "5291747463584062848"
DOLLAR_EMOJI_ID = "5386752951920393980"
TOPUP_EMOJI_ID = "5890848474563352982"
LINK_EMOJI_ID = "6021344879689341042"
PARTY_EMOJI_ID = "6041731551845159060"
CROWN_NEW_EMOJI_ID = "6021428854889913572"
NEW_USER_EMOJI_ID = "6033108709213736873"
REFERRAL_EMOJI_ID = "5994453058656931434"
REFERRAL_LIST_EMOJI_ID = "6021435576513730578"
SHARE_EMOJI_ID = "6039519841256214245"


def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


STREAM = emoji(STREAM_EMOJI_ID, "👋")
ROCKET = emoji(ROCKET_EMOJI_ID, "🚀")
BOLT = emoji(BOLT_EMOJI_ID, "⚡")
LOCK = emoji(LOCK_EMOJI_ID, "🔒")
UNLOCK = emoji(UNLOCK_EMOJI_ID, "🔓")
CHECK = emoji(CHECK_EMOJI_ID, "✅")
HELP_EMOJI = emoji(HELP_EMOJI_ID, "🆘")
SATELLITE = emoji(SATELLITE_EMOJI_ID, "📡")
WARNING = emoji(WARNING_EMOJI_ID, "⚠️")
CLICK = emoji(CLICK_EMOJI_ID, "👇")
NUMBER_1 = emoji(NUMBER_1_ID, "1️⃣")
NUMBER_2 = emoji(NUMBER_2_ID, "2️⃣")
NUMBER_3 = emoji(NUMBER_3_ID, "3️⃣")
STATS = emoji(STATS_EMOJI_ID, "📊")
MAIL = emoji(MAIL_EMOJI_ID, "📢")
QUESTION_EMOJI = emoji(QUESTION_EMOJI_ID, "❓")
CHECK_MARK = emoji(CHECK_MARK_EMOJI_ID, "✅")
CROSS = emoji(CROSS_EMOJI_ID, "❌")
BROADCAST_START = emoji(BROADCAST_START_EMOJI_ID, "📢")
MANUAL = emoji(MANUAL_EMOJI_ID, "📝")
URL = emoji(URL_EMOJI_ID, "🔗")
HELP_WARNING = emoji(HELP_WARNING_EMOJI_ID, "⚠️")
HELP_SATELLITE = emoji(HELP_SATELLITE_EMOJI_ID, "📡")
CLICK_DOWN = emoji(CLICK_DOWN_EMOJI_ID, "👇")
IPHONE = emoji(IPHONE_EMOJI_ID, "🍏")
ANDROID = emoji(ANDROID_EMOJI_ID, "🤖")
MACOS = emoji(MACOS_EMOJI_ID, "😊")
WINDOWS = emoji(WINDOWS_EMOJI_ID, "🌐")
ANDROIDTV = emoji(ANDROIDTV_EMOJI_ID, "📺")
HOME = emoji(HOME_EMOJI_ID, "🏠")
LANG = emoji(LANG_EMOJI_ID, "🌐")
USA = emoji(USA_EMOJI_ID, "🇺🇸")
RUS = emoji(RUS_EMOJI_ID, "🇷🇺")
HEART = emoji(HEART_EMOJI_ID, "❤️")
SIGNAL = emoji(SIGNAL_EMOJI_ID, "📶")
DONATE = emoji(DONATE_EMOJI_ID, "💰")
KEY = emoji(KEY_EMOJI_ID, "🔑")
WARNING_NEW = emoji(WARNING_NEW_EMOJI_ID, "⚠️")
SIGNAL_NEW = emoji(SIGNAL_NEW_EMOJI_ID, "📶")
TECH_SUPPORT = emoji(TECH_SUPPORT_EMOJI_ID, "👨‍💻")
ID_CARD = emoji(ID_CARD_EMOJI_ID, "🪪")
MAN = emoji(MAN_EMOJI_ID, "👨")
MONEY = emoji(MONEY_EMOJI_ID, "💰")
LOCK_DOC = emoji(LOCK_DOC_EMOJI_ID, "🔒")
NOTE = emoji(NOTE_EMOJI_ID, "📝")
ID_SYMBOL = emoji(ID_SYMBOL_EMOJI_ID, "🆔")
HOURGLASS = emoji(HOURGLASS_EMOJI_ID, "⏳")
ENVELOPE = emoji(ENVELOPE_EMOJI_ID, "💌")
CLICK_DOWN_NEW = emoji(CLICK_DOWN_NEW_EMOJI_ID, "👇")
FREE = emoji(FREE_EMOJI_ID, "🆓")
CROWN = emoji(CROWN_EMOJI_ID, "👑")
QUESTION_ABOUT = emoji(QUESTION_ABOUT_EMOJI_ID, "❓")
CHECK_NEW = emoji(CHECK_EMOJI_NEW_ID, "✅")
RELOAD = emoji(RELOAD_EMOJI_ID, "⏳")
MONEY_FLY = emoji(MONEY_FLY_EMOJI_ID, "💸")
GLOBE = emoji(GLOBE_EMOJI_ID, "🌐")
MONEY_BAG = emoji(MONEY_BAG_EMOJI_ID, "💰")
ID_CARD_PAY = emoji(ID_CARD_PAY_EMOJI_ID, "🆔")
CLICK_PAY = emoji(CLICK_PAY_EMOJI_ID, "👇")
HOURGLASS_PAY = emoji(HOURGLASS_PAY_EMOJI_ID, "⏳")
CARD = emoji(CARD_EMOJI_ID, "💳")
CHECK_PAY = emoji(CHECK_PAY_EMOJI_ID, "✅")
CROSS_PAY = emoji(CROSS_PAY_EMOJI_ID, "❌")
CHECK_OK = emoji(CHECK_OK_EMOJI_ID, "✔")
PEOPLE = emoji(PEOPLE_EMOJI_ID, "👥")
GIFT = emoji(GIFT_EMOJI_ID, "🎁")
DOLLAR = emoji(DOLLAR_EMOJI_ID, "💵")
TOPUP = emoji(TOPUP_EMOJI_ID, "💳")
LINK = emoji(LINK_EMOJI_ID, "🔗")
PARTY = emoji(PARTY_EMOJI_ID, "🎉")
CROWN_NEW = emoji(CROWN_NEW_EMOJI_ID, "👑")
NEW_USER = emoji(NEW_USER_EMOJI_ID, "👨")
REFERRAL = emoji(REFERRAL_EMOJI_ID, "🤝")
REFERRAL_LIST = emoji(REFERRAL_LIST_EMOJI_ID, "📋")
SHARE = emoji(SHARE_EMOJI_ID, "🔗")

DOWNLOAD_LINKS = {
    "iphone": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973",
    "android": "https://play.google.com/store/apps/details?id=com.happproxy",
    "macos": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973",
    "windows": "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe",
    "androidtv": "https://play.google.com/store/apps/details?id=com.happproxy"
}


def generate_short_transaction_id() -> str:
    return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:8]


async def premium_expiry_checker():
    while True:
        try:
            await asyncio.sleep(1800)
            await disable_expired_premiums_async()
        except Exception as e:
            print(f"[ERROR] Premium checker error: {e}")


async def set_all_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Menu"),
        BotCommand(command="language", description="Change language"),
    ])
    await bot.set_my_commands([
        BotCommand(command="start", description="Menu"),
        BotCommand(command="language", description="Change language"),
    ], language_code="en")
    await bot.set_my_commands([
        BotCommand(command="start", description="Меню"),
        BotCommand(command="language", description="Сменить язык"),
    ], language_code="ru")


async def get_welcome_text(language: str):
    if language == "ru":
        return (f"{STREAM} <b>Добро пожаловать в StreamNet VPN!</b>\n\n"
                f"<i>Мы помогаем получить быстрый, безопасный и свободный доступ к интернету — <b>совершенно бесплатно</b>.</i>\n\n"
                f"{BOLT} <u>Высокая скорость</u>\n"
                f"{SIGNAL} <u>Обход Белых списков</u>\n"
                f"{LOCK} <u>Полная конфиденциальность без логов</u>\n"
                f"{CHECK} <u>Доступ к сайтам и сервисам без ограничений</u>\n\n"
                f"{CLICK} <b>Нажмите кнопку ниже, чтобы начать.</b>")
    else:
        return (f"{STREAM} <b>Welcome to StreamNet VPN!</b>\n\n"
                f"<i>We help you get fast, secure and free access to the internet — <b>completely free</b>.</i>\n\n"
                f"{BOLT} <u>High speed</u>\n"
                f"{SIGNAL} <u>Bypassing Whitelists</u>\n"
                f"{LOCK} <u>Full privacy, no logs</u>\n"
                f"{CHECK} <u>Unlimited access to websites and services</u>\n\n"
                f"{CLICK} <b>Click the button below to get started.</b>")


async def get_language_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="English", callback_data="lang_en", style="primary", icon_custom_emoji_id=USA_EMOJI_ID),
        InlineKeyboardButton(text="Русский", callback_data="lang_ru", style="primary", icon_custom_emoji_id=RUS_EMOJI_ID)
    )
    return builder.as_markup()


async def get_main_menu_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(InlineKeyboardButton(text="Подключиться", callback_data="connect", style="success", icon_custom_emoji_id=KEY_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="Пополнить баланс", callback_data="replenish_balance", style="default", icon_custom_emoji_id=TOPUP_EMOJI_ID))
        builder.row(
            InlineKeyboardButton(text="О боте", callback_data="about_bot", style="primary", icon_custom_emoji_id=QUESTION_ABOUT_EMOJI_ID),
            InlineKeyboardButton(text="Профиль", callback_data="profile", style="primary", icon_custom_emoji_id=MAN_EMOJI_ID)
        )
        builder.row(InlineKeyboardButton(text="Реферальная программа", callback_data="referral", style="default", icon_custom_emoji_id=REFERRAL_EMOJI_ID))
        builder.row(
            InlineKeyboardButton(text="Не работает", callback_data="help_vpn", style="danger", icon_custom_emoji_id=WARNING_NEW_EMOJI_ID),
            InlineKeyboardButton(text="Прокси", url="https://t.me/proxy?server=proxy.streamnetvpn.top&port=444&secret=d31b30f9e0d6b6c85c42936d6c5930aa", style="danger", icon_custom_emoji_id=SIGNAL_NEW_EMOJI_ID)
        )
        builder.row(InlineKeyboardButton(text="Поддержать проект", url="https://pay.cloudtips.ru/p/8eeb8506", style="default", icon_custom_emoji_id=MONEY_EMOJI_ID))
    else:
        builder.row(InlineKeyboardButton(text="Connect", callback_data="connect", style="success", icon_custom_emoji_id=KEY_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="Top up balance", callback_data="replenish_balance", style="default", icon_custom_emoji_id=TOPUP_EMOJI_ID))
        builder.row(
            InlineKeyboardButton(text="About bot", callback_data="about_bot", style="primary", icon_custom_emoji_id=QUESTION_ABOUT_EMOJI_ID),
            InlineKeyboardButton(text="Profile", callback_data="profile", style="primary", icon_custom_emoji_id=MAN_EMOJI_ID)
        )
        builder.row(InlineKeyboardButton(text="Referral program", callback_data="referral", style="default", icon_custom_emoji_id=REFERRAL_EMOJI_ID))
        builder.row(
            InlineKeyboardButton(text="Not working", callback_data="help_vpn", style="danger", icon_custom_emoji_id=WARNING_NEW_EMOJI_ID),
            InlineKeyboardButton(text="Proxy", url="https://t.me/proxy?server=proxy.streamnetvpn.top&port=444&secret=d31b30f9e0d6b6c85c42936d6c5930aa", style="danger", icon_custom_emoji_id=SIGNAL_NEW_EMOJI_ID)
        )
        builder.row(InlineKeyboardButton(text="Support the project", url="https://pay.cloudtips.ru/p/8eeb8506", style="default", icon_custom_emoji_id=MONEY_EMOJI_ID))
    return builder.as_markup()


async def get_about_bot_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Тех. поддержка" if language == "ru" else "Tech support", url="https://t.me/StreamNetAdmin", style="primary", icon_custom_emoji_id=TECH_SUPPORT_EMOJI_ID))
    builder.row(
        InlineKeyboardButton(text="Политика" if language == "ru" else "Privacy policy", url="https://telegra.ph/Politika-konfidencialnosti-04-01-26", style="primary", icon_custom_emoji_id=LOCK_DOC_EMOJI_ID),
        InlineKeyboardButton(text="Оферта" if language == "ru" else "Terms of service", url="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19", style="primary", icon_custom_emoji_id=NOTE_EMOJI_ID)
    )
    builder.row(InlineKeyboardButton(text="« Назад" if language == "ru" else "« Back", callback_data="back_to_menu", style="default"))
    return builder.as_markup()


async def get_back_keyboard(language: str, back_callback: str = "back_to_menu", show_home: bool = False):
    builder = InlineKeyboardBuilder()
    if show_home:
        if language == "ru":
            builder.row(
                InlineKeyboardButton(text="« Назад", callback_data=back_callback, style="default"),
                InlineKeyboardButton(text="Меню", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
            )
        else:
            builder.row(
                InlineKeyboardButton(text="« Back", callback_data=back_callback, style="default"),
                InlineKeyboardButton(text="Menu", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
            )
    else:
        builder.row(InlineKeyboardButton(text="« Назад" if language == "ru" else "« Back", callback_data=back_callback, style="default"))
    return builder.as_markup()


async def get_choose_device_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="IPhone", callback_data="device_iphone", style="primary", icon_custom_emoji_id=IPHONE_EMOJI_ID),
        InlineKeyboardButton(text="Android", callback_data="device_android", style="primary", icon_custom_emoji_id=ANDROID_EMOJI_ID)
    )
    builder.row(
        InlineKeyboardButton(text="MacOS", callback_data="device_macos", style="primary", icon_custom_emoji_id=MACOS_EMOJI_ID),
        InlineKeyboardButton(text="Windows", callback_data="device_windows", style="primary", icon_custom_emoji_id=WINDOWS_EMOJI_ID)
    )
    builder.row(InlineKeyboardButton(text="AndroidTV", callback_data="device_androidtv", style="primary", icon_custom_emoji_id=ANDROIDTV_EMOJI_ID))
    if language == "ru":
        builder.row(
            InlineKeyboardButton(text="« Назад", callback_data="back_to_rate_select", style="default"),
            InlineKeyboardButton(text="Меню", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
        )
    else:
        builder.row(
            InlineKeyboardButton(text="« Back", callback_data="back_to_rate_select", style="default"),
            InlineKeyboardButton(text="Menu", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
        )
    return builder.as_markup()


async def get_choose_plan_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(InlineKeyboardButton(text="Бесплатный", callback_data="plan_free", style="success", icon_custom_emoji_id=FREE_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="Премиум", callback_data="plan_premium", style="danger", icon_custom_emoji_id=CROWN_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="Отличия тарифов", callback_data="plan_differences", style="primary", icon_custom_emoji_id=PEOPLE_EMOJI_ID))
        builder.row(
            InlineKeyboardButton(text="« Назад", callback_data="back_to_menu", style="default"),
            InlineKeyboardButton(text="Меню", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
        )
    else:
        builder.row(InlineKeyboardButton(text="Free", callback_data="plan_free", style="success", icon_custom_emoji_id=FREE_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="Premium", callback_data="plan_premium", style="danger", icon_custom_emoji_id=CROWN_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="Plan differences", callback_data="plan_differences", style="primary", icon_custom_emoji_id=PEOPLE_EMOJI_ID))
        builder.row(
            InlineKeyboardButton(text="« Back", callback_data="back_to_menu", style="default"),
            InlineKeyboardButton(text="Menu", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
        )
    return builder.as_markup()


async def get_payment_keyboard(language: str, payment_url: str, paid: bool = False, is_replenish: bool = False, transaction_id: str = None):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        if paid:
            if is_replenish:
                builder.row(InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_replenish_{transaction_id}", style="success"))
        else:
            builder.row(InlineKeyboardButton(text="Оплатить", url=payment_url, style="primary", icon_custom_emoji_id=CARD_EMOJI_ID))
            builder.row(InlineKeyboardButton(text="Проверить платёж", callback_data=f"check_replenish_{transaction_id}", style="success", icon_custom_emoji_id=CHECK_PAY_EMOJI_ID))
            builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_payment", style="danger", icon_custom_emoji_id=CROSS_PAY_EMOJI_ID))
    else:
        if paid:
            if is_replenish:
                builder.row(InlineKeyboardButton(text="Confirm", callback_data=f"confirm_replenish_{transaction_id}", style="success"))
        else:
            builder.row(InlineKeyboardButton(text="Pay", url=payment_url, style="primary", icon_custom_emoji_id=CARD_EMOJI_ID))
            builder.row(InlineKeyboardButton(text="Check payment", callback_data=f"check_replenish_{transaction_id}", style="success", icon_custom_emoji_id=CHECK_PAY_EMOJI_ID))
            builder.row(InlineKeyboardButton(text="Cancel", callback_data="cancel_payment", style="danger", icon_custom_emoji_id=CROSS_PAY_EMOJI_ID))
    return builder.as_markup()


async def get_premium_payment_keyboard(language: str, transaction_id: str, paid: bool = False):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        if paid:
            builder.row(InlineKeyboardButton(text="Активировать премиум", callback_data=f"activate_premium_internal_{transaction_id}", style="success", icon_custom_emoji_id=CROWN_EMOJI_ID))
        else:
            builder.row(InlineKeyboardButton(text="Оплатить", callback_data=f"pay_premium_from_balance_{transaction_id}", style="success", icon_custom_emoji_id=CARD_EMOJI_ID))
            builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_premium_payment", style="danger", icon_custom_emoji_id=CROSS_PAY_EMOJI_ID))
    else:
        if paid:
            builder.row(InlineKeyboardButton(text="Activate premium", callback_data=f"activate_premium_internal_{transaction_id}", style="success", icon_custom_emoji_id=CROWN_EMOJI_ID))
        else:
            builder.row(InlineKeyboardButton(text="Pay", callback_data=f"pay_premium_from_balance_{transaction_id}", style="success", icon_custom_emoji_id=CARD_EMOJI_ID))
            builder.row(InlineKeyboardButton(text="Cancel", callback_data="cancel_premium_payment", style="danger", icon_custom_emoji_id=CROSS_PAY_EMOJI_ID))
    return builder.as_markup()


async def get_replenish_amount_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отмена" if language == "ru" else "Cancel", callback_data="cancel_replenish", style="danger", icon_custom_emoji_id=CROSS_PAY_EMOJI_ID))
    return builder.as_markup()


async def get_replenish_payment_text(language: str, amount: int, transaction_id: str, paid: bool = False):
    if language == "ru":
        if paid:
            return (f"{MONEY_FLY} <b>Ваш счет для пополнения баланса успешно оплачен</b>\n\n"
                    f"{GLOBE} <b>Провайдер:</b> Platega\n\n"
                    f"{MONEY_BAG} <b>Сумма пополнения:</b> <code>{amount} RUB</code>\n"
                    f"{ID_CARD_PAY} <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
                    f"{CHECK_OK} <b>Платёж подтверждён!</b>")
        else:
            return (f"{MONEY_FLY} <b>Ваш счет для пополнения баланса успешно создан</b>\n\n"
                    f"{GLOBE} <b>Провайдер:</b> Platega\n\n"
                    f"{MONEY_BAG} <b>Сумма пополнения:</b> <code>{amount} RUB</code>\n"
                    f"{ID_CARD_PAY} <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
                    f"{CLICK_PAY} <b>Нажмите</b> «Оплатить» <b>для перехода к оплате</b>\n\n"
                    f"{HOURGLASS_PAY} <b>Ожидаем оплату...</b>")
    else:
        if paid:
            return (f"{MONEY_FLY} <b>Your balance recharge invoice has been paid</b>\n\n"
                    f"{GLOBE} <b>Provider:</b> Platega\n\n"
                    f"{MONEY_BAG} <b>Recharge amount:</b> <code>{amount} RUB</code>\n"
                    f"{ID_CARD_PAY} <b>Transaction ID:</b> <code>{transaction_id}</code>\n\n"
                    f"{CHECK_OK} <b>Payment confirmed!</b>")
        else:
            return (f"{MONEY_FLY} <b>Your balance recharge invoice has been created</b>\n\n"
                    f"{GLOBE} <b>Provider:</b> Platega\n\n"
                    f"{MONEY_BAG} <b>Recharge amount:</b> <code>{amount} RUB</code>\n"
                    f"{ID_CARD_PAY} <b>Transaction ID:</b> <code>{transaction_id}</code>\n\n"
                    f"{CLICK_PAY} <b>Click</b> «Pay» <b>to proceed to payment</b>\n\n"
                    f"{HOURGLASS_PAY} <b>Waiting for payment...</b>")


async def get_device_instruction_text(device, language: str, plan: str = 'free', user_id: int = None, config_url: str = None):
    if config_url is None:
        if plan == 'premium':
            token = get_or_create_subscription_token(user_id)
            config_url = f"https://streamnetvpn.bothost.tech/sub/{token}"
        else:
            config_url = CONFIG_URL
    device_emojis = {"iphone": IPHONE, "android": ANDROID, "macos": MACOS, "windows": WINDOWS, "androidtv": ANDROIDTV}
    device_names = {"iphone": "IPhone", "android": "Android", "macos": "MacOS", "windows": "Windows", "androidtv": "AndroidTV"}
    device_emoji = device_emojis.get(device, IPHONE)
    device_name = device_names.get(device, "IPhone")

    if language == "ru":
        return (f"<b>Инструкция для</b> {device_emoji} <b>{device_name}:</b>\n\n"
                f"{NUMBER_1} <b>- Скачать</b>\n"
                f"{NUMBER_2} <b>- Подключиться</b>\n\n"
                f"{WARNING} <b>Если не удаётся подключиться:</b>\n"
                f"<blockquote>Скопируйте ключ ниже, перейдите в Happ и нажмите «Из буфера»</blockquote>\n\n"
                f"{ROCKET} <b>Ключ для ручного подключения:</b> <code>{config_url}</code>")
    else:
        return (f"<b>Instructions for</b> {device_emoji} <b>{device_name}:</b>\n\n"
                f"{NUMBER_1} <b>- Download</b>\n"
                f"{NUMBER_2} <b>- Connect</b>\n\n"
                f"{WARNING} <b>If connection fails:</b>\n"
                f"<blockquote>Copy the key below, go to Happ and press «From buffer»</blockquote>\n\n"
                f"{ROCKET} <b>Key for manual connection:</b> <code>{config_url}</code>")


async def get_device_instruction_keyboard(device, language: str, plan: str = 'free', user_id: int = None, config_url: str = None):
    if config_url is None:
        if plan == 'premium':
            token = get_or_create_subscription_token(user_id)
            config_url = f"https://streamnetvpn.bothost.tech/sub/{token}"
        else:
            config_url = CONFIG_URL
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(
            InlineKeyboardButton(text="Скачать", url=DOWNLOAD_LINKS.get(device, DOWNLOAD_LINKS["iphone"]), style="primary", icon_custom_emoji_id=NUMBER_1_ID),
            InlineKeyboardButton(text="Подключиться", url=config_url, style="success", icon_custom_emoji_id=NUMBER_2_ID)
        )
        builder.row(
            InlineKeyboardButton(text="« Назад", callback_data="back_to_device_select", style="default"),
            InlineKeyboardButton(text="Меню", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
        )
    else:
        builder.row(
            InlineKeyboardButton(text="Download", url=DOWNLOAD_LINKS.get(device, DOWNLOAD_LINKS["iphone"]), style="primary", icon_custom_emoji_id=NUMBER_1_ID),
            InlineKeyboardButton(text="Connect", url=config_url, style="success", icon_custom_emoji_id=NUMBER_2_ID)
        )
        builder.row(
            InlineKeyboardButton(text="« Back", callback_data="back_to_device_select", style="default"),
            InlineKeyboardButton(text="Menu", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID)
        )
    return builder.as_markup()


def get_cancel_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отмена" if language == "ru" else "Cancel", callback_data="cancel_broadcast", style="danger", icon_custom_emoji_id=CROSS_EMOJI_ID))
    return builder.as_markup()


def get_confirm_keyboard(language: str):
    builder = InlineKeyboardBuilder()
    if language == "ru":
        builder.row(
            InlineKeyboardButton(text="Да, хочу", callback_data="confirm_broadcast", style="success", icon_custom_emoji_id=CHECK_MARK_EMOJI_ID),
            InlineKeyboardButton(text="Нет, не хочу", callback_data="cancel_broadcast", style="danger", icon_custom_emoji_id=CROSS_EMOJI_ID)
        )
    else:
        builder.row(
            InlineKeyboardButton(text="Yes, I want", callback_data="confirm_broadcast", style="success", icon_custom_emoji_id=CHECK_MARK_EMOJI_ID),
            InlineKeyboardButton(text="No, I don't", callback_data="cancel_broadcast", style="danger", icon_custom_emoji_id=CROSS_EMOJI_ID)
        )
    return builder.as_markup()


async def get_captcha_keyboard(emojis_list: list):
    builder = InlineKeyboardBuilder()
    builder.row(*[InlineKeyboardButton(text=e, callback_data=f"captcha_{e}") for e in emojis_list[:5]])
    builder.row(*[InlineKeyboardButton(text=e, callback_data=f"captcha_{e}") for e in emojis_list[5:10]])
    return builder.as_markup()


async def create_platega_payment(amount: int, user_id: int, language: str):
    headers = {"X-MerchantId": PLATEGA_MERCHANT_ID, "X-Secret": PLATEGA_SECRET, "Content-Type": "application/json"}
    desc_text = f"Пополнение баланса для пользователя {user_id}" if language == "ru" else f"Replenishment of the balance for the user {user_id}"
    payload = {
        "paymentMethod": 2,
        "paymentDetails": {"amount": amount, "currency": "RUB"},
        "description": desc_text,
        "return": "https://t.me/StreamNetVPN_bot",
        "failedUrl": "https://t.me/StreamNetVPN_bot"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{PLATEGA_API_URL}/transaction/process", headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("redirect"), data.get("transactionId")
                return None, None
        except Exception as e:
            print(f"Platega API exception: {e}")
            return None, None


async def check_platega_payment(transaction_id: str):
    headers = {"X-MerchantId": PLATEGA_MERCHANT_ID, "X-Secret": PLATEGA_SECRET, "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{PLATEGA_API_URL}/transaction/{transaction_id}", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("status") in ["PAID", "SUCCESS", "CONFIRMED"]
                return False
        except Exception as e:
            print(f"Platega status check exception: {e}")
            return False


# ========== ХЕНДЛЕРЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            pass

    add_user(user_id, message.from_user.username, message.from_user.first_name)

    if referrer_id:
        set_referrer(user_id, referrer_id)

    language = get_language(user_id)

    if language is None:
        await message.answer(f"{LANG} <b>Choose a language / Выберите язык</b>", reply_markup=await get_language_keyboard())
    else:
        if referrer_id is not None and not is_captcha_passed(user_id):
            await start_captcha(message, user_id, referrer_id, language)
        else:
            text = await get_welcome_text(language)
            await bot.send_photo(message.chat.id, photo=IMAGES["welcome"], caption=text, reply_markup=await get_main_menu_keyboard(language), message_effect_id=HEART_MESSAGE_EFFECT_ID)


async def start_captcha(message: types.Message, user_id: int, referrer_id: int, language: str):
    selected_emojis = random.sample(ALL_EMOJIS, 10)
    target_emoji = random.choice(selected_emojis)
    task_text = TASKS_DB.get(target_emoji, {}).get("ru_form" if language == "ru" else "en", "this emoji")
    captcha_data[user_id] = {"task": task_text, "attempts": 0, "target_emoji": target_emoji, "referrer_id": referrer_id, "emojis": selected_emojis, "language": language}
    text = (f"😊 <b>Небольшая проверка на робота</b>\n\n<blockquote>Выберите эмодзи {task_text}:</blockquote>" if language == "ru"
            else f"😊 <b>Small robot check</b>\n\n<blockquote>Select the {task_text} emoji:</blockquote>")
    await message.answer(text, reply_markup=await get_captcha_keyboard(selected_emojis))


@dp.callback_query(F.data.startswith("captcha_"))
async def handle_captcha(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    selected_emoji = callback.data.split("_")[1]
    if user_id not in captcha_data:
        return
    captcha = captcha_data[user_id]
    target_emoji = captcha["target_emoji"]
    referrer_id = captcha["referrer_id"]
    language = captcha.get("language", get_language(user_id) or "ru")
    if selected_emoji == target_emoji:
        set_captcha_passed(user_id)
        if referrer_id:
            add_referral_reward(referrer_id, user_id, 5)
            referrer_lang = get_language(referrer_id) or "ru"
            await bot.send_message(referrer_id,
                                   f"{NEW_USER} <b>По вашей реферальной ссылке перешёл новый пользователь.</b>\n{DOLLAR} <b>Баланс пополнен на 5 рублей.</b>" if referrer_lang == "ru"
                                   else f"{NEW_USER} <b>A new user joined via your referral link.</b>\n{DOLLAR} <b>Balance topped up by 5 rubles.</b>",
                                   parse_mode="HTML")
        del captcha_data[user_id]
        text = await get_welcome_text(language)
        await bot.send_photo(callback.message.chat.id, photo=IMAGES["welcome"], caption=text, reply_markup=await get_main_menu_keyboard(language), message_effect_id=HEART_MESSAGE_EFFECT_ID)
        try:
            await callback.message.delete()
        except:
            pass
    else:
        captcha["attempts"] += 1
        if captcha["attempts"] >= 3:
            del captcha_data[user_id]
            await callback.message.edit_text("❌ <b>Вы превысили количество попыток. Начните заново командой /start</b>" if language == "ru" else "❌ <b>You have exceeded the number of attempts. Start over with /start</b>", parse_mode="HTML")
        else:
            await callback.answer(f"❌ Неправильно! Осталось попыток: {3 - captcha['attempts']}" if language == "ru" else f"❌ Wrong! Attempts left: {3 - captcha['attempts']}", show_alert=True)


@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    await message.answer(f"{LANG} <b>Choose a language / Выберите язык</b>", reply_markup=await get_language_keyboard())


@dp.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    language = callback.data.split("_")[1]
    set_language(user_id, language)
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id, captcha_passed FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    referrer_id = result[0] if result else None
    captcha_passed = result[1] == 1 if result else False
    await callback.message.delete()
    if referrer_id is not None and not captcha_passed:
        await start_captcha(callback.message, user_id, referrer_id, language)
    else:
        text = await get_welcome_text(language)
        await bot.send_photo(callback.message.chat.id, photo=IMAGES["welcome"], caption=text, reply_markup=await get_main_menu_keyboard(language), message_effect_id=HEART_MESSAGE_EFFECT_ID)


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_count = get_user_count()
    lang = get_language(ADMIN_ID) or "ru"
    await message.answer(f"{STATS} <b>Всего пользователей:</b> <u>{user_count}</u>" if lang == "ru" else f"{STATS} <b>Total users:</b> <u>{user_count}</u>")


@dp.message(Command("adsoff"))
async def cmd_adsoff(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_language(ADMIN_ID) or "ru"
    try:
        parts = message.text.split()
        if len(parts) == 2:
            disable_ads(int(parts[1]))
            await message.answer(f"{CHECK_MARK} <b>Реклама отключена для пользователя {parts[1]}</b>" if lang == "ru" else f"{CHECK_MARK} <b>Advertising is disabled for user {parts[1]}</b>")
        else:
            disable_ads_all()
            await message.answer(f"{CHECK_MARK} <b>Реклама отключена для всех пользователей</b>" if lang == "ru" else f"{CHECK_MARK} <b>Advertising is disabled for all users</b>")
    except ValueError:
        await message.answer("❌ Неверный формат ID" if lang == "ru" else "❌ Invalid ID format")


@dp.message(Command("adson"))
async def cmd_adson(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_language(ADMIN_ID) or "ru"
    try:
        parts = message.text.split()
        if len(parts) == 2:
            enable_ads(int(parts[1]))
            await message.answer(f"{CHECK_MARK} <b>Реклама включена для пользователя {parts[1]}</b>" if lang == "ru" else f"{CHECK_MARK} <b>Advertising is enabled for user {parts[1]}</b>")
        else:
            enable_ads_all()
            await message.answer(f"{CHECK_MARK} <b>Реклама включена для всех пользователей</b>" if lang == "ru" else f"{CHECK_MARK} <b>Advertising is enabled for all users</b>")
    except ValueError:
        await message.answer("❌ Неверный формат ID" if lang == "ru" else "❌ Invalid ID format")


@dp.message(Command("setplan"))
async def cmd_set_plan(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("❌ Использование: /setplan free|premium {user_id}\nПример: /setplan free 7752488661")
        return
    new_plan = parts[1].lower()
    if new_plan not in ['free', 'premium']:
        await message.answer("❌ План должен быть 'free' или 'premium'")
        return
    try:
        target_user_id = int(parts[2])
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
        return
    if new_plan == 'premium':
        activate_premium(target_user_id, days=30)
    else:
        disable_premium(target_user_id)
    lang = get_language(target_user_id) or "ru"
    plan_display = "премиум" if new_plan == 'premium' else "бесплатный" if lang == "ru" else "Premium" if new_plan == 'premium' else "Free"
    await message.answer(f"{CHECK_NEW} <b>План пользователя {target_user_id} изменён на:</b> <u>{plan_display}</u>" if lang == "ru" else f"{CHECK_NEW} <b>User {target_user_id} plan changed to:</b> <u>{plan_display}</u>")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    global broadcast_mode
    broadcast_mode = True
    lang = get_language(ADMIN_ID) or "ru"
    await message.answer(f"{MAIL} <b>Отправьте сообщение для рассылки...</b>" if lang == "ru" else f"{MAIL} <b>Send a message for broadcast...</b>", reply_markup=get_cancel_keyboard(lang))


@dp.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.answer()
    lang = get_language(ADMIN_ID) or "ru"
    global broadcast_mode, pending_broadcast
    broadcast_mode = False
    pending_broadcast.pop(callback.from_user.id, None)
    await callback.message.edit_text(f"{CROSS} <b>Рассылка отменена.</b>" if lang == "ru" else f"{CROSS} <b>Broadcast cancelled.</b>")


@dp.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.answer()
    lang = get_language(ADMIN_ID) or "ru"
    global broadcast_mode, pending_broadcast
    broadcast_data = pending_broadcast.get(callback.from_user.id)
    if not broadcast_data:
        await callback.answer("No data for broadcast", show_alert=True)
        return
    broadcast_mode = False
    users = get_all_users()
    await callback.message.edit_text(f"{BROADCAST_START} <b>Рассылка начата...</b>" if lang == "ru" else f"{BROADCAST_START} <b>Broadcast started...</b>")
    success = 0
    msg_type = broadcast_data["type"]
    for user_id in users:
        try:
            if msg_type == "text":
                await bot.send_message(chat_id=user_id, text=broadcast_data["text"], parse_mode="HTML")
            elif msg_type == "photo":
                await bot.send_photo(chat_id=user_id, photo=broadcast_data["photo"], caption=broadcast_data.get("caption", ""), parse_mode="HTML")
            elif msg_type == "video":
                await bot.send_video(chat_id=user_id, video=broadcast_data["video"], caption=broadcast_data.get("caption", ""), parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    pending_broadcast.pop(callback.from_user.id, None)
    await callback.message.edit_text(f"{CHECK_MARK} <b>Рассылка завершена!</b>\n\n<i>Отправлено: {success} / {len(users)} пользователям</i>." if lang == "ru" else f"{CHECK_MARK} <b>Broadcast completed!</b>\n\n<i>Sent: {success} / {len(users)} users</i>.")


@dp.message(F.text)
async def handle_all_text(message: types.Message):
    global broadcast_mode
    user_id = message.from_user.id
    if message.from_user.id == ADMIN_ID and broadcast_mode:
        lang = get_language(ADMIN_ID) or "ru"
        broadcast_mode = False
        pending_broadcast[message.from_user.id] = {"type": "text", "text": message.text}
        await message.answer(f"{QUESTION_EMOJI} <b>Вы точно хотите разослать это сообщение всем пользователям бота?</b>" if lang == "ru" else f"{QUESTION_EMOJI} <b>Are you sure you want to send this message to all bot users?</b>", reply_markup=get_confirm_keyboard(lang))
        return
    if user_replenish_mode.get(user_id, False):
        await handle_replenish_amount_input(message)


async def handle_replenish_amount_input(message: types.Message):
    user_id = message.from_user.id
    lang = get_language(user_id) or "en"
    try:
        amount = int(float(message.text.strip().replace(',', '.')))
        if amount < 50:
            await message.answer(f"{WARNING} <b>Минимальная сумма пополнения: <u>50 рублей</u></b>" if lang == "ru" else f"{WARNING} <b>Minimum top-up amount: <u>50 rubles</u></b>")
            return
        user_replenish_mode[user_id] = False
        wait_msg = await message.answer(f"{RELOAD} <b>Создаём счёт для оплаты, пожалуйста подождите...</b>" if lang == "ru" else f"{RELOAD} <b>Creating a payment invoice, please wait...</b>")
        await asyncio.sleep(2)
        await wait_msg.delete()
        try:
            await message.delete()
        except:
            pass
        payment_url, transaction_id = await create_platega_payment(amount, user_id, lang)
        if not payment_url or not transaction_id:
            await message.answer(f"{WARNING} <b>Ошибка создания платежа. Попробуйте позже.</b>" if lang == "ru" else f"{WARNING} <b>Payment creation error. Try again later.</b>")
            return
        replenish_data[user_id] = {"transaction_id": transaction_id, "chat_id": message.chat.id, "paid": False, "payment_url": payment_url, "amount": amount, "is_replenish": True}
        text = await get_replenish_payment_text(lang, amount, transaction_id, paid=False)
        sent_msg = await bot.send_photo(message.chat.id, photo=IMAGES["replenish" if lang == "ru" else "replenish_en"], caption=text, reply_markup=await get_payment_keyboard(lang, payment_url, paid=False, is_replenish=True, transaction_id=transaction_id))
        replenish_data[user_id]["message_id"] = sent_msg.message_id
    except ValueError:
        await message.answer(f"{WARNING} <b>Пожалуйста, введите число.</b>" if lang == "ru" else f"{WARNING} <b>Please enter a number.</b>")


@dp.callback_query(F.data.startswith("check_replenish_"))
async def handle_check_replenish(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    transaction_id = callback.data.split("_")[2]
    if user_id not in replenish_data or replenish_data[user_id]["transaction_id"] != transaction_id:
        await callback.answer("❌ Платёж не найден", show_alert=True)
        return
    is_paid = await check_platega_payment(transaction_id)
    amount = replenish_data[user_id]["amount"]
    if is_paid:
        replenish_data[user_id]["paid"] = True
        await callback.answer(f"✅ Оплата подтверждена. Ваш баланс пополнен на {amount} рублей." if lang == "ru" else f"✅ Payment confirmed. Your balance has been topped up by {amount} rubles.", show_alert=True)
        add_balance(user_id, amount)
        referrer_id = get_referrer(user_id)
        if referrer_id:
            reward = int(amount * 0.1)
            if reward > 0:
                add_balance(referrer_id, reward)
                referrer_lang = get_language(referrer_id) or "ru"
                try:
                    await bot.send_message(referrer_id, f"{NEW_USER} <b>Ваш реферал пополнил баланс на {amount} руб.</b>\n{TOPUP} <b>Вы получили {reward} руб.</b>" if referrer_lang == "ru" else f"{NEW_USER} <b>Your referral topped up balance by {amount} rub.</b>\n{TOPUP} <b>You received {reward} rub.</b>", parse_mode="HTML")
                except:
                    pass
        del replenish_data[user_id]
        user_replenish_mode[user_id] = False
        text = await get_welcome_text(lang)
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["welcome"], caption=text), reply_markup=await get_main_menu_keyboard(lang))
    else:
        await callback.answer("⏳ Оплата еще не поступила. Попробуйте позже..." if lang == "ru" else "⏳ Payment not received yet. Try again later...", show_alert=True)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = await get_welcome_text(lang)
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["welcome"], caption=text), reply_markup=await get_main_menu_keyboard(lang))


@dp.callback_query(F.data == "back_to_rate_select")
async def back_to_rate_select(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = f"{CLICK_DOWN_NEW} <b>Выберите тариф:</b>" if lang == "ru" else f"{CLICK_DOWN_NEW} <b>Choose a plan:</b>"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["chooserate" if lang == "ru" else "chooserate_en"], caption=text), reply_markup=await get_choose_plan_keyboard(lang))


@dp.callback_query(F.data == "back_to_device_select")
async def back_to_device_select(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = f"{CLICK_DOWN_NEW} <b>Выберите тариф:</b>" if lang == "ru" else f"{CLICK_DOWN_NEW} <b>Choose a plan:</b>"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["chooserate" if lang == "ru" else "chooserate_en"], caption=text), reply_markup=await get_choose_plan_keyboard(lang))


@dp.callback_query(F.data == "connect")
async def handle_connect(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = f"{CLICK_DOWN_NEW} <b>Выберите тариф:</b>" if lang == "ru" else f"{CLICK_DOWN_NEW} <b>Choose a plan:</b>"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["chooserate" if lang == "ru" else "chooserate_en"], caption=text), reply_markup=await get_choose_plan_keyboard(lang))


@dp.callback_query(F.data == "plan_free")
async def handle_free_plan(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    set_plan(user_id, 'free')
    sponsors = await get_sponsors(user_id, callback.message.chat.id, 'free')
    if sponsors is None:
        text = f"{WARNING} <b>Ошибка подключения к Subgram. Попробуйте позже.</b>" if lang == "ru" else f"{WARNING} <b>Error connecting to Subgram. Try again later.</b>"
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["subscribe" if lang == "ru" else "en_subscribe"], caption=text), reply_markup=await get_back_keyboard(lang))
        return
    if sponsors:
        user_data[user_id] = sponsors
        builder = InlineKeyboardBuilder()
        for i, sponsor in enumerate(sponsors):
            builder.add(InlineKeyboardButton(text=f"Спонсор №{i + 1}" if lang == "ru" else f"Sponsor №{i + 1}", url=sponsor.get("link", ""), style="primary"))
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text="Проверить подписку" if lang == "ru" else "Check subscription", callback_data="check_subs_free", style="success", icon_custom_emoji_id=CHECK_EMOJI_ID))
        builder.row(InlineKeyboardButton(text="« Назад" if lang == "ru" else "« Back", callback_data="back_to_menu", style="default"), InlineKeyboardButton(text="Меню" if lang == "ru" else "Menu", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID))
        text = f"{LOCK} <b>Для доступа к VPN необходимо подписаться на каналы спонсоров:</b>\n<blockquote>{WARNING} <b>Отписаться от спонсоров можно в понедельник следующей недели</b> <i>(от тех, на которых вы подписались до этого понедельника).</i></blockquote>" if lang == "ru" else f"{LOCK} <b>To access VPN you need to subscribe to sponsor channels:</b>\n<blockquote>{WARNING} <b>You can unsubscribe from sponsors on Monday of next week</b> <i>(from those you subscribed to before this Monday).</i></blockquote>"
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["subscribe"], caption=text), reply_markup=builder.as_markup())
    else:
        text = f"{CLICK_DOWN} <b>Выберите устройство:</b>" if lang == "ru" else f"{CLICK_DOWN} <b>Choose device:</b>"
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["choosedevice"], caption=text), reply_markup=await get_choose_device_keyboard(lang))


@dp.callback_query(F.data == "plan_premium")
async def handle_premium_plan(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    PRICE = 130
    if check_premium_active(user_id):
        text = f"{CLICK_DOWN} <b>Выберите устройство:</b>" if lang == "ru" else f"{CLICK_DOWN} <b>Choose device:</b>"
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["choosedevice"], caption=text), reply_markup=await get_choose_device_keyboard(lang))
        return
    try:
        await callback.message.delete()
    except:
        pass
    wait_msg = await callback.message.answer(f"{RELOAD} <b>Создаём счёт для оплаты, пожалуйста подождите...</b>" if lang == "ru" else f"{RELOAD} <b>Creating a payment invoice, please wait...</b>")
    await asyncio.sleep(2)
    await wait_msg.delete()
    transaction_id = generate_short_transaction_id()
    text = (f"{MONEY_FLY} <b>Ваш счет на оплату успешно создан</b>\n\n"
            f"{MONEY_BAG} <b>Сумма к оплате:</b> <code>{PRICE} RUB</code>\n"
            f"{ID_CARD_PAY} <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
            f"{CLICK_PAY} <b>Нажмите</b> «Оплатить» <b>для оплаты доступа</b>\n\n"
            f"{HOURGLASS_PAY} <b>Ожидаем оплату...</b>" if lang == "ru" else
            f"{MONEY_FLY} <b>Your payment invoice has been successfully created</b>\n\n"
            f"{MONEY_BAG} <b>Amount to pay:</b> <code>{PRICE} RUB</code>\n"
            f"{ID_CARD_PAY} <b>Transaction ID:</b> <code>{transaction_id}</code>\n\n"
            f"{CLICK_PAY} <b>Click</b> «Pay» <b>to pay for access</b>\n\n"
            f"{HOURGLASS_PAY} <b>Waiting for payment...</b>")
    sent_msg = await bot.send_photo(callback.message.chat.id, photo=IMAGES["payment" if lang == "ru" else "payment_en"], caption=text, reply_markup=await get_premium_payment_keyboard(lang, transaction_id, paid=False))
    payment_data[user_id] = {"transaction_id": transaction_id, "amount": PRICE, "message_id": sent_msg.message_id, "chat_id": callback.message.chat.id, "paid": False}


@dp.callback_query(F.data.startswith("pay_premium_from_balance_"))
async def handle_pay_premium_from_balance(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    transaction_id = callback.data.split("_")[4]
    PRICE = 130
    if user_id not in payment_data or payment_data[user_id]["transaction_id"] != transaction_id:
        await callback.answer("❌ Платёж не найден", show_alert=True)
        return
    balance = get_balance(user_id)
    if balance >= PRICE:
        deduct_balance(user_id, PRICE)
        activate_premium(user_id, days=30)
        payment_data[user_id]["paid"] = True
        await callback.answer("🎉 Премиум тариф активирован. Спасибо за покупку :)" if lang == "ru" else "🎉 Premium plan activated. Thank you for your purchase :)", show_alert=True)
        text = f"{CLICK_DOWN} <b>Выберите устройство:</b>" if lang == "ru" else f"{CLICK_DOWN} <b>Choose device:</b>"
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["choosedevice"], caption=text), reply_markup=await get_choose_device_keyboard(lang))
        del payment_data[user_id]
    else:
        needed = PRICE - balance
        await callback.answer(f"🚫 На вашем балансе недостаточно средств. Пополните его на {needed} рублей чтобы совершить оплату." if lang == "ru" else f"🚫 Insufficient funds in your balance. Top up by {needed} rubles to complete the payment.", show_alert=True)


@dp.callback_query(F.data.startswith("activate_premium_internal_"))
async def handle_activate_premium_internal(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    transaction_id = callback.data.split("_")[3]
    if user_id not in payment_data or payment_data[user_id]["transaction_id"] != transaction_id:
        await callback.answer("❌ Платёж не найден", show_alert=True)
        return
    if not payment_data[user_id].get("paid", False):
        await callback.answer("❌ Сначала оплатите счёт", show_alert=True)
        return
    del payment_data[user_id]
    activate_premium(user_id, days=30)
    await callback.answer("🎉 Премиум активирован на 30 дней!" if lang == "ru" else "🎉 Premium activated for 30 days!", show_alert=True)
    text = f"{CLICK_DOWN} <b>Выберите устройство:</b>" if lang == "ru" else f"{CLICK_DOWN} <b>Choose device:</b>"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["choosedevice"], caption=text), reply_markup=await get_choose_device_keyboard(lang))


@dp.callback_query(F.data == "cancel_premium_payment")
async def cancel_premium_payment(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    if user_id in payment_data:
        del payment_data[user_id]
    await callback.answer("❌ Оплата отменена" if lang == "ru" else "❌ Payment cancelled", show_alert=True)
    text = await get_welcome_text(lang)
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["welcome"], caption=text), reply_markup=await get_main_menu_keyboard(lang))


@dp.callback_query(F.data == "replenish_balance")
async def handle_replenish_balance(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    user_replenish_mode[user_id] = True
    text = f"{TOPUP} <b>Введите сумму пополнения баланса в рублях:</b>" if lang == "ru" else f"{TOPUP} <b>Enter the top-up amount in rubles:</b>"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["replenish" if lang == "ru" else "replenish_en"], caption=text), reply_markup=await get_replenish_amount_keyboard(lang))


@dp.callback_query(F.data == "cancel_replenish")
async def cancel_replenish(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    user_replenish_mode[user_id] = False
    text = await get_welcome_text(lang)
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["welcome"], caption=text), reply_markup=await get_main_menu_keyboard(lang))


@dp.callback_query(F.data == "referral")
async def handle_referral(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    referral_code = get_referral_code(user_id)
    stats = get_referral_stats(user_id)
    bot_username = (await bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    text = (f"<b>Ваша статистика:</b>\n"
            f"{PEOPLE} Приглашено: <code>{stats['count']}</code> человек\n"
            f"{MONEY} Заработано: <code>{stats['earnings']} руб.</code>\n\n"
            f"<b>Как это работает:</b>\n"
            f"• Друг переходит по вашей ссылке → вам <code>+5 руб.</code>\n"
            f"• Друг пополняет баланс → вам <code>10%</code> от суммы пополнения\n\n"
            f"<b>Ваша реферальная ссылка:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            f"{SHARE} <b>Поделитесь ссылкой с друзьями!</b>" if lang == "ru" else
            f"<b>Your stats:</b>\n"
            f"{PEOPLE} Invited: <code>{stats['count']}</code> people\n"
            f"{MONEY} Earned: <code>{stats['earnings']} rub.</code>\n\n"
            f"<b>How it works:</b>\n"
            f"• Friend joins via your link → to you <code>+5 rub.</code>\n"
            f"• A friend replenishes the balance → to you <code>10%</code> from the deposit amount\n\n"
            f"<b>Your referral link:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            f"{SHARE} <b>Share the link with friends!</b>")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Список рефералов" if lang == "ru" else "Referral list", callback_data="referral_list", style="primary", icon_custom_emoji_id=REFERRAL_LIST_EMOJI_ID))
    builder.row(InlineKeyboardButton(text="« Назад" if lang == "ru" else "« Back", callback_data="back_to_menu", style="default"))
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["referral_program" if lang == "ru" else "referral_program_en"], caption=text), reply_markup=builder.as_markup())


@dp.callback_query(F.data == "referral_list")
async def handle_referral_list(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    referrals = get_referral_list(user_id)
    if not referrals:
        text = "<b>У вас пока нет приглашённых пользователей.</b>" if lang == "ru" else "<b>You don't have any referred users yet.</b>"
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["referral_program" if lang == "ru" else "referral_program_en"], caption=text), reply_markup=await get_back_keyboard(lang, "referral"))
        return
    text = "<b>Ваши рефералы:</b>\n\n" if lang == "ru" else f"{GIFT} <b>Your referrals:</b>\n\n"
    for ref in referrals[:20]:
        _, first_name, _, reward, created_at = ref
        date_str = created_at[:10] if created_at else ""
        text += f"• {first_name} — <code>+{reward} руб.</code> ({date_str})\n" if lang == "ru" else f"• {first_name} — <code>+{reward} rub.</code> ({date_str})\n"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["referral_program" if lang == "ru" else "referral_program_en"], caption=text), reply_markup=await get_back_keyboard(lang, "referral"))


@dp.callback_query(F.data.startswith("confirm_replenish_"))
async def handle_confirm_replenish(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    transaction_id = callback.data.split("_")[2]
    if user_id not in replenish_data or replenish_data[user_id]["transaction_id"] != transaction_id:
        await callback.answer("❌ Платёж не найден", show_alert=True)
        return
    if not replenish_data[user_id].get("paid", False):
        await callback.answer("❌ Сначала оплатите счёт", show_alert=True)
        return
    amount = replenish_data[user_id]["amount"]
    add_balance(user_id, amount)
    referrer_id = get_referrer(user_id)
    if referrer_id:
        reward = int(amount * 0.1)
        if reward > 0:
            add_balance(referrer_id, reward)
            referrer_lang = get_language(referrer_id) or "ru"
            try:
                await bot.send_message(referrer_id, f"{NEW_USER} <b>Ваш реферал пополнил баланс на {amount} руб.</b>\n{TOPUP} <b>Вы получили {reward} руб.</b>" if referrer_lang == "ru" else f"{NEW_USER} <b>Your referral topped up balance by {amount} rub.</b>\n{TOPUP} <b>You received {reward} rub.</b>", parse_mode="HTML")
            except:
                pass
    del replenish_data[user_id]
    user_replenish_mode[user_id] = False
    await callback.answer(f"✅ Баланс пополнен на {amount} руб!" if lang == "ru" else f"✅ Balance topped up by {amount} rub!", show_alert=True)
    text = await get_welcome_text(lang)
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["welcome"], caption=text), reply_markup=await get_main_menu_keyboard(lang))


@dp.callback_query(F.data == "cancel_payment")
async def handle_cancel_payment(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    if user_id in payment_data:
        del payment_data[user_id]
    if user_id in replenish_data:
        del replenish_data[user_id]
    user_replenish_mode[user_id] = False
    await callback.answer("❌ Оплата отменена" if lang == "ru" else "❌ Payment cancelled", show_alert=True)
    text = await get_welcome_text(lang)
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["welcome"], caption=text), reply_markup=await get_main_menu_keyboard(lang))


@dp.callback_query(F.data == "plan_differences")
async def plan_differences(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = (f"{FREE} <b>Бесплатный тариф:</b>\n\n"
            f"{CHECK_MARK} <u>Стандартная скорость соединения</u>\n"
            f"{CHECK_MARK} <u>Ограниченное количество серверов</u>\n"
            f"{CHECK_MARK} <u>Базовое шифрование трафика</u>\n"
            f"{CROSS} <s>Обход Белых списков</s>\n"
            f"{CROSS} <s>Высокоскоростные серверы</s>\n"
            f"{CROSS} <s>Расширенный выбор локаций</s>\n"
            f"{CROSS} <s>Приоритетное шифрование</s>\n\n"
            f"{CROWN} <b>Премиум тариф:</b>\n\n"
            f"{CHECK_MARK} <u>Максимальная скорость соединения</u>\n"
            f"{CHECK_MARK} <u>Обход Белых списков</u>\n"
            f"{CHECK_MARK} <u>Большое количество серверов по всему миру</u>\n"
            f"{CHECK_MARK} <u>Улучшенное шифрование трафика</u>\n"
            f"{CHECK_MARK} <u>Специальные VPN протоколы</u>\n"
            f"{CHECK_MARK} <u>Отсутствие ограничений по трафику</u>" if lang == "ru" else
            f"{FREE} <b>Free plan:</b>\n\n"
            f"{CHECK_MARK} <u>Standard connection speed</u>\n"
            f"{CHECK_MARK} <u>Limited number of servers</u>\n"
            f"{CHECK_MARK} <u>Basic traffic encryption</u>\n"
            f"{CROSS} <s>Bypassing Whitelists</s>\n"
            f"{CROSS} <s>High-speed servers</s>\n"
            f"{CROSS} <s>Extended location selection</s>\n"
            f"{CROSS} <s>Priority encryption</s>\n\n"
            f"{CROWN} <b>Premium plan:</b>\n\n"
            f"{CHECK_MARK} <u>Maximum connection speed</u>\n"
            f"{CHECK_MARK} <u>Bypassing Whitelists</u>\n"
            f"{CHECK_MARK} <u>Large number of servers worldwide</u>\n"
            f"{CHECK_MARK} <u>Advanced traffic encryption</u>\n"
            f"{CHECK_MARK} <u>Special VPN protocols</u>\n"
            f"{CHECK_MARK} <u>No traffic limits</u>")
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["differences" if lang == "ru" else "differences_en"], caption=text), reply_markup=await get_back_keyboard(lang, "back_to_rate_select", show_home=True))


@dp.callback_query(F.data == "check_subs_free")
async def check_subs_free(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    sponsors = user_data.get(user_id, [])
    links = [s.get("link") for s in sponsors if s.get("link")]
    ads_disabled = is_ads_disabled(user_id)
    if not links:
        text = (f"{CLICK_DOWN} <b>Выберите устройство:</b>" if ads_disabled else f"{HEART} <b>Спасибо за подписку!</b>\n\n{CLICK_DOWN} <b>Выберите устройство:</b>" if lang == "ru" else
                f"{CLICK_DOWN} <b>Choose device:</b>" if ads_disabled else f"{HEART} <b>Thank you for subscribing!</b>\n\n{CLICK_DOWN} <b>Choose device:</b>")
        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["choosedevice"], caption=text), reply_markup=await get_choose_device_keyboard(lang))
        return
    headers = {"Auth": SUBGRAM_API_KEY, "Content-Type": "application/json"}
    payload = {"user_id": user_id, "links": links}
    async with aiohttp.ClientSession() as session:
        async with session.post(SUBGRAM_CHECK_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("status") == "ok":
                    sponsors_data = data.get("additional", {}).get("sponsors", [])
                    status_map = {s.get("link"): s.get("status") == "subscribed" for s in sponsors_data}
                    not_subscribed = [s for s in sponsors if not status_map.get(s.get("link"), False)]
                    if not not_subscribed:
                        user_data.pop(user_id, None)
                        text = f"{HEART} <b>Спасибо за подписку!</b>\n\n{CLICK_DOWN} <b>Выберите устройство:</b>" if lang == "ru" else f"{HEART} <b>Thank you for subscribing!</b>\n\n{CLICK_DOWN} <b>Choose device:</b>"
                        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["choosedevice"], caption=text), reply_markup=await get_choose_device_keyboard(lang))
                    else:
                        user_data[user_id] = [{"link": s["link"], "resource_name": s["resource_name"]} for s in not_subscribed]
                        builder = InlineKeyboardBuilder()
                        for i, sponsor in enumerate(not_subscribed):
                            builder.add(InlineKeyboardButton(text=f"Спонсор {i + 1}" if lang == "ru" else f"Sponsor {i + 1}", url=sponsor.get("link", ""), style="primary"))
                        builder.adjust(2)
                        builder.row(InlineKeyboardButton(text="Проверить подписку" if lang == "ru" else "Check subscription", callback_data="check_subs_free", style="success", icon_custom_emoji_id=CHECK_EMOJI_ID))
                        builder.row(InlineKeyboardButton(text="« Назад" if lang == "ru" else "« Back", callback_data="back_to_menu", style="default"), InlineKeyboardButton(text="Меню" if lang == "ru" else "Menu", callback_data="back_to_menu", style="default", icon_custom_emoji_id=HOME_EMOJI_ID))
                        text = f"{WARNING} <b>Вы подписались не на все каналы.</b>\n\n<i>Подпишитесь на все и нажмите «Проверить подписку».</i>" if lang == "ru" else f"{WARNING} <b>You haven't subscribed to all channels.</b>\n\n<i>Subscribe to all and press «Check subscription».</i>"
                        await callback.message.edit_media(InputMediaPhoto(media=IMAGES["subscribe" if lang == "ru" else "en_subscribe"], caption=text), reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("device_"))
async def handle_device_selection(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    device = callback.data.split("_")[1]
    plan = get_plan(user_id)
    
    if plan == 'premium':
        token = get_or_create_subscription_token(user_id)
        config_url = f"https://streamnetvpn.bothost.tech/sub/{token}"
    else:
        config_url = CONFIG_URL
    
    device_image_map = {"iphone": "iphone", "android": "android", "macos": "laptop", "windows": "laptop", "androidtv": "tv"}
    image_key = device_image_map.get(device, "choosedevice")
    text = await get_device_instruction_text(device, lang, plan, user_id, config_url)
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES[image_key], caption=text), reply_markup=await get_device_instruction_keyboard(device, lang, plan, user_id, config_url))


@dp.callback_query(F.data == "about_bot")
async def about_bot(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = (f"<b>StreamNet VPN</b> — это современный и надёжный инструмент для обеспечения безопасности и конфиденциальности в интернете.\n\n"
            f"• <u>Быстрое и стабильное соединение</u>\n"
            f"• <u>Защита ваших данных на публичных Wi-Fi сетях</u>\n"
            f"• <u>Доступ к любимым сайтам и сервисам даже при белых списках</u>\n"
            f"• <u>Безлимитный трафик</u>\n"
            f"• <u>Не храним логи пользователей</u>\n\n"
            f"<b>Бот предоставляет удобный способ получить доступ к конфигурациям VPN и прокси для Telegram.</b>" if lang == "ru" else
            f"<b>StreamNet VPN</b> is a modern and reliable tool for ensuring security and privacy on the internet.\n\n"
            f"• <u>Fast and stable connection</u>\n"
            f"• <u>Protect your data on public Wi-Fi networks</u>\n"
            f"• <u>Access to your favorite websites and services even with the white lists</u>\n"
            f"• <u>Unlimited traffic</u>\n"
            f"• <u>No user logs stored</u>\n\n"
            f"<b>The bot provides a convenient way to get access to VPN configurations and proxies for Telegram.</b>")
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["documents" if lang == "ru" else "documents_en"], caption=text), reply_markup=await get_about_bot_keyboard(lang))


@dp.callback_query(F.data == "help_vpn")
async def help_vpn(callback: types.CallbackQuery):
    await callback.answer()
    lang = get_language(callback.from_user.id) or "en"
    text = (f"{HELP_WARNING} <b>VPN:</b>"
            f"<blockquote>1 способ: Обновите подписку в приложении Happ\n"
            f"2 способ (если 1 не помог): Получите актуальный конфиг</blockquote>\n\n"
            f"{HELP_SATELLITE} <b>Прокси:</b>"
            f"<blockquote>1 способ: Переключитесь с мобильной сети на Wi-Fi и наоборот\n"
            f"2 способ: Выберите другой прокси (с наименьшим пингом)</blockquote>" if lang == "ru" else
            f"{HELP_WARNING} <b>VPN:</b>"
            f"<blockquote>Method 1: Update subscription in Happ app\n"
            f"Method 2 (if method 1 didn't help): Get the actual config</blockquote>\n\n"
            f"{HELP_SATELLITE} <b>Proxy:</b>"
            f"<blockquote>Method 1: Switch between mobile network and Wi-Fi\n"
            f"Method 2: Choose a different proxy (with the lowest ping)</blockquote>")
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["notwork" if lang == "ru" else "en_notwork"], caption=text), reply_markup=await get_back_keyboard(lang))


@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lang = get_language(user_id) or "en"
    days_in_bot = get_user_joined_date(user_id)
    plan = get_plan(user_id)
    premium_until = get_premium_until(user_id)
    balance = get_balance(user_id)
    plan_display = "премиум" if plan == 'premium' else "бесплатный" if lang == "ru" else "Premium" if plan == 'premium' else "Free"
    text = (f"{ID_SYMBOL} <b>Ваш Telegram ID:</b> <code>{user_id}</code>\n"
            f"{MONEY} <b>На балансе:</b> <code>{balance} руб.</code>\n"
            f"{HOURGLASS} <b>Вы с нами:</b> <u>{days_in_bot} дней</u>\n"
            f"{ENVELOPE} <b>Ваш тариф:</b> <i>{plan_display}</i>\n" if lang == "ru" else
            f"{ID_SYMBOL} <b>Your Telegram ID:</b> <code>{user_id}</code>\n"
            f"{MONEY} <b>Balance:</b> <code>{balance} rub.</code>\n"
            f"{HOURGLASS} <b>With us:</b> <u>{days_in_bot} days</u>\n"
            f"{ENVELOPE} <b>Your plan:</b> <i>{plan_display}</i>\n")
    if plan == 'premium' and premium_until:
        until_str = premium_until.split(':')[0] if ':' in premium_until else premium_until
        text += f"{CROWN} <b>Премиум активен до:</b> <u>{until_str}</u>\n" if lang == "ru" else f"{CROWN} <b>Premium active until:</b> <u>{until_str}</u>\n"
    await callback.message.edit_media(InputMediaPhoto(media=IMAGES["profile" if lang == "ru" else "profile_en"], caption=text), reply_markup=await get_back_keyboard(lang))


# ========== MAIN ==========

async def main():
    asyncio.create_task(premium_expiry_checker())
    await set_all_commands(bot)
    print("Bot StreamNet VPN started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())