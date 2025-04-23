import os, logging
from datetime import date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, ConversationHandler,
    MessageHandler, filters
)
from notion_service import create_page, update_property

PROP_MAP = {
    'idea':  'Идея',
    'draft': 'Черновик',
    'final': 'Финал'
}

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
logging.basicConfig(level=logging.INFO)

# Состояния разговора
(
    STEP_CHOOSE,     # ждём, что вводит пользователь: idea/draft/final
    STEP_INPUT,      # ждём сам текст идеи, черновика или финала
    STEP_DATE        # ждём дату напоминания
) = range(3)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь любую из команд:\n"
        "/idea — сохранить идею\n"
        "/draft — сохранить черновик\n"
        "/final — сохранить финал\n"
        "После текста бот спросит дату напоминания."
    )

async def entry(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Общий вход для /idea, /draft, /final."""
    cmd = update.message.text.split()[0][1:]  # "idea", "draft" или "final"
    ctx.user_data['mode'] = cmd                   # запомним, что сейчас сохраняем
    ctx.user_data['page_id'] = create_page()  # если нет строки — создаём
    await update.message.reply_text(f"Введи текст для {cmd}.")
    return STEP_INPUT

async def save_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    mode = ctx.user_data['mode']
    text = update.message.text.strip()
    prop = PROP_MAP[mode]                     # 'Идея' / 'Черновик' / 'Финал'
    update_property(ctx.user_data['page_id'], prop, text)
    await update.message.reply_text('Текст сохранён. Укажи дату напоминания (YYYY-MM-DD).')
    return STEP_DATE

async def save_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Получили дату, валидируем и сохраняем её."""
    raw = update.message.text.strip().replace('.', '-').replace('/', '-')
    try:
        date.fromisoformat(raw)
    except ValueError:
        return await update.message.reply_text("Неверный формат. Вводи YYYY-MM-DD.")
    update_property(ctx.user_data['page_id'], 'Напоминание', raw)
    await update.message.reply_text("Напоминание установлено. Готово! 😊")
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена. Начни заново /idea, /draft или /final.")
    return ConversationHandler.END

if __name__ == '__main__':
    conv = ConversationHandler(
        entry_points=[
            CommandHandler('idea', entry),
            CommandHandler('draft', entry),
            CommandHandler('final', entry),
        ],
        states={
            STEP_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_text)],
            STEP_DATE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, save_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)
    app.run_polling(drop_pending_updates=True)
