import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler
import schedule
import time
import json
import random

load_dotenv()

TOKEN = os.getenv('TOKEN')
BOOK_FILE = "book.txt"
SUBSCRIBERS_FILE = "subscribers.json"

def load_quotes():
    try:
        with open(BOOK_FILE, "r") as f:
            text = f.read().strip()
            entries = text.split('\n\n')
            quotes = []
            for entry in entries:
                parts = entry.split('|||>')
                if len(parts) == 2:
                    quote, attribution = [p.strip() for p in parts]
                    full_quote = f"{quote}\n\n— {attribution}"
                    quotes.append(full_quote)
                else:
                    quotes.append(entry.strip())
            return quotes
    except FileNotFoundError:
        return ["No book found! Add a text file named book.txt."]

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f)

class QuoteCycler:
    def __init__(self):
        self.quotes = load_quotes()
        random.shuffle(self.quotes)
        self.index = 0
        print("Initial shuffled quotes:", self.quotes)

    def get_next_quote(self):
        if not self.quotes:
            return "No excerpts available!"
        quote = self.quotes[self.index]
        self.index += 1
        if self.index >= len(self.quotes):
            random.shuffle(self.quotes)
            self.index = 0
            print("Reshuffled quotes:", self.quotes)
        return quote

quote_cycler = QuoteCycler()

def start(update, context):
    update.message.reply_text("Welcome! Use /subscribe to get book excerpts.")

def subscribe(update, context):
    user_id = update.message.from_user.id
    subscribers = load_subscribers()
    if user_id not in subscribers:
        subscribers.append(user_id)
        save_subscribers(subscribers)
        update.message.reply_text("You’re subscribed! Excerpts every 10 seconds for now.")
    else:
        update.message.reply_text("You’re already subscribed!")

def unsubscribe(update, context):
    user_id = update.message.from_user.id
    subscribers = load_subscribers()
    if user_id in subscribers:
        subscribers.remove(user_id)
        save_subscribers(subscribers)
        update.message.reply_text("You’ve been unsubscribed. No more excerpts!")
    else:
        update.message.reply_text("You’re not subscribed, so nothing to unsubscribe from!")

def send_quote(bot):
    subscribers = load_subscribers()
    print("Subscribers:", subscribers)  # Debug
    quote = quote_cycler.get_next_quote()
    print("Selected quote:", repr(quote))
    if len(quote) > 4096:
        quote = quote[:4093] + "..."
    for user_id in subscribers:
        print(f"Sending to {user_id}")  # Debug
        bot.send_message(chat_id=user_id, text=quote)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))

    schedule.every(10).seconds.do(send_quote, bot=updater.bot)
    print("Scheduler started")  # Debug

    updater.start_polling()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()