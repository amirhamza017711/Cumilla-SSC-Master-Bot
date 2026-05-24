import telebot
import os

# আমীর ভাই, আপনার সেই পরিচিত টেস্ট টোকেন
BOT_TOKEN = "7993443657:AAG70xknlViwpbfQNDukUMTQUQLZDqJx7D4"
bot = telebot.TeleBot(BOT_TOKEN)

# আপনার আপলোড করা ফাইলগুলোর তালিকা (যা ফোল্ডারে আছে)
KNOWLEDGE_FILES = [
    "HID.md", "vaxEPI.md", "Telemedicine.md", "SHR.md", 
    "HRIS.md", "CRVS.md", "openmrs.md", "MIS.md", 
    "ICD11.md", "PrivacyPolicySHR.md", "eappointment.md"
]

def search_in_files(query):
    results = []
    query = query.lower()
    
    for filename in KNOWLEDGE_FILES:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if query in content.lower():
                    # তথ্য পাওয়া গেলে ফাইলের নামসহ প্রথম কিছু অংশ দেখাবে
                    snippet = content[content.lower().find(query):content.lower().find(query)+500]
                    results.append(f"📄 **উৎস:** {filename}\n---\n...{snippet}...")
    
    return results

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 আমীর ভাই, আপনার 'স্মার্ট স্বাস্থ্য বট' এখন সচল! 🔥\n\n"
                          "আপনি স্বাস্থ্য অধিদপ্তরের যেকোনো বিষয় লিখে সার্চ দিন।\n"
                          "যেমন: NID, Vaccine, Hospital, Health ID ইত্যাদি।")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    
    found_data = search_in_files(query)
    
    if found_data:
        for info in found_data[:3]: # টপ ৩টি রেজাল্ট দেখাবে
            bot.send_message(message.chat.id, info, parse_mode="Markdown")
    else:
        bot.reply_to(message, "দুঃখিত আমীর ভাই, এই কিউওয়ার্ড দিয়ে কোনো তথ্য ফাইলগুলোতে পাওয়া যায়নি।")

print("🚀 বট চালু হয়েছে... আমীর ভাই, এখন টেস্ট করে দেখুন!")
bot.polling()