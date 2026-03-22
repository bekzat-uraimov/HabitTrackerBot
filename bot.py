from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler, PicklePersistence
)
from app import PixelaUser, PixelaGraph, PixelaPixel


# Tiny server to keep Render happy
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200);
        self.end_headers();
        self.wfile.write(b"Bot is alive!")


def run_health_check():
    try:
        server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
        server.serve_forever()
    except Exception:
        pass


threading.Thread(target=run_health_check, daemon=True).start()

load_dotenv()

# States for 2 habits
N1, C1, U1, N2, C2, U2, LOG_VAL = range(7)


async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Main menu"),
        BotCommand("register", "New account: /register user token"),
        BotCommand("login", "Login & Sync: /login user token"),
        BotCommand("custom", "Setup 2 habits"),
        BotCommand("done", "Log a habit"),
        BotCommand("view", "See your graphs"),
        BotCommand("logout", "Switch account")
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Habit Tracker Online**\n\nCommands:\n/register [user] [token] - Create new account\n/login [user] [token] - Sync existing account\n/done - Log your habits")


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        return await update.message.reply_text("❌ Usage: /register username token")

    user = PixelaUser(args[0], args[1])
    res = user.create_user()
    if res.get('isSuccess'):
        context.user_data['user'] = user
        await update.message.reply_text("✅ Account created! Now use /custom to set up your 2 habits.")
    else:
        await update.message.reply_text(f"❌ Error: {res.get('message')}")


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        return await update.message.reply_text("❌ Usage: /login username token")

    user = PixelaUser(args[0], args[1])
    graphs = user.get_graphs()

    if isinstance(graphs, list):
        context.user_data['user'] = user
        # This part fixes the 'Not Found' error by mapping existing names
        for i, g in enumerate(graphs[:2]):
            context.user_data[f'n{i + 1}'] = g['name']
            context.user_data[f'u{i + 1}'] = g['unit']
        await update.message.reply_text(f"✅ Synced {len(graphs)} habits! Use /done to log.")
    else:
        await update.message.reply_text("❌ Failed to sync. Check your credentials.")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'user' not in context.user_data:
        return await update.message.reply_text("⚠️ Please /login or /register first!")

    # Auto-recovery if Render cleared memory
    if 'n1' not in context.user_data:
        user = context.user_data['user']
        graphs = user.get_graphs()
        for i, g in enumerate(graphs[:2]):
            context.user_data[f'n{i + 1}'] = g['name']
            context.user_data[f'u{i + 1}'] = g['unit']

    n1 = context.user_data.get('n1', "Habit 1")
    n2 = context.user_data.get('n2', "Habit 2")

    kb = [[InlineKeyboardButton(n1, callback_data='g1')],
          [InlineKeyboardButton(n2, callback_data='g2')]]
    await update.message.reply_text("Which habit did you finish?", reply_markup=InlineKeyboardMarkup(kb))


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['current_g'] = query.data
    unit = context.user_data.get('u1' if query.data == 'g1' else 'u2', 'units')
    await query.edit_message_text(f"How many {unit} did you complete?")
    return LOG_VAL


async def log_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    gid = context.user_data.get('current_g')
    user = context.user_data.get('user')

    pixel = PixelaPixel(user, gid)
    if pixel.update(val):
        await update.message.reply_text(f"✅ Success! Logged {val} to {gid}.")
    else:
        await update.message.reply_text("❌ Error: Graph not found. Try running /custom.")
    return ConversationHandler.END


# --- Customization logic ---
async def start_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'user' not in context.user_data:
        return await update.message.reply_text("Please /login first.")
    await update.message.reply_text("Setting up Habit 1. What is the name? (e.g. Coding)")
    return N1


async def get_n1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['n1'] = update.message.text
    await update.message.reply_text("Color for Habit 1? (shibafu, momiji, sora, ichigo)")
    return C1


async def get_c1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c1'] = update.message.text
    await update.message.reply_text("Unit? (e.g. hours, km)")
    return U1


async def get_u1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u1'] = update.message.text
    await update.message.reply_text("Setting up Habit 2. Name?")
    return N2


async def get_n2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['n2'] = update.message.text
    await update.message.reply_text("Color for Habit 2?")
    return C2


async def get_c2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c2'] = update.message.text
    await update.message.reply_text("Unit for Habit 2?")
    return U2


async def finish_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u2'] = update.message.text
    user = context.user_data['user']
    g = PixelaGraph(user)

    # Create/Update g1 and g2
    g.create("g1", context.user_data['n1'], context.user_data['c1'], context.user_data['u1'])
    g.create("g2", context.user_data['n2'], context.user_data['c2'], context.user_data['u2'])

    await update.message.reply_text("✨ Habits configured! Use /done to log.")
    return ConversationHandler.END


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Logged out.")


async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'user' not in context.user_data: return
    user = context.user_data['user']
    await update.message.reply_text(
        f"📊 Graphs:\nHabit 1: https://pixe.la/v1/users/{user.username}/graphs/g1.html\nHabit 2: https://pixe.la/v1/users/{user.username}/graphs/g2.html")


if __name__ == '__main__':
    persistence = PicklePersistence(filepath='data.pickle')
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).persistence(persistence).post_init(
        post_init).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('custom', start_custom)],
        states={
            N1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_n1)],
            C1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_c1)],
            U1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_u1)],
            N2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_n2)],
            C2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_c2)],
            U2: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_custom)],
            LOG_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_value)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("view", view))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_choice, pattern='^g[1-2]$'))

    app.run_polling()