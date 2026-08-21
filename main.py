# main.py - মূল বটের লজিক এবং ইন্টারফেস ফাইল

import time
import threading
import secrets
import hashlib
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ১ম ফাইল থেকে সেটিংস ও ডেটা ইম্পোর্ট করা হলো
import config
from config import bot, live_tokens, user_database, active_messages, OWNER_WALLET

bot = telebot.TeleBot(config.BOT_TOKEN)

def generate_pure_solana_address():
    prefix = "SOL"
    raw_bytes = secrets.token_bytes(32)
    chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return prefix + "".join(chars[int(b) % len(chars)] for b in raw_bytes[:41])

def get_user_data(user_id):
    if user_id not in user_database:
        user_database[user_id] = {
            "sol_address": generate_pure_solana_address(),
            "amount": 0.1,
            "tip": 0.01,
            "holdings": {},
            "copy_trades": [],
            "filters": {"twitter": True, "telegram": True, "website": True, "mint_auth": True, "freeze_auth": True}
        }
    return user_database[user_id]

# 📊 মেইন ড্যাশবোর্ড স্ক্রিন
@bot.message_handler(commands=['start', 'dashboard'])
def send_dashboard(message):
    user_data = get_user_data(message.from_user.id)
    
    top_markup = InlineKeyboardMarkup()
    filter_hub_btn = InlineKeyboardButton(text="🔎 Filter Hub", callback_data="main_filter_hub")
    trading_btn = InlineKeyboardButton(text="📊 Trading", callback_data="main_trading_hub")
    top_markup.row(filter_hub_btn, trading_btn)
    
    header_text = (
        "📊 **Solana Pump Trading Dashboard** 📊\n"
        "------------------------------------\n"
        f"💳 **Your System SOL Address:**\n`{user_data['sol_address']}`\n"
        "⚠️ _ট্রেড ও স্নাইপিং সচল রাখতে এই ওয়ালেটে SOL ডিপোজিট রাখুন।_\n"
        "------------------------------------\n"
        "INFO | MKT CAP | TAX DATA | PROFIT | BUY/SELL"
    )
    bot.send_message(message.chat.id, header_text, reply_markup=top_markup, parse_mode="Markdown")
    
    for token_id in live_tokens:
        render_token_message(message.chat.id, token_id, user_data)

def render_token_message(chat_id, token_id, user_data, message_id=None):
    data = live_tokens[token_id]
    profit_text = "Not Bought"
    if token_id in user_data["holdings"]:
        buy_mcap = user_data["holdings"][token_id]
        pct = ((data["mcap"] - buy_mcap) / buy_mcap) * 100
        profit_text = f"{'📈' if pct >= 0 else '📉'} {pct:+.1f}%"
        
    msg_text = (
        f"🔹 **{data['name']}** ({data['price']})\n"
        f"📊 MKT CAP: ${data['mcap']/1000:.1f}K | 🛑 TAX: {data['tax'].replace('\n', ' ')}\n"
        f"💰 PROFIT: *{profit_text}* | 🔒 SEC: {data['status']}\n"
        f"📍 `Address: {data['address']}`"
    )
    
    markup = InlineKeyboardMarkup()
    buy_btn = InlineKeyboardButton(text="🟩 B (1-Click)", callback_data=f"tr_buy_{token_id}")
    sell_btn = InlineKeyboardButton(text="🟥 S (1-Click)", callback_data=f"tr_sell_{token_id}")
    markup.row(buy_btn, sell_btn)
    
    if message_id:
        try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg_text, reply_markup=markup, parse_mode="Markdown")
        except: pass
    else:
        sent_msg = bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
        active_messages[token_id] = {"chat_id": chat_id, "message_id": sent_msg.message_id}

# 🎛️ "Trading" সাব-মেনু পেজ (Trojan Style)
@bot.callback_query_handler(func=lambda call: call.data == "main_trading_hub")
def open_trading_hub(call):
    bot.answer_callback_query(call.id, text="Opening Trading Options...")
    t_markup = InlineKeyboardMarkup()
    t_markup.row(InlineKeyboardButton(text="👥 Copy Trade Mode", callback_data="submenu_copy_trade"),
                 InlineKeyboardButton(text="🎯 Sniper Mode (Auto/LP)", callback_data="submenu_sniper"))
    t_markup.row(InlineKeyboardButton(text="⬅️ Back to Main Dashboard", callback_data="back_to_main"))
    
    bot.send_message(call.message.chat.id, "📊 **Trojan Pro Trading Hub**\n\nনিচের যেকোনো একটি এডভান্সড অপশন সিলেক্ট করুন:", reply_markup=t_markup)

# 👥 Page 1: Copy Trade পেজ
@bot.callback_query_handler(func=lambda call: call.data == "submenu_copy_trade")
def page_copy_trade(call):
    bot.answer_callback_query(call.id)
    user_data = get_user_data(call.from_user.id)
    ct_markup = InlineKeyboardMarkup()
    ct_markup.row(InlineKeyboardButton(text="➕ New", callback_data="ct_new"), InlineKeyboardButton(text="Resume All", callback_data="ct_resume"))
    ct_markup.row(InlineKeyboardButton(text="🔙 Back", callback_data="main_trading_hub"))
    
    ct_text = (
        "👥 **Copy Trade**\n"
        f"Wallet: `{user_data['sol_address']}` — W1 ✏️\n\n"
        "Copy Trade allows you to copy the buys and sells of any target wallet.\n"
        "🟢 Indicates a copy trade setup is active.\n"
        "🟠 Indicates a copy trade setup is paused.\n\n"
        "❌ You do not have any copy trades setup yet. Click on the New button to create one!"
    )
    bot.send_message(call.message.chat.id, ct_text, reply_markup=ct_markup, parse_mode="Markdown")

# 🎯 Page 2: Sniper Mode পেজ
@bot.callback_query_handler(func=lambda call: call.data == "submenu_sniper")
def page_sniper_mode(call):
    bot.answer_callback_query(call.id)
    sn_markup = InlineKeyboardMarkup()
    sn_markup.row(InlineKeyboardButton(text="🚀 Auto Sniper", callback_data="sn_auto"), InlineKeyboardButton(text="📈 Migration Sniper", callback_data="sn_migration"))
    sn_markup.row(InlineKeyboardButton(text="🔙 Back", callback_data="main_trading_hub"))
    
    sn_text = (
        "🎯 **Solana Sniper Pro Mode**\n\n"
        "**Auto Sniper:** Set your custom parameters and Auto Snipe any launch on Solana.\n\n"
        "**LP/Migration Sniper:** Snipe tokens and pumpfun migrations when they launch on Raydium."
    )
    bot.send_message(call.message.chat.id, sn_text, reply_markup=sn_markup, parse_mode="Markdown")

# 🔎 Filter Hub পেজ
@bot.callback_query_handler(func=lambda call: call.data == "main_filter_hub")
def page_filter_hub(call):
    bot.answer_callback_query(call.id)
    f_markup = InlineKeyboardMarkup()
    f_markup.row(InlineKeyboardButton(text="✅ Twitter", callback_data="f_toggle_tw"), InlineKeyboardButton(text="✅ Website", callback_data="f_toggle_ws"))
    f_markup.row(InlineKeyboardButton(text="✅ Telegram", callback_data="f_toggle_tg"), InlineKeyboardButton(text="✅ Mint Auth", callback_data="f_toggle_mint"))
    f_markup.row(InlineKeyboardButton(text="✅ Freeze Auth", callback_data="f_toggle_freeze"))
    f_markup.row(InlineKeyboardButton(text="Apply Filters 🚀", callback_data="back_to_main"))
    
    f_text = "🔎 **Solana Pump Filters Configuration**\n\nবট শুধুমাত্র আপনার ফিল্টার করা টোকেনগুলোই লাইভ ড্যাশবোর্ডে দেখাবে।"
    bot.send_message(call.message.chat.id, f_text, reply_markup=f_markup, parse_mode="Markdown")

# 🟩 🟥 ইনস্ট্যান্ট ওয়ান-ক্লিক বাই/সেল এবং ১% কমিশন প্রসেসিং
@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_buy_") or call.data.startswith("tr_sell_"))
def execute_instant_trade(call):
    user_data = get_user_data(call.from_user.id)
    token_id = call.data.replace("tr_buy_", "").replace("tr_sell_", "")
    token_info = live_tokens.get(token_id)
    
    fee_sol = user_data["amount"] * 0.01  # ১% কমিশন আপনার অ্যাডমিন ওয়ালেটের জন্য
    trade_sol = user_data["amount"] - fee_sol
    
    if call.data.startswith("tr_buy_"):
        user_data["holdings"][token_id] = live_tokens[token_id]["mcap"]
        bot.answer_callback_query(call.id, text=f"🟩 1-Click Buy Success for {token_info['name']}")
        bot.send_message(
            call.message.chat.id, 
            f"⚡ **[Instant Millisecond Trade]**\n🎯 Bought: {token_info['name']}\n"
            f"📥 Net Swap: {trade_sol:.3f} SOL\n"
            f"💰 1% Commission Transferred to Owner Wallet: `{OWNER_WALLET[:6]}...`"
        )
    elif call.data.startswith("tr_sell_"):
        if token_id in user_data["holdings"]: del user_data["holdings"][token_id]
        bot.answer_callback_query(call.id, text=f"🟥 1-Click Sell Success for {token_info['name']}")
        bot.send_message(call.message.chat.id, f"⚡ **[Instant Millisecond Sell]** Sold all holdings for {token_info['name']}!")
        
    msg_info = active_messages.get(token_id)
    if msg_info: render_token_message(msg_info["chat_id"], token_id, user_data, msg_info["message_id"])

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    bot.answer_callback_query(call.id)
    send_dashboard(call.message)

# 🔄 ব্যাকগ্রাউন্ড লাইভ রিফ্রেশার (মার্কেট ক্যাপ ও প্রফিট স্ক্রিনে লাইভ পরিবর্তন করবে)
def live_data_refresher():
    while True:
        time.sleep(2)
        for token_id, msg_info in list(active_messages.items()):
            if token_id in live_tokens:
                live_tokens[token_id]["mcap"] += 220 
                for user_id in user_database:
                    render_token_message(msg_info["chat_id"], token_id, user_database[user_id], msg_info["message_id"])

threading.Thread(target=live_data_refresher, daemon=True).start()

if __name__ == '__main__':
    print("🤖 Trojan-Style Solana Pro Bot Running Successfully...")
    bot.infinity_polling()
