import os
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler, PicklePersistence
)
from app import PixelaUser, PixelaGraph, PixelaPixel

load_dotenv()

# States for 2 habits
N1, C1, U1, N2, C2, U2, LOG_VAL = range(7)
COLORS = [['shibafu (Green)', 'momiji (Red)'], ['sora (Blue)', 'ichigo (Pink)']]
UNITS = [['km', 'min', 'count', '$']]


async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Main menu"),
        BotCommand("register", "New account: /register user token"),
        BotCommand("login", "Login & Sync: /login user token"),
        BotCommand("custom", "Setup 2 habits"),
        BotCommand("done", "Log progress"),
        BotCommand("view", "Show links"),
        BotCommand("logout", "Clear session")
    ])


async def start(u, c):
    await u.message.reply_text(
        "🚀 **Habit Tracker (2-Habit Edition)**\n\n"
        "1️⃣ `/register user token` (New User)\n"
        "2️⃣ `/login user token` (Existing User)\n"
        "3️⃣ `/custom` (Setup Names/Units)\n"
        "4️⃣ `/done` (Log Progress)",
        parse_mode="Markdown"
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: `/register username token`")
        return
    un, tk = context.args[0], context.args[1]
    user = PixelaUser(un, tk)
    res = user.create_user()
    if res.get("isSuccess") or "already exists" in str(res.get("message")):
        context.user_data.clear()
        context.user_data["username"], context.user_data["token"] = un, tk
        await update.message.reply_text(f"✅ Registered **{un}**! Now run /custom to set your habits.",
                                        parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ Error: {res.get('message')}")


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: `/login username token`")
        return

    un, tk = context.args[0], context.args[1]
    user = PixelaUser(un, tk)

    await update.message.reply_text(f"⏳ Syncing habits for {un}...")
    graphs = user.get_graphs()

    context.user_data.clear()
    context.user_data["username"], context.user_data["token"] = un, tk

    if graphs:
        # Sort graphs so g1 comes before g2, or just take the first two found
        for i, graph in enumerate(graphs[:2]):
            idx = i + 1
            # We save the ACTUAL ID from Pixela so the bot knows how to log to it
            real_id = graph.get("id")
            context.user_data[f"g{idx}_id"] = real_id
            context.user_data[f"n{idx}"] = graph.get("name")
            context.user_data[f"u{idx}"] = graph.get("unit")
            print(f"✅ Found and Synced: {real_id} as {graph.get('name')}")

        await update.message.reply_text(f"✅ Sync Complete! {len(graphs[:2])} habits loaded.")
    else:
        await update.message.reply_text(f"⚠️ No habits found on Pixela for **{un}**. Run /custom to create them.",
                                        parse_mode="Markdown")


async def logout(u, c):
    c.user_data.clear()
    await u.message.reply_text("👋 Logged out. Memory cleared.")


# --- CUSTOM SETUP (2 HABITS) ---
async def start_custom(u, c):
    if "username" not in c.user_data:
        await u.message.reply_text("Login first!");
        return ConversationHandler.END
    await u.message.reply_text("Habit #1 Name?");
    return N1


async def get_n1(u, c): c.user_data['n1'] = u.message.text; await u.message.reply_text("Color?",
                                                                                       reply_markup=ReplyKeyboardMarkup(
                                                                                           COLORS,
                                                                                           one_time_keyboard=True)); return C1


async def get_c1(u, c): c.user_data['c1'] = u.message.text.split(' ')[0]; await u.message.reply_text("Unit?",
                                                                                                     reply_markup=ReplyKeyboardMarkup(
                                                                                                         UNITS,
                                                                                                         one_time_keyboard=True)); return U1


async def get_u1(u, c): c.user_data['u1'] = u.message.text; await u.message.reply_text("Habit #2 Name?",
                                                                                       reply_markup=ReplyKeyboardRemove()); return N2


async def get_n2(u, c): c.user_data['n2'] = u.message.text; await u.message.reply_text("Color?",
                                                                                       reply_markup=ReplyKeyboardMarkup(
                                                                                           COLORS,
                                                                                           one_time_keyboard=True)); return C2


async def get_c2(u, c): c.user_data['c2'] = u.message.text.split(' ')[0]; await u.message.reply_text("Unit?",
                                                                                                     reply_markup=ReplyKeyboardMarkup(
                                                                                                         UNITS,
                                                                                                         one_time_keyboard=True)); return U2


async def finish_custom(u, c):
    c.user_data['u2'] = u.message.text
    await u.message.reply_text("⏳ Syncing 2 habits to Pixela...", reply_markup=ReplyKeyboardRemove())
    user = PixelaUser(c.user_data['username'], c.user_data['token'])
    gt = PixelaGraph(user)
    for i in range(1, 3):
        gt.create(f"g{i}", c.user_data[f'n{i}'], c.user_data[f'c{i}'], c.user_data[f'u{i}'])
        time.sleep(1)
    await u.message.reply_text("✅ Setup complete! Use /done.");
    return ConversationHandler.END


# --- LOGGING ---
async def done(u, c):
    if "username" not in c.user_data: return
    n1, n2 = c.user_data.get('n1', 'Habit 1'), c.user_data.get('n2', 'Habit 2')
    kb = [[InlineKeyboardButton(n1, callback_data='g1')], [InlineKeyboardButton(n2, callback_data='g2')]]
    await u.message.reply_text("Select habit:", reply_markup=InlineKeyboardMarkup(kb))


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # query.data is 'g1' or 'g2'
    choice_idx = query.data[-1]  # '1' or '2'

    # Get the real ID we stored during login (e.g., 'g1' or 'my-habit')
    actual_id = context.user_data.get(f"g{choice_idx}_id", query.data)
    context.user_data['active_graph'] = actual_id

    unit = context.user_data.get(f'u{choice_idx}', 'units')
    await query.edit_message_text(f"How many **{unit}** today?", parse_mode="Markdown")
    return LOG_VAL


async def log_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    user = PixelaUser(context.user_data['username'], context.user_data['token'])
    pixel = PixelaPixel(user, context.user_data['active_graph'])
    await update.message.reply_text(f"⏳ Logging {val}...")
    pixel.update(val)
    await update.message.reply_text(f"🎯 Success!")
    return ConversationHandler.END


async def view(u, c):
    un = c.user_data.get('username')
    if not un: return
    msg = "\n".join(
        [f"• {c.user_data.get(f'n{i}', f'H{i}')}: [Link](https://pixe.la/v1/users/{un}/graphs/g{i}.html)" for i in
         range(1, 3)])
    await u.message.reply_text(f"📊 **Heatmaps:**\n{msg}", parse_mode="Markdown")


if __name__ == '__main__':
    persistence = PicklePersistence(filepath='data.pickle')
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).persistence(persistence).post_init(
        post_init).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('custom', start_custom), CallbackQueryHandler(handle_choice, pattern='^g[1-2]$')],
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

    print("🚀 App Online (2-Habit Mode)")
    app.run_polling()