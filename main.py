import logging
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === Настройки ===
BOT_TOKEN = "8028052304:AAFETr-_12avRBGhc2oj2-woXIyfjof9gE4"  # ⚠️ Не публикуй его нигде!
GROUP_CHAT_ID = -1001234567890  # ⚠️ Укажи здесь ИД группы, куда бот должен отправлять отчёт

# === Пункты чек-листа ===
checklist_items = [
    "Проветрить помещение",
    "Включить освещение и телевизор (видео с камином)",
    "Загрузить полотенценагреватель и воскоплав",
    "Проверить расходники на рабочих местах",
    "Проверить конфеты для гостей",
    "Проверить запасы в «баре»",
    "Подготовить кофе-машину",
    "Протереть зону ожидания",
    "Проверить туалет",
    "Протереть зеркала и стекла",
    "Проверить записи на 3-4 дня вперёд",
    "Проверить график мастеров",
    "Запостить сторис в соцсетях",
    "Ответить на сообщения / звонки",
    "Провести инвентаризацию"
]

# === Переменные состояний ===
ASKING, WAITING_PHOTO = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'] = []
    context.user_data['step'] = 0
    await update.message.reply_text(f"Привет, {update.effective_user.first_name}! Давай заполним чек-лист.")
    await update.message.reply_text(f"{checklist_items[0]}\n\nОтветьте: ✅ или ❌")
    return ASKING


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    if answer not in ["✅", "❌"]:
        await update.message.reply_text("Пожалуйста, ответьте смайликом ✅ или ❌")
        return ASKING

    context.user_data['answers'].append(answer)
    context.user_data['step'] += 1

    if context.user_data['step'] >= len(checklist_items):
        await update.message.reply_text("Спасибо! Теперь отправьте фото готового зала или напишите /skip, если хотите пропустить.")
        return WAITING_PHOTO
    else:
        next_question = checklist_items[context.user_data['step']]
        await update.message.reply_text(f"{next_question}\n\nОтветьте: ✅ или ❌")
        return ASKING


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_report(context, update, photo=None)
    await update.message.reply_text("Отчёт без фото отправлен.")
    return ConversationHandler.END


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    context.user_data['photo'] = photo_file
    await send_report(context, update, photo=photo_file)
    await update.message.reply_text("Отчёт с фото отправлен.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заполнение чек-листа отменено.")
    return ConversationHandler.END


async def send_report(context: ContextTypes.DEFAULT_TYPE, update: Update, photo=None):
    user = update.effective_user.first_name
    answers = context.user_data['answers']
    report_lines = [f"📝 *Чек-лист открытия смены* от *{user}*\n"]
    for item, answer in zip(checklist_items, answers):
        report_lines.append(f"- {item}: {answer}")
    report_text = "\n".join(report_lines)

    try:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=report_text, parse_mode="Markdown")

        if photo:
            await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo.file_id)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Отчёт создан, но не удалось отправить в группу. Ошибка: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, handle_photo),
                CommandHandler("skip", skip_photo)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)

    print("✅ Бот запущен. Ожидает команды /start...")
    app.run_polling()


if __name__ == '__main__':
    main()
