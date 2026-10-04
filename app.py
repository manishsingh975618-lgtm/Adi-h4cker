import telebot
from telebot import types
import requests

BOT_TOKEN = "8656166996:AAEuoQ3XUNeO-xYHQs028DAjXEIABjJmIDY"
bot = telebot.TeleBot(BOT_TOKEN)

# Welcome Video & Text Config
START_VIDEO_FILE_ID = "BAACAgUAAxkBAAIFEWrCUGwV-ZsNurKTFlRPePHK92YFAAK3IgACVJ0RVkw0yojv6_cBPQQ"

WELCOME_CAPTION = """
✨ ** 𝐀𝐃𝐈𝐓𝐘𝐀 𝐇𝟒𝐂𝐊𝐄𝐑 𝐁𝐎𝐓** ✨

━━━━━━━━━━━━━━━━━━━━━
👋 Welcome adi bot!
Click /start kare or option select kre.
━━━━━━━━━━━━━━━━━━━━━
"""

# Main Menu Keyboard
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Number Info")
    btn2 = types.KeyboardButton("🆔 Aadhaar")
    markup.add(btn1, btn2)
    return markup

# Updated Start Command Handler (With Video & Fancy Text)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.send_video(
            chat_id=message.chat.id,
            video=START_VIDEO_FILE_ID,
            caption=WELCOME_CAPTION,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        # Fallback agar video send hone me koi issue aaye
        bot.send_message(
            message.chat.id, 
            WELCOME_CAPTION, 
            parse_mode="Markdown", 
            reply_markup=main_menu_keyboard()
        )

@bot.message_handler(func=lambda msg: msg.text in ["📱 Number Info", "🆔 Aadhaar"])
def ask_input(message):
    service_name = "Mobile number" if message.text == "📱 Number Info" else "Aadhaar number"
    msg = bot.send_message(
        message.chat.id, 
        f"📝 {service_name} bhej 👇", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_search)

def clean_val(val):
    if not val or str(val).strip().lower() in ["none", "null", ""]:
        return "N/A"
    return str(val).strip()

def find_records(data):
    """API response mein se list/records extract karne ke liye flexible function"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["results", "result", "data", "records", "response"]:
            if key in data:
                res = data[key]
                if isinstance(res, list) and len(res) > 0:
                    return res
                elif isinstance(res, dict):
                    sub_res = find_records(res)
                    if sub_res:
                        return sub_res
        if any(k in data for k in ["name", "phoneNumber", "aadharNumber", "fathersName"]):
            return [data]
    return []

def process_search(message):
    query = message.text.strip()
    loading_msg = bot.send_message(message.chat.id, "Searching... 🔍")
    
    try:
        url = f"https://patel-hiteck-api.vercel.app/search?q={query}"
        response = requests.get(url, timeout=35)
        
        if response.status_code == 200:
            data = response.json()
            
            results = find_records(data)

            if not results:
                bot.edit_message_text(
                    "❌ Is query ke liye koi record nahi mila.", 
                    chat_id=message.chat.id, 
                    message_id=loading_msg.message_id
                )
                bot.send_message(message.chat.id, "Select Menu:", reply_markup=main_menu_keyboard())
                return

            output = f"💀 ✈️ **Search Results for:** `{query}` 💀\n"
            output += f"📊 **Total Records Found:** {len(results)}\n"
            output += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for idx, item in enumerate(results, 1):
                if not isinstance(item, dict):
                    continue
                    
                name = clean_val(item.get("name"))
                father = clean_val(item.get("fathersName") or item.get("father_name") or item.get("father"))
                phone = clean_val(item.get("phoneNumber") or item.get("mobile") or item.get("phone"))
                aadhaar = clean_val(item.get("aadharNumber") or item.get("aadhaar") or item.get("uid"))
                other_num = clean_val(item.get("otherNumber"))
                address = clean_val(item.get("address"))
                
                if address != "N/A":
                    address = address.replace("!", " ").strip()

                output += f"👤 **Record #{idx}**\n"
                output += f"• **Name:** {name}\n"
                output += f"• **Father's Name:** {father}\n"
                output += f"• **Phone:** {phone}\n"
                output += f"• **Aadhaar:** {aadhaar}\n"
                output += f"• **Other Number:** {other_num}\n"
                output += f"• **Address:** {address}\n"
                output += "━━━━━━━━━━━━━━━━━━━━━\n\n"

            if len(output) > 4000:
                output = output[:3900] + "\n\n⚠️ *Response shortened due to character limit.*"

            bot.edit_message_text(
                output, 
                chat_id=message.chat.id, 
                message_id=loading_msg.message_id, 
                parse_mode="Markdown"
            )
            
        else:
            bot.edit_message_text(
                f"❌ Server Error: Status Code {response.status_code}", 
                chat_id=message.chat.id, 
                message_id=loading_msg.message_id
            )

    except requests.exceptions.Timeout:
        bot.edit_message_text(
            "⏳ **API Time Out:** Server ne slow response diya, dobara try karein.", 
            chat_id=message.chat.id, 
            message_id=loading_msg.message_id,
            parse_mode="Markdown"
        )
            
    except Exception as e:
        bot.edit_message_text(
            f"⚠ Error: {str(e)}", 
            chat_id=message.chat.id, 
            message_id=loading_msg.message_id
        )

    bot.send_message(
        message.chat.id, 
        "Done:", 
        reply_markup=main_menu_keyboard()
    )

bot.infinity_polling()
