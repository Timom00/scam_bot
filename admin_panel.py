import telebot
from telebot import types
import json
import re
from datetime import datetime, timezone

TOKEN = "7660678589:AAG5Bo3rAodVO_YiHs4f6jPniKQt8ZBVU1U"
bot = telebot.TeleBot(TOKEN)

SCAMLIST_FILE = "scamlist.json"
VOTES_FILE = "votes.json"

SCAM_KEYWORDS = [
    "заработок", "легкие деньги", "быстрый доход", "инвестиции", "крипта",
    "100% прибыль", "без риска", "гарантированный доход", "пассивный доход",
    "скам", "лохотрон", "пирамида", "бесплатно", "вложение", "легко",
    "финансовая пирамида", "отзывы", "поддержка", "прибыль", "доход", "вывод",
    "минимальная сумма", "акция", "бонус", "платит", "торговля", "биткоин",
    "обман", "скам-проект", "мошенники", "легкие деньги", "работа на дому",
    "без вложений", "заработок в интернете", "прибыль с нуля", "сделай сам",
    "инвестируй", "токены", "форекс", "робот для торговли", "супер доход",
    "программа", "гарантия", "пассивный доход", "сеть", "маркетинг", "реферальная программа",
    "доход до", "заработок онлайн", "проверено", "секрет успеха", "мультипликатор",
    "обещают", "быстрая прибыль", "работай дома", "пассивный заработок",
    "финансовый консультант", "подработка", "трейдинг", "зарплата", "финансовый советник",
    "финансовые инвестиции", "акции", "инвестиционный фонд", "деньги без риска",
    "супер предложение", "онлайн бизнес", "платежи", "вывод средств", "автоматический доход",
    "прибыль 100%", "заработок с нуля", "гарантированная прибыль", "обучение трейдингу",
    "финансовая пирамида", "лохотрон", "проект с гарантией", "скрытые комиссии",
    "легкий заработок", "доход без вложений", "выплаты", "прямые инвестиции",
    "бот для заработка", "бот для торговли", "скам-проект", "мошенничество", "фейк",
    "обмануть", "ввод денег", "вывод денег", "криптовалюта", "финансовая афера",
    "пирамида", "схема", "быстрый обман", "скрытый обман", "сделать деньги быстро",
    "получить деньги", "сделай деньги", "обман пользователей", "платформа"
]

def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def contains_scam_keywords(text):
    if not text:
        return False
    text = text.lower()
    for kw in SCAM_KEYWORDS:
        if kw in text:
            return True
    return False

def check_url_scammy(url):
    scam_url_keywords = ["free", "bonus", "investment", "crypto", "earn", "quick", "fast", "money"]
    url = url.lower()
    for kw in scam_url_keywords:
        if kw in url:
            return True
    return False

def check_scam_factors(chat):
    warnings = []
    scam_score = 0

    # Проверка подписчиков
    try:
        members_count = bot.get_chat_members_count(chat.id)
        if members_count < 50:
            warnings.append(f"Подписчиков всего {members_count} — мало.")
            scam_score += 1
    except Exception:
        warnings.append("Не удалось проверить количество подписчиков.")
        scam_score += 1

    # Проверка названия и описания
    if contains_scam_keywords(chat.title):
        warnings.append("В названии канала есть подозрительные слова.")
        scam_score += 2
    try:
        description = bot.get_chat(chat.id).description
        if contains_scam_keywords(description):
            warnings.append("В описании канала есть подозрительные слова.")
            scam_score += 2
    except Exception:
        pass

    # Проверка ссылки на скам
    try:
        invite_link = bot.export_chat_invite_link(chat.id)
        if check_url_scammy(invite_link):
            warnings.append("В ссылке приглашения есть подозрительные слова.")
            scam_score += 1
    except Exception:
        pass

    # Проверка аватарки
    try:
        photos = bot.get_chat(chat.id).photo
        if photos is None:
            warnings.append("У канала нет аватарки.")
            scam_score += 1
    except Exception:
        pass

    # Проверка закреплённого сообщения
    try:
        pinned_msg = bot.get_chat(chat.id).pinned_message
        if pinned_msg is None:
            warnings.append("У канала нет закреплённого сообщения.")
            scam_score += 1
    except Exception:
        pass

    return warnings, scam_score

def init_votes_for_channel(channel_username):
    votes = load_json(VOTES_FILE)
    if channel_username not in votes:
        votes[channel_username] = {"scam": 0, "not_scam": 0, "voters": []}
        save_json(VOTES_FILE, votes)

def update_vote(channel_username, user_id, vote_type):
    votes = load_json(VOTES_FILE)
    if channel_username not in votes:
        votes[channel_username] = {"scam": 0, "not_scam": 0, "voters": []}

    if user_id in votes[channel_username]["voters"]:
        return False

    if vote_type == "scam":
        votes[channel_username]["scam"] += 1
    else:
        votes[channel_username]["not_scam"] += 1
    votes[channel_username]["voters"].append(user_id)
    save_json(VOTES_FILE, votes)
    return True

def get_vote_stats(channel_username):
    votes = load_json(VOTES_FILE)
    if channel_username not in votes:
        return (0, 0)
    return votes[channel_username]["scam"], votes[channel_username]["not_scam"]

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне @username канала — я проверю его на скам и предложу проголосовать.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("@"))
def check_channel(message):
    channel_username = message.text.strip()[1:].lower()

    try:
        chat = bot.get_chat(message.text.strip())
    except Exception as e:
        bot.send_message(message.chat.id, f"Не удалось получить данные канала: {e}")
        return

    warnings, scam_score = check_scam_factors(chat)
    init_votes_for_channel(channel_username)

    if scam_score >= 3:
        verdict = "🚨 Высокая вероятность скама!"
    elif scam_score == 0:
        verdict = "✅ Канал выглядит безопасным."
    else:
        verdict = "⚠️ Есть подозрительные признаки."

    reply = f"{verdict}\n\n"
    if warnings:
        reply += "Подробности:\n" + "\n".join(f"- {w}" for w in warnings) + "\n\n"
    reply += "Голосуй, чтобы помочь другим!"

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_scam = types.InlineKeyboardButton(text="🚫 Скам", callback_data=f"vote_scam_{channel_username}")
    btn_not_scam = types.InlineKeyboardButton(text="✅ Не скам", callback_data=f"vote_not_scam_{channel_username}")
    markup.add(btn_scam, btn_not_scam)

    bot.send_message(message.chat.id, reply, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def handle_vote(call):
    data = call.data.split("_")
    if len(data) < 3:
        bot.answer_callback_query(call.id, "Ошибка данных голосования.")
        return

    vote_type = data[1]
    channel_username = "_".join(data[2:]).lower()
    user_id = call.from_user.id

    success = update_vote(channel_username, user_id, vote_type)
    if not success:
        bot.answer_callback_query(call.id, "Ты уже голосовал за этот канал.")
        return

    bot.answer_callback_query(call.id, "Спасибо за голос!")

    scam_votes, not_scam_votes = get_vote_stats(channel_username)

    stat_text = (
        f"Статистика голосования для @{channel_username}:\n"
        f"🚫 Скам: {scam_votes}\n"
        f"✅ Не скам: {not_scam_votes}\n\n"
        f"Если хочешь проверить другой канал — отправь его @username."
    )

    bot.send_message(call.message.chat.id, stat_text)

bot.polling(none_stop=True)
