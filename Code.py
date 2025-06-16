from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Токен 
TOKEN = "7620194484:AAFpjOHCPlYI_ok11m4Jy2uWt9-nYXm1Bwg"

# Состояния для ConversationHandler
SELECTING_OPTION, CHOOSING_FLIGHTS, CHOOSING_HOTELS = range(3)

# Приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я ваш помощник в путешествиях.\n"
        "Я могу помочь найти подходящий отель или билеты на самолёт по выгодной цене!\n\n"
        "Чем могу помочь?",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_main_options(update)
    return SELECTING_OPTION

# Показать основные опции
async def show_main_options(update: Update):
    reply_keyboard = [["Билеты", "Отели"], ["Мультивыбор"]]
    await update.message.reply_text(
        "Выберите опцию из меню ниже:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Показать опции билетов
async def show_flight_options(update: Update):
    reply_keyboard = [["Поиск билетов", "Избранное билетов"], ["Назад"]]
    await update.message.reply_text(
        "Вы в разделе 'Билеты'. Здесь вы можете:\n"
        "- Найти авиабилеты (Поиск билетов)\n"
        "- Посмотреть сохранённые варианты (Избранное билетов)\n\n"
        "Или вернуться назад:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Показать опции отелей
async def show_hotel_options(update: Update):
    reply_keyboard = [["Поиск отелей", "Избранное отелей"], ["Назад"]]
    await update.message.reply_text(
        "Вы в разделе 'Отели'. Здесь вы можете:\n"
        "- Найти подходящий отель (Поиск отелей)\n"
        "- Посмотреть сохранённые варианты (Избранное отелей)\n\n"
        "Или вернуться назад:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Обработка мультивыбора
async def multi_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Сначала билеты", "Сначала отели"], ["Назад"]]
    await update.message.reply_text(
        "Вы выбрали 'Мультивыбор'. Мы можем:\n"
        "1. Сначала найти билеты, а затем подобрать отели\n"
        "2. Сначала выбрать отель, а затем найти билеты\n\n"
        "Какой вариант вам удобнее?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_FLIGHTS if update.message.text == "Сначала билеты" else CHOOSING_HOTELS

# Поиск билетов для мультивыбора
async def choose_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Поиск билетов":
        await update.message.reply_text(
            "Давайте найдём билеты. Укажите:\n"
            "- Город отправления\n"
            "- Город назначения\n"
            "- Даты поездки\n"
            "- Количество пассажиров"
        )
        return CHOOSING_FLIGHTS
    
    # После поиска билетов предлагаем найти отели
    reply_keyboard = [["Найти отели"], ["Назад"]]
    await update.message.reply_text(
        "Отлично! Теперь можем подобрать отели для вашей поездки.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_HOTELS

# Поиск отелей для мультивыбора
async def choose_hotels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Поиск отелей":
        await update.message.reply_text(
            "Давайте найдём отели. Укажите:\n"
            "- Город\n"
            "- Даты проживания\n"
            "- Количество гостей\n"
            "- Количество номеров"
        )
        return CHOOSING_HOTELS
    
    # После поиска отелей предлагаем найти билеты (если начали с отелей)
    if context.user_data.get('started_with_hotels'):
        reply_keyboard = [["Найти билеты"], ["Назад"]]
        await update.message.reply_text(
            "Отлично! Теперь можем подобрать билеты для вашей поездки.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_FLIGHTS
    else:
        # Завершаем процесс
        reply_keyboard = [["Завершить бронирование"], ["Назад"]]
        await update.message.reply_text(
            "Всё готово! Вы можете завершить бронирование.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return ConversationHandler.END

# Обработка кнопки Назад
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вы вернулись в главное меню.",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_main_options(update)
    return SELECTING_OPTION

# Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Билеты":
        await show_flight_options(update)
        return SELECTING_OPTION
    elif text == "Отели":
        await show_hotel_options(update)
        return SELECTING_OPTION
    elif text == "Мультивыбор":
        return await multi_search(update, context)
    elif text == "Поиск билетов":
        return await choose_flights(update, context)
    elif text == "Избранное билетов":
        await update.message.reply_text(
            "Ваши сохранённые билеты:\n(здесь будет список)"
        )
        return SELECTING_OPTION
    elif text == "Поиск отелей":
        return await choose_hotels(update, context)
    elif text == "Избранное отелей":
        await update.message.reply_text(
            "Ваши сохранённые отели:\n(здесь будет список)"
        )
        return SELECTING_OPTION
    elif text == "Назад":
        return await back_to_main(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для выбора.",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_main_options(update)
        return SELECTING_OPTION

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_OPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
            CHOOSING_FLIGHTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_flights)
            ],
            CHOOSING_HOTELS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_hotels)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
