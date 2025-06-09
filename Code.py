from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен 
TOKEN = "TOKEN"

# Приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я ваш помощник в путешествиях. Чем могу помочь?",
        reply_markup=ReplyKeyboardRemove()
    )
    # Отправляем клавиатуру с кнопками
    reply_keyboard = [["Билеты", "Отели", "Мультивыбор"]]
    await update.message.reply_text(
        "Выберите опцию:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Обработка текстовых сообщений (кнопок)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Билеты":
        await update.message.reply_text("Вы выбрали раздел 'Билеты'. Что вас интересует?")
    elif text == "Отели":
        await update.message.reply_text("Вы выбрали раздел 'Отели'. Куда вы планируете поехать?")
    elif text == "Мультивыбор":
        await update.message.reply_text("Вы выбрали 'Мультивыбор'. Здесь можно комбинировать параметры.")
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки для выбора.")

def main():
    # Создаем приложение и передаем токен
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()