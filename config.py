# config.py - বটের সব সেটিংস ও ডেটাবেজ ফাইল

import telebot

BOT_TOKEN = "8862192124:AAHBuWhTdndS0mTBvNWsiTMZs-tEWpTEGfs"
bot = telebot.TeleBot(BOT_TOKEN)
OWNER_WALLET = "BeFY9t9MCLKGP5Ka5qahN9ogzbro5q87iJXgEMLGfWCr"

user_database = {}
active_messages = {}

# পাম্প ডট ফানের লাইভ টোকেন ডেটা
live_tokens = {
    "token_1": {"name": "$Goal", "price": "$0.00404", "mcap": 7200, "tax": "891nS6/33", "status": "🛡️ SAFE", "address": ""},
    "token_2": {"name": "$NGL", "price": "$0.00077", "mcap": 13200, "tax": "371n30/7", "status": "🛡️ SAFE", "address": ""},
    "token_3": {"name": "$LUCY", "price": "$0.00174", "mcap": 6200, "tax": "941n80/14", "status": "🚨 RUG RISK", "address": ""}
}
