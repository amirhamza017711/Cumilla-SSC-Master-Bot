import requests
import asyncio
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import os
import urllib3
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# =========================================================
# FLASK KEEP ALIVE
# =========================================================

app = Flask('')

@app.route('/')
def home():
    return "MASTER BOT RUNNING!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8751047450:AAGBCmxj4t6AP0yiDeYeRQ8qD3v0-LzNon8"

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://billpay.sonalibank.com.bd/XIClassAdmission/Fee/"
}

current_search_id = 0
user_modes = {}

# =========================================================
# SONALI FETCH
# =========================================================

def get_sonali_data(tid):

    url = (
        "https://billpay.sonalibank.com.bd/"
        f"XIClassAdmission/Home/Voucher/{tid}"
    )

    try:

        r = session.get(
            url,
            headers=headers,
            timeout=15,
            verify=False
        )

        soup = BeautifulSoup(r.text, "html.parser")

        d = {
            "id": tid,
            "date": "N/A",
            "fee_type": "N/A",
            "name": "N/A",
            "contact": "N/A",
            "roll": "N/A",
            "board": "N/A",
            "year": "N/A",
            "amount": "0.00"
        }

        tds = soup.find_all("td")

        for i, td in enumerate(tds):

            txt = td.get_text(strip=True).replace(":", "")

            if i + 1 < len(tds):

                val = tds[i + 1].get_text(strip=True)

                if "Transaction Id" == txt:
                    d["id"] = val

                elif "Date" == txt:
                    d["date"] = val

                elif "Fee Type" == txt:
                    d["fee_type"] = val

                elif "Student Name" == txt:
                    d["name"] = val

                elif "Contact No" == txt:
                    d["contact"] = val

                elif "Roll" == txt:
                    d["roll"] = val

                elif "Board" == txt:
                    d["board"] = val

                elif "Year" == txt:
                    d["year"] = val

                elif "Fee Amount" == txt:
                    d["amount"] = val

        return d

    except:
        return None

# =========================================================
# SSC FETCH
# =========================================================

def fetch_cumilla_result(roll):

    url = (
        "https://result19.comillaboard.gov.bd/"
        "2025/individual/result.php"
    )

    headers2 = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer":
        "https://result19.comillaboard.gov.bd/2025/individual/"
    }

    try:

        r = requests.post(
            url,
            data={"roll": roll},
            headers=headers2,
            timeout=15,
            verify=False
        )

        if r.status_code != 200 or "Name" not in r.text:
            return None, None

        soup = BeautifulSoup(r.text, "html.parser")

        info = {}

        all_tds = soup.find_all("td")

        for i, td in enumerate(all_tds):

            text = td.get_text(strip=True)

            if "Name" == text:
                info['name'] = all_tds[i+1].get_text(strip=True)

            elif "Father's Name" == text:
                info['father'] = all_tds[i+1].get_text(strip=True)

            elif "Mother's Name" == text:
                info['mother'] = all_tds[i+1].get_text(strip=True)

            elif "Group" == text:
                info['group'] = all_tds[i+1].get_text(strip=True)

            elif "GPA" == text:
                info['gpa'] = all_tds[i+1].get_text(strip=True)

            elif "Institute" == text:
                info['institute'] = all_tds[i+1].get_text(strip=True)

        subjects = []

        rows = soup.find_all("tr")

        for row in rows:

            cols = row.find_all("td")

            if (
                len(cols) >= 3
                and cols[0].get_text(strip=True).isdigit()
            ):

                subjects.append(
                    f"{cols[0].get_text(strip=True)} → "
                    f"{cols[1].get_text(strip=True)} → "
                    f"{cols[2].get_text(strip=True)}"
                )

        return info, subjects

    except:
        return None, None

# =========================================================
# BUTTONS
# =========================================================

def phone_buttons(phone):

    keyboard = []

    if len(phone) >= 11:

        keyboard.append([
            InlineKeyboardButton(
                "🟢 WhatsApp",
                url=f"https://wa.me/88{phone}"
            ),

            InlineKeyboardButton(
                "🔵 Telegram",
                url=f"https://t.me/+88{phone}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "👉 Next 500",
            callback_data="next_500"
        )
    ])

    return InlineKeyboardMarkup(keyboard)

def next_button():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👉 Next 500",
                callback_data="next_500"
            )
        ]
    ])

# =========================================================
# SONALI OUTPUT
# =========================================================

async def send_sonali_result(
    update_or_query,
    data_list
):

    msg_source = (
        update_or_query.message
        if hasattr(update_or_query, 'message')
        else update_or_query
    )

    final_output = (
        "🏛️ <b>XI Admission Fee Result</b>\n\n"
    )

    phones = []

    for i, data in enumerate(data_list, 1):

        final_output += (
            f"🎯 Result {i}\n"

            f"<pre>"
            f"🆔 Transaction Id: {data['id']}\n"
            f"👤 Student Name: {data['name']}\n"
            f"🔢 Roll: {data['roll']}\n"
            f"🏫 Board: {data['board']}\n"
            f"📆 Year: {data['year']}\n"
            f"📳 Contact No: {data['contact']}\n"
            f"📝 Fee Type: {data['fee_type']}\n"
            f"💰 Fee Amount: {data['amount']}\n"
            f"📅 Date: {data['date']}"
            f"</pre>\n\n"
        )

        p = data["contact"].strip()[-11:]

        if len(p) >= 11 and p not in phones:
            phones.append(p)

    await msg_source.reply_text(
        final_output,
        parse_mode="HTML",
        reply_markup=phone_buttons(phones[0]) if phones else next_button()
    )

# =========================================================
# SSC OUTPUT
# =========================================================

async def send_ssc_result(
    update_or_query,
    roll,
    marksheet
):

    msg_source = (
        update_or_query.message
        if hasattr(update_or_query, 'message')
        else update_or_query
    )

    info, subjects = marksheet

    sub_text = "\n".join(subjects)

    final_msg = (
        f"🧑‍🎓 <b>STUDENT INFORMATION</b>\n"
        f"━━━━━━━━━━━━━━\n\n"

        f"👤 Name: {info.get('name')}\n"
        f"👨 Father: {info.get('father')}\n"
        f"👩 Mother: {info.get('mother')}\n"

        f"\n━━━━━━━━━━━━━━\n"
        f"📘 <b>SSC RESULT 2025</b>\n"
        f"━━━━━━━━━━━━━━\n\n"

        f"🆔 Roll No: {roll}\n"
        f"🏫 Board: CUMILLA\n"
        f"📚 Group: {info.get('group')}\n"
        f"📊 Result: GPA: {info.get('gpa')}\n"

        f"🏫 Institute: "
        f"{info.get('institute')}\n\n"

        f"📊 <b>SUBJECTS</b>\n"
        f"━━━━━━━━━━━━━━\n"

        f"<pre>{sub_text}</pre>"
    )

    await msg_source.reply_text(
        final_msg,
        parse_mode="HTML",
        reply_markup=next_button()
    )

# =========================================================
# MASTER OUTPUT
# =========================================================

async def send_master_result(
    update_or_query,
    sonali_list,
    marksheet
):

    msg_source = (
        update_or_query.message
        if hasattr(update_or_query, 'message')
        else update_or_query
    )

    info, subjects = marksheet

    sub_text = "\n".join(subjects)

    final_output = ""

    phones = []

    for i, sonali in enumerate(sonali_list, 1):

        final_output += (
            f"🧑‍🎓 <b>STUDENT INFORMATION</b>\n"
            f"━━━━━━━━━━━━━━\n\n"

            f"🎯 Result {i}\n\n"

            f"🆔 Transaction Id: {sonali['id']}\n"
            f"👤 Name: {info.get('name')}\n"
            f"👨 Father: {info.get('father')}\n"
            f"👩 Mother: {info.get('mother')}\n"

            f"\n━━━━━━━━━━━━━━\n"
            f"📘 <b>SSC RESULT 2025</b>\n"
            f"━━━━━━━━━━━━━━\n\n"

            f"🔢 Roll: {sonali['roll']}\n"
            f"🏫 Board: CUMILLA\n"
            f"📚 Group: {info.get('group')}\n"
            f"📆 Year: {sonali['year']}\n"

            f"📊 Result: GPA: {info.get('gpa')}\n"

            f"📳 Contact No: {sonali['contact']}\n"
            f"📝 Fee Type: {sonali['fee_type']}\n"
            f"💰 Fee Amount: {sonali['amount']}\n"
            f"📅 Date: {sonali['date']}\n"

            f"🏫 Institute: "
            f"{info.get('institute')}\n\n"

            f"📊 <b>SUBJECTS</b>\n"
            f"━━━━━━━━━━━━━━\n"

            f"<pre>{sub_text}</pre>\n\n"
        )

        p = sonali["contact"].strip()[-11:]

        if len(p) >= 11 and p not in phones:
            phones.append(p)

    await msg_source.reply_text(
        final_output,
        parse_mode="HTML",
        reply_markup=phone_buttons(phones[0]) if phones else next_button()
    )

# =========================================================
# SEARCH SYSTEM
# =========================================================

async def run_search(
    update_or_query,
    context,
    start_roll,
    end_roll,
    mode
):

    global current_search_id

    this_id = current_search_id

    msg_source = (
        update_or_query.message
        if hasattr(update_or_query, 'message')
        else update_or_query
    )

    status_msg = await msg_source.reply_text(
        "⏳ <b>Scanning...</b>",
        parse_mode="HTML"
    )

    context.user_data["current_end"] = end_roll

    found = 0

    total = end_roll - start_roll + 1

    for i, roll in enumerate(
        range(start_roll, end_roll + 1),
        1
    ):

        if this_id != current_search_id:
            return

        try:

            # =====================================================
            # SONALI MODE
            # =====================================================

            if mode == "sonali":

                search_url = (
                    "https://billpay.sonalibank.com.bd/"
                    f"XIClassAdmission/Home/Search?searchStr={roll}"
                )

                r = session.get(
                    search_url,
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                ids = re.findall(
                    r'Voucher/([A-Za-z0-9\-]+)',
                    r.text
                )

                sonali_results = []

                for tid in set(ids):

                    sonali = get_sonali_data(tid)

                    if (
                        sonali
                        and sonali["name"] != "N/A"
                        and sonali["board"].strip().lower()
                        in ["comilla", "cumilla"]
                    ):

                        sonali_results.append(sonali)

                if sonali_results:

                    found += 1

                    await send_sonali_result(
                        update_or_query,
                        sonali_results
                    )

            # =====================================================
            # SSC MODE
            # =====================================================

            elif mode == "ssc":

                marksheet = fetch_cumilla_result(
                    str(roll)
                )

                if (
                    marksheet
                    and marksheet[0]
                ):

                    found += 1

                    await send_ssc_result(
                        update_or_query,
                        roll,
                        marksheet
                    )

            # =====================================================
            # MASTER MODE
            # =====================================================

            elif mode == "master":

                search_url = (
                    "https://billpay.sonalibank.com.bd/"
                    f"XIClassAdmission/Home/Search?searchStr={roll}"
                )

                r = session.get(
                    search_url,
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                ids = re.findall(
                    r'Voucher/([A-Za-z0-9\-]+)',
                    r.text
                )

                sonali_results = []

                for tid in set(ids):

                    sonali = get_sonali_data(tid)

                    if (
                        sonali
                        and sonali["name"] != "N/A"
                        and sonali["board"].strip().lower()
                        in ["comilla", "cumilla"]
                    ):

                        sonali_results.append(sonali)

                if sonali_results:

                    marksheet = fetch_cumilla_result(
                        sonali_results[0]["roll"]
                    )

                    if (
                        marksheet
                        and marksheet[0]
                    ):

                        found += 1

                        await send_master_result(
                            update_or_query,
                            sonali_results,
                            marksheet
                        )

            # =====================================================

            if i % 5 == 0 or i == total:

                await status_msg.edit_text(
                    f"⏳ <b>Processing</b>\n"
                    f"🔢 Roll: {roll}\n"
                    f"📊 Found: {found}\n"
                    f"✅ Progress: {i}/{total}",
                    parse_mode="HTML"
                )

            await asyncio.sleep(0.1)

        except:
            continue

    await status_msg.delete()

    await msg_source.reply_text(
        f"✅ Done!\n📊 Found Students: {found}"
    )

# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global current_search_id

    current_search_id += 1

    keyboard = [
        ["1️⃣ Sonali Result", "2️⃣ SSC Result"],
        ["3️⃣ Master Result"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🚀 SELECT RESULT MODE",
        reply_markup=reply_markup
    )

# =========================================================
# HANDLE TEXT
# =========================================================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global current_search_id

    text = update.message.text.strip()

    chat_id = update.message.chat.id

    # MODE SELECT

    if text == "1️⃣ Sonali Result":

        user_modes[chat_id] = "sonali"

        await update.message.reply_text(
            "✅ Sonali Result Mode Activated\n\n"
            "📌 Send Roll or Range"
        )

        return

    elif text == "2️⃣ SSC Result":

        user_modes[chat_id] = "ssc"

        await update.message.reply_text(
            "✅ SSC Result Mode Activated\n\n"
            "📌 Send Roll or Range"
        )

        return

    elif text == "3️⃣ Master Result":

        user_modes[chat_id] = "master"

        await update.message.reply_text(
            "✅ Master Result Mode Activated\n\n"
            "📌 Send Roll or Range"
        )

        return

    mode = user_modes.get(chat_id)

    if not mode:

        await update.message.reply_text(
            "❌ First Select Result Mode"
        )

        return

    current_search_id += 1

    try:

        if "-" in text:

            s, e = map(int, text.split("-"))

            if e - s > 2000:

                await update.message.reply_text(
                    "❌ Maximum Range 2000"
                )

                return

            await run_search(
                update,
                context,
                s,
                e,
                mode
            )

        else:

            roll = int(text)

            await run_search(
                update,
                context,
                roll,
                roll,
                mode
            )

    except:

        await update.message.reply_text(
            "❌ Invalid Roll Format"
        )

# =========================================================
# CALLBACK
# =========================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global current_search_id

    query = update.callback_query

    await query.answer()

    chat_id = query.message.chat.id

    if query.data == "next_500":

        current_search_id += 1

        mode = user_modes.get(chat_id)

        last_end = context.user_data.get(
            "current_end",
            0
        )

        await run_search(
            query,
            context,
            last_end + 1,
            last_end + 500,
            mode
        )

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    keep_alive()

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print("MASTER MULTI SYSTEM BOT RUNNING")

    application.run_polling(
        drop_pending_updates=True
    )
