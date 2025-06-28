import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# Конфигурация
TOKEN = "8161815639:AAEbO5i_MfBt46pyi0HfTUmlVQxIDdQPtlk"
ADMIN_GROUP_ID = -2684367477  # ID группы, где работает команда /add
LAST_SHOW_ITEMS = 3  # Количество последних элементов для показа

# Состояния бота
(
    MAIN_MENU, FLIGHTS_MENU, HOTELS_MENU,
    PROCESS_FLIGHTS, PROCESS_HOTELS,
    FILTER_FLIGHTS, FILTER_HOTELS
) = range(7)

class ContentAdder:
    def __init__(self, group_chat_id: int):
        self.GROUP_CHAT_ID = group_chat_id
        self.CONTENT_DB_FILE = "content_add_db.json"
        self.content_db = self.load_content_db()
        
        self.group_keyboard = ReplyKeyboardMarkup(
            [["✈️ Добавить авиабилет", "🏨 Добавить отель"], ["❌ Отменить добавление"]],
            resize_keyboard=True
        )

    def load_content_db(self):
        """Загружает базу данных контента из файла"""
        try:
            if Path(self.CONTENT_DB_FILE).exists():
                with open(self.CONTENT_DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке базы данных: {e}")
        
        return {"flights": {}, "hotels": {}}

    def save_content_db(self):
        """Сохраняет базу данных контента в файл"""
        try:
            with open(self.CONTENT_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.content_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении базы данных: {e}")

    async def start_group_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /add в группе"""
        await update.message.reply_text(
            "Выберите тип контента для добавления:",
            reply_markup=self.group_keyboard
        )

    async def start_content_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str):
        """Начинает процесс пошагового добавления контента"""
        context.user_data['adding_content'] = {
            'type': content_type,
            'step': 0,
            'metadata': {
                "title": "Не указано",
                "description": "Не указано",
                "link": "Нет ссылки",
                "price": "Не указана"
            }
        }

        # Добавляем специфичные поля
        if content_type == "flights":
            context.user_data['adding_content']['metadata'].update({
                'airline': "Не указана",
                'departure': "Не указано",
                'destination': "Не указано",
                'date': "Не указана",
                'duration': "Не указана"
            })
        elif content_type == "hotels":
            context.user_data['adding_content']['metadata'].update({
                'location': "Не указано",
                'check_in': "Не указана",
                'check_out': "Не указана",
                'rating': "Не указан",
                'amenities': "Не указаны"
            })

        # Приветственное сообщение
        await update.message.reply_text(
            f"""{'✈️' if content_type == 'flights' else '🏨'} <b>Добавление нового {'авиабилета' if content_type == 'flights' else 'отеля'}</b>

            Давайте заполним информацию шаг за шагом. 
            Можете пропустить любой пункт, отправив "-".""",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
    
        await self.ask_for_next_field(update, context)

    async def ask_for_next_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрашивает следующее поле"""
        content_type = context.user_data['adding_content']['type']
        step = context.user_data['adding_content']['step']
        metadata = context.user_data['adding_content']['metadata']

        # Поля с эмодзи и описаниями
        fields_order = [
            ('title', "📝 <b>Название:</b>\n(Например: <i>Авиабилет в Париж</i> или <i>Отель Marriott</i>)"),
            ('price', "💰 <b>Цена:</b>\n(Например: <i>150$</i> или <i>12000₽</i>)"),
            ('description', "📖 <b>Описание:</b>\n(Краткое описание предложения)")
        ]

        # Специфичные поля для каждого типа
        if content_type == "flights":
            fields_order.extend([
                ('airline', "✈️ <b>Авиакомпания:</b>\n(Например: <i>Aeroflot</i>)"),
                ('departure', "🛫 <b>Откуда:</b>\n(Город вылета, например: <i>Москва</i>)"),
                ('destination', "🛬 <b>Куда:</b>\n(Город прилета, например: <i>Париж</i>)"),
                ('date', "📅 <b>Дата вылета:</b>\n(Например: <i>15.07.2023</i>)"),
                ('duration', "⏱ <b>Длительность полета:</b>\n(Например: <i>3ч 30м</i>)")
            ])
        elif content_type == "hotels":
            fields_order.extend([
                ('location', "📍 <b>Местоположение:</b>\n(Например: <i>Париж, Франция</i>)"),
                ('check_in', "🔑 <b>Дата заезда:</b>\n(Например: <i>15.07.2023</i>)"),
                ('check_out', "🚪 <b>Дата выезда:</b>\n(Например: <i>20.07.2023</i>)"),
                ('rating', "⭐ <b>Рейтинг:</b>\n(Например: <i>4.5/5</i>)"),
                ('amenities', "🛁 <b>Удобства:</b>\n(Например: <i>Wi-Fi, бассейн, завтрак</i>)")
            ])

        if step < len(fields_order):
            field, prompt = fields_order[step]
            context.user_data['adding_content']['current_field'] = field

            await update.message.reply_text(
                prompt,
                parse_mode='HTML'
            )
        else:
            # Все основные поля заполнены, запрашиваем ссылку
            if 'link' not in context.user_data['adding_content']['metadata'] or context.user_data['adding_content']['metadata']['link'] == "Нет ссылки":
                context.user_data['adding_content']['current_field'] = 'link'
                await update.message.reply_text(
                    "🔗 <b>Ссылка на бронирование:</b>\n(URL или \"-\" чтобы пропустить)",
                    parse_mode='HTML'
                )
            else:
                # Ссылка получена, запрашиваем фото
                summary = self._generate_content_summary(metadata, content_type)
                await update.message.reply_text(
                    f"""✅ <b>Информация сохранена!</b>

{summary}

Теперь отправьте фото для этого предложения (или отправьте '-' чтобы пропустить):""",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                context.user_data['adding_content']['step'] = 'awaiting_photo'

    def _generate_content_summary(self, metadata: dict, content_type: str) -> str:
        """Генерирует резюме введенных данных"""
        content_type_name = {
            "flights": "Авиабилет",
            "hotels": "Отель" 
        }[content_type]

        summary = [f"\n📋 <b>{content_type_name}:</b> <i>{metadata['title']}</i>"]

        # Общие поля
        fields = [
            ('price', '💰 Цена:'),
            ('description', '📖 Описание:')
        ]

        # Специфичные поля для авиабилетов
        if content_type == "flights":
            fields.extend([
                ('airline', '✈️ Авиакомпания:'),
                ('departure', '🛫 Откуда:'),
                ('destination', '🛬 Куда:'),
                ('date', '📅 Дата:'),
                ('duration', '⏱ Длительность:')
            ])
        # Специфичные поля для отелей
        elif content_type == "hotels":
            fields.extend([
                ('location', '📍 Местоположение:'),
                ('check_in', '🔑 Заезд:'),
                ('check_out', '🚪 Выезд:'),
                ('rating', '⭐ Рейтинг:'),
                ('amenities', '🛁 Удобства:')
            ])

        # Формируем строки
        for field, emoji in fields:
            value = metadata.get(field)
            if value and value != "Не указано":
                summary.append(f"{emoji} <i>{value}</i>")

        # Добавляем ссылку в конец, если она есть
        if metadata.get('link') and metadata['link'] != "Нет ссылки":
            summary.append(f"\n🔗 <b>Ссылка:</b> <i>{metadata['link']}</i>")

        return "\n".join(summary)
    
    async def handle_content_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает введенное значение поля"""
        if 'adding_content' not in context.user_data:
            return

        current_field = context.user_data['adding_content']['current_field']
        value = update.message.text.strip()

        # Обработка пропуска поля
        if value == "-":
            value = "Нет ссылки" if current_field == "link" else "Не указано"

        # Сохраняем значение
        context.user_data['adding_content']['metadata'][current_field] = value

        # Подтверждение ввода
        field_names = {
            'title': "Название",
            'price': "Цена",
            'description': "Описание",
            'link': "Ссылка",
            'airline': "Авиакомпания",
            'departure': "Откуда",
            'destination': "Куда",
            'date': "Дата вылета",
            'duration': "Длительность полета",
            'location': "Местоположение",
            'check_in': "Дата заезда",
            'check_out': "Дата выезда",
            'rating': "Рейтинг",
            'amenities': "Удобства"
        }

        await update.message.reply_text(
            f"✅ <b>{field_names[current_field]}:</b> <i>{value}</i>",
            parse_mode='HTML',
            disable_web_page_preview=True
        )

        # Увеличиваем шаг
        context.user_data['adding_content']['step'] += 1

        # Запрашиваем следующее поле
        await self.ask_for_next_field(update, context)

    async def handle_content_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает фото, отправленное после заполнения метаданных."""
        if ('adding_content' not in context.user_data or 
            context.user_data['adding_content'].get('step') != 'awaiting_photo'):
            return  # Не в режиме ожидания фото

        content_type = context.user_data['adding_content']['type']
        metadata = context.user_data['adding_content']['metadata']

        # Если пользователь отправил "-", пропускаем добавление фото
        if update.message.text and update.message.text.strip() == "-":
            file_id = None
        else:
            if not update.message.photo:
                await update.message.reply_text("Пожалуйста, отправьте фото или '-' чтобы пропустить.")
                return
            
            file = update.message.photo[-1]  # Берем фото с самым высоким разрешением
            file_id = file.file_id

        # Сохраняем в базу данных
        self.content_db[content_type][metadata["title"]] = {
            "file_id": file_id,
            "is_photo": file_id is not None,
            "message_id": update.message.message_id,
            "metadata": metadata
        }
        self.save_content_db()

        # Отправляем подтверждение
        await update.message.reply_text(
            f"✅ {'Авиабилет' if content_type == 'flights' else 'Отель'} успешно добавлен в базу!",
            reply_markup=self.create_group_keyboard(),
            disable_web_page_preview=True
        )

        # Очищаем состояние
        del context.user_data['adding_content']

    async def handle_group_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает текстовые сообщения в группе"""
        text = update.message.text
    
        if text == "✈️ Добавить авиабилет":
            await self.start_content_adding(update, context, "flights")
        elif text == "🏨 Добавить отель":
            await self.start_content_adding(update, context, "hotels")
        elif text == "❌ Отменить добавление":
            await update.message.reply_text(
                "Добавление отменено",
                reply_markup=ReplyKeyboardRemove()
            )
            if 'adding_content' in context.user_data:
                del context.user_data['adding_content']
        elif 'adding_content' in context.user_data:
            # Если идет процесс добавления
            if context.user_data['adding_content']['step'] == 'awaiting_photo':
                await self.handle_content_photo(update, context)
            else:
                await self.handle_content_field(update, context)

class ContentManager:
    def __init__(self, group_chat_id: int):
        self.GROUP_CHAT_ID = group_chat_id
        self.CONTENT_DB_FILE = "content_add_db.json"
        self.DATA_FILE = "data.json"
        self.travel_data = self.load_content_db()
        
        # Клавиатура для групповых команд
        self.group_keyboard = ReplyKeyboardMarkup(
            [
                ["✈️ Добавить авиабилет", "🏨 Добавить отель"],
                ["❌ Отменить добавление"]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )

    def create_group_keyboard(self):
        """Создает клавиатуру с командами для группы"""
        return self.group_keyboard

    def load_content_db(self):
        """Загружает базу данных контента из файла"""
        try:
            if Path(self.CONTENT_DB_FILE).exists():
                with open(self.CONTENT_DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке базы данных: {e}")
        
        return {"flights": {}, "hotels": {}}

    def save_content_db(self):
        """Сохраняет базу данных контента в файл"""
        try:
            with open(self.CONTENT_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.content_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении базы данных: {e}")

    async def start_content_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str):
        """Начинает процесс пошагового добавления контента"""
        context.user_data['adding_content'] = {
            'type': content_type,
            'step': 0,
            'metadata': {
                "title": "Не указано",
                "description": "Не указано",
                "link": "Нет ссылки",
                "price": "Не указана"
            }
        }

        # Добавляем специфичные поля
        if content_type == "flights":
            context.user_data['adding_content']['metadata'].update({
                'airline': "Не указана",
                'departure': "Не указано",
                'destination': "Не указано",
                'date': "Не указана",
                'duration': "Не указана"
            })
        elif content_type == "hotels":
            context.user_data['adding_content']['metadata'].update({
                'location': "Не указано",
                'check_in': "Не указана",
                'check_out': "Не указана",
                'rating': "Не указан",
                'amenities': "Не указаны"
            })

        # Приветственное сообщение
        await update.message.reply_text(
            f"""{'✈️' if content_type == 'flights' else '🏨'} <b>Добавление нового {'авиабилета' if content_type == 'flights' else 'отеля'}</b>

            Давайте заполним информацию шаг за шагом. 
            Можете пропустить любой пункт, отправив "-".""",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
    
        await self.ask_for_next_field(update, context)

    async def ask_for_next_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрашивает следующее поле"""
        content_type = context.user_data['adding_content']['type']
        step = context.user_data['adding_content']['step']
        metadata = context.user_data['adding_content']['metadata']

        # Поля с эмодзи и описаниями
        fields_order = [
            ('title', "📝 <b>Название:</b>\n(Например: <i>Авиабилет в Париж</i> или <i>Отель Marriott</i>)"),
            ('price', "💰 <b>Цена:</b>\n(Например: <i>150$</i> или <i>12000₽</i>)"),
            ('description', "📖 <b>Описание:</b>\n(Краткое описание предложения)")
        ]

        # Специфичные поля для каждого типа
        if content_type == "flights":
            fields_order.extend([
                ('airline', "✈️ <b>Авиакомпания:</b>\n(Например: <i>Aeroflot</i>)"),
                ('departure', "🛫 <b>Откуда:</b>\n(Город вылета, например: <i>Москва</i>)"),
                ('destination', "🛬 <b>Куда:</b>\n(Город прилета, например: <i>Париж</i>)"),
                ('date', "📅 <b>Дата вылета:</b>\n(Например: <i>15.07.2023</i>)"),
                ('duration', "⏱ <b>Длительность полета:</b>\n(Например: <i>3ч 30м</i>)")
            ])
        elif content_type == "hotels":
            fields_order.extend([
                ('location', "📍 <b>Местоположение:</b>\n(Например: <i>Париж, Франция</i>)"),
                ('check_in', "🔑 <b>Дата заезда:</b>\n(Например: <i>15.07.2023</i>)"),
                ('check_out', "🚪 <b>Дата выезда:</b>\n(Например: <i>20.07.2023</i>)"),
                ('rating', "⭐ <b>Рейтинг:</b>\n(Например: <i>4.5/5</i>)"),
                ('amenities', "🛁 <b>Удобства:</b>\n(Например: <i>Wi-Fi, бассейн, завтрак</i>)")
            ])

        if step < len(fields_order):
            field, prompt = fields_order[step]
            context.user_data['adding_content']['current_field'] = field

            await update.message.reply_text(
                prompt,
                parse_mode='HTML'
            )
        else:
            # Все основные поля заполнены, запрашиваем ссылку
            if 'link' not in context.user_data['adding_content']['metadata'] or context.user_data['adding_content']['metadata']['link'] == "Нет ссылки":
                context.user_data['adding_content']['current_field'] = 'link'
                await update.message.reply_text(
                    "🔗 <b>Ссылка на бронирование:</b>\n(URL или \"-\" чтобы пропустить)",
                    parse_mode='HTML'
                )
            else:
                # Ссылка получена, запрашиваем фото
                summary = self._generate_content_summary(metadata, content_type)
                await update.message.reply_text(
                    f"""✅ <b>Информация сохранена!</b>

{summary}

Теперь отправьте фото для этого предложения (или отправьте '-' чтобы пропустить):""",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                context.user_data['adding_content']['step'] = 'awaiting_photo'

    def _generate_content_summary(self, metadata: dict, content_type: str) -> str:
        """Генерирует резюме введенных данных"""
        content_type_name = {
            "flights": "Авиабилет",
            "hotels": "Отель" 
        }[content_type]

        summary = [f"\n📋 <b>{content_type_name}:</b> <i>{metadata['title']}</i>"]

        # Общие поля
        fields = [
            ('price', '💰 Цена:'),
            ('description', '📖 Описание:')
        ]

        # Специфичные поля для авиабилетов
        if content_type == "flights":
            fields.extend([
                ('airline', '✈️ Авиакомпания:'),
                ('departure', '🛫 Откуда:'),
                ('destination', '🛬 Куда:'),
                ('date', '📅 Дата:'),
                ('duration', '⏱ Длительность:')
            ])
        # Специфичные поля для отелей
        elif content_type == "hotels":
            fields.extend([
                ('location', '📍 Местоположение:'),
                ('check_in', '🔑 Заезд:'),
                ('check_out', '🚪 Выезд:'),
                ('rating', '⭐ Рейтинг:'),
                ('amenities', '🛁 Удобства:')
            ])

        # Формируем строки
        for field, emoji in fields:
            value = metadata.get(field)
            if value and value != "Не указано":
                summary.append(f"{emoji} <i>{value}</i>")

        # Добавляем ссылку в конец, если она есть
        if metadata.get('link') and metadata['link'] != "Нет ссылки":
            summary.append(f"\n🔗 <b>Ссылка:</b> <i>{metadata['link']}</i>")

        return "\n".join(summary)
    
    async def handle_content_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает введенное значение поля"""
        if 'adding_content' not in context.user_data:
            return

        current_field = context.user_data['adding_content']['current_field']
        value = update.message.text.strip()

        # Обработка пропуска поля
        if value == "-":
            value = "Нет ссылки" if current_field == "link" else "Не указано"

        # Сохраняем значение
        context.user_data['adding_content']['metadata'][current_field] = value

        # Подтверждение ввода
        field_names = {
            'title': "Название",
            'price': "Цена",
            'description': "Описание",
            'link': "Ссылка",
            'airline': "Авиакомпания",
            'departure': "Откуда",
            'destination': "Куда",
            'date': "Дата вылета",
            'duration': "Длительность полета",
            'location': "Местоположение",
            'check_in': "Дата заезда",
            'check_out': "Дата выезда",
            'rating': "Рейтинг",
            'amenities': "Удобства"
        }

        await update.message.reply_text(
            f"✅ <b>{field_names[current_field]}:</b> <i>{value}</i>",
            parse_mode='HTML',
            disable_web_page_preview=True
        )

        # Увеличиваем шаг
        context.user_data['adding_content']['step'] += 1

        # Запрашиваем следующее поле
        await self.ask_for_next_field(update, context)

    async def handle_content_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает фото, отправленное после заполнения метаданных."""
        if ('adding_content' not in context.user_data or 
            context.user_data['adding_content'].get('step') != 'awaiting_photo'):
            return  # Не в режиме ожидания фото

        content_type = context.user_data['adding_content']['type']
        metadata = context.user_data['adding_content']['metadata']

        # Если пользователь отправил "-", пропускаем добавление фото
        if update.message.text and update.message.text.strip() == "-":
            file_id = None
        else:
            if not update.message.photo:
                await update.message.reply_text("Пожалуйста, отправьте фото или '-' чтобы пропустить.")
                return
            
            file = update.message.photo[-1]  # Берем фото с самым высоким разрешением
            file_id = file.file_id

        # Сохраняем в базу данных
        self.content_db[content_type][metadata["title"]] = {
            "file_id": file_id,
            "is_photo": file_id is not None,
            "message_id": update.message.message_id,
            "metadata": metadata
        }
        self.save_content_db()

        # Отправляем подтверждение
        await update.message.reply_text(
            f"✅ {'Авиабилет' if content_type == 'flights' else 'Отель'} успешно добавлен в базу!",
            reply_markup=self.create_group_keyboard(),
            disable_web_page_preview=True
        )

        # Очищаем состояние
        del context.user_data['adding_content']

    async def handle_group_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает текстовые сообщения в группе при добавлении контента"""
        if 'adding_content' in context.user_data:
            # Если идет процесс добавления контента
            if context.user_data['adding_content']['step'] == 'awaiting_photo':
                # Обрабатываем как фото (или пропуск)
                await self.handle_content_photo(update, context)
            else:
                # Обрабатываем поле контента
                await self.handle_content_field(update, context)
        else:
            # Обрабатываем команды из клавиатуры
            await self.handle_group_command(update, context)

# Инициализация менеджера контента
content_manager = ContentManager(ADMIN_GROUP_ID)

# ========== КЛАВИАТУРЫ ==========
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✈️ Авиабилеты", callback_data='flights'),
            InlineKeyboardButton("🏨 Гостиницы", callback_data='hotels')
        ],
        [InlineKeyboardButton("ℹ️ О боте", callback_data='about')]
    ])

def flights_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Найти билеты", callback_data='search_flights')],
        [InlineKeyboardButton("📋 Посмотреть варианты", callback_data='list_flights')],
        [InlineKeyboardButton("💡 Советы по поиску", callback_data='flights_tips')],
        [InlineKeyboardButton("↩️ На главную", callback_data='back_to_main')]
    ])

def hotels_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Найти отели", callback_data='search_hotels')],
        [InlineKeyboardButton("📋 Посмотреть варианты", callback_data='list_hotels')],
        [InlineKeyboardButton("💡 Советы по поиску", callback_data='hotels_tips')],
        [InlineKeyboardButton("↩️ На главную", callback_data='back_to_main')]
    ])

def flights_tips_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад к авиабилетам", callback_data='back_to_flights')]
    ])

def hotels_tips_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад к отелям", callback_data='back_to_hotels')]
    ])

def search_results_keyboard(item_type):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Фильтры", callback_data=f'filter_{item_type}')],
        [InlineKeyboardButton("↩️ Назад", callback_data=f'back_to_{item_type}')]
    ])

def filter_options_keyboard(item_type):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 По цене (дешевые)", callback_data=f'filter_{item_type}_price_asc')],
        [InlineKeyboardButton("💰 По цене (дорогие)", callback_data=f'filter_{item_type}_price_desc')],
        [InlineKeyboardButton("🆕 Новые", callback_data=f'filter_{item_type}_newest')],
        [InlineKeyboardButton("↩️ Назад к результатам", callback_data=f'back_to_results_{item_type}')]
    ])

def back_keyboard(target_menu):
    """Клавиатура с кнопкой Назад"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад", callback_data=f'back_to_{target_menu}')]
    ])

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await show_main_menu(update)
    return MAIN_MENU

async def show_main_menu(update: Update):
    """Показывает главное меню"""
    text = (
        "🌟 Добро пожаловать в TravelBot! 🌟\n\n"
        "Я помогу вам найти:\n"
        "• Авиабилеты по лучшим ценам\n"
        "• Отели с хорошими отзывами\n\n"
        "Выберите интересующий вас раздел:"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())

# ========== ПОИСК И ФИЛЬТРАЦИЯ ==========
async def show_last_items(update: Update, item_type: str):
    """Показывает последние добавленные элементы"""
    items = content_manager.travel_data[item_type][-LAST_SHOW_ITEMS:] if content_manager.travel_data[item_type] else []
    
    if not items:
        text = f"✈️ <b>Доступные авиабилеты</b> ✈️\n\nНет доступных вариантов." if item_type == 'flights' else \
               f"🏨 <b>Доступные отели</b> 🏨\n\nНет доступных вариантов."
    else:
        text = f"✈️ <b>Последние авиабилеты</b> ✈️\n\n" if item_type == 'flights' else \
               f"🏨 <b>Последние отели</b> 🏨\n\n"
        for item in items:
            meta = item.get('metadata', {})
            text += (
                f"<b>{meta.get('name', 'Без названия')}</b>\n"
                f"💵 Цена: {meta.get('price', 'Не указана')}\n"
                f"📝 Описание: {meta.get('description', 'Нет описания')}\n"
                f"🔗 Подробнее: {meta.get('link', 'Нет ссылки')}\n\n"
            )
        text += "Используйте фильтры для уточнения поиска."
    
    keyboard = search_results_keyboard(item_type)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

async def show_all_items(update: Update, item_type: str):
    """Показывает все элементы (для list_flights и list_hotels)"""
    items = content_manager.travel_data[item_type] if content_manager.travel_data[item_type] else []
    
    if not items:
        text = f"✈️ <b>Доступные авиабилеты</b> ✈️\n\nНет доступных вариантов." if item_type == 'flights' else \
               f"🏨 <b>Доступные отели</b> 🏨\n\nНет доступных вариантов."
    else:
        text = f"✈️ <b>Все авиабилеты</b> ✈️\n\n" if item_type == 'flights' else \
               f"🏨 <b>Все отели</b> 🏨\n\n"
        for item in items:
            meta = item.get('metadata', {})
            text += (
                f"<b>{meta.get('name', 'Без названия')}</b>\n"
                f"💵 Цена: {meta.get('price', 'Не указана')}\n"
                f"📝 Описание: {meta.get('description', 'Нет описания')}\n"
                f"🔗 Подробнее: {meta.get('link', 'Нет ссылки')}\n\n"
            )
    
    keyboard = back_keyboard('flights' if item_type == 'flights' else 'hotels')
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

def apply_filters(items, filter_type):
    """Применяет фильтры к списку элементов"""
    if filter_type == 'price_asc':
        return sorted(items, key=lambda x: float(x.get('metadata', {}).get('price', '0').split()[0].replace('$', '').replace('€', '').replace('₽', '')))
    elif filter_type == 'price_desc':
        return sorted(items, key=lambda x: float(x.get('metadata', {}).get('price', '0').split()[0].replace('$', '').replace('€', '').replace('₽', ''), reverse=True))
    elif filter_type == 'newest':
        return items[-LAST_SHOW_ITEMS:]
    return items

async def show_filtered_items(update: Update, item_type: str, filter_type: str):
    """Показывает отфильтрованные элементы"""
    query = update.callback_query
    await query.answer()
    
    items = apply_filters(content_manager.travel_data[item_type], filter_type)
    items = items[-LAST_SHOW_ITEMS:] if items else []
    
    if not items:
        text = f"Нет доступных {'авиабилетов' if item_type == 'flights' else 'отелей'} с выбранными фильтрами."
    else:
        text = f"✈️ Авиабилеты (фильтр: {'дешевые' if filter_type == 'price_asc' else 'дорогие' if filter_type == 'price_desc' else 'новые'}):\n\n" if item_type == 'flights' else \
              f"🏨 Отели (фильтр: {'дешевые' if filter_type == 'price_asc' else 'дорогие' if filter_type == 'price_desc' else 'новые'}):\n\n"
        for item in items:
            meta = item.get('metadata', {})
            text += (
                f"<b>{meta.get('name', 'Без названия')}</b>\n"
                f"💵 Цена: {meta.get('price', 'Не указана')}\n"
                f"📝 Описание: {meta.get('description', 'Нет описания')}\n"
                f"🔗 Подробнее: {meta.get('link', 'Нет ссылки')}\n\n"
            )
    
    keyboard = search_results_keyboard(item_type)
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode='HTML')

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка главного меню"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'flights':
        await show_flights_menu(update)
        return FLIGHTS_MENU
    elif query.data == 'hotels':
        await show_hotels_menu(update)
        return HOTELS_MENU
    elif query.data == 'about':
        about_text = (
            "ℹ️ <b>О StayFlyBot</b> ℹ️\n\n"
            "Я создан, чтобы помочь вам быстро находить лучшие варианты "
            "авиабилетов и отелей для ваших путешествий.\n\n"
            "<b>Что я умею:</b>\n"
            "• Искать авиабилеты по вашим параметрам\n"
            "• Находить подходящие отели\n"
            "• Показывать актуальные цены\n\n"
            "Версия бота: 2.1\n"
            "Последнее обновление: 01.01.2023"
        )
        await query.message.reply_text(about_text, parse_mode='HTML')
    elif query.data == 'back_to_main':
        await show_main_menu(update)
        return MAIN_MENU
    return MAIN_MENU

async def show_flights_menu(update: Update):
    """Показывает меню авиабилетов"""
    menu_text = (
        "✈️ <b>Меню авиабилетов</b> ✈️\n\n"
        "Здесь вы можете:\n"
        "• Найти билеты по вашим параметрам\n"
        "• Посмотреть список доступных вариантов\n"
        "• Получить полезные советы по поиску\n\n"
        "Я проверяю информацию от множества авиакомпаний!"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(menu_text, reply_markup=flights_menu_keyboard(), parse_mode='HTML')
    else:
        await update.message.reply_text(menu_text, reply_markup=flights_menu_keyboard(), parse_mode='HTML')

async def show_hotels_menu(update: Update):
    """Показывает меню отелей"""
    menu_text = (
        "🏨 <b>Меню гостиниц</b> 🏨\n\n"
        "В этом разделе вы можете:\n"
        "• Найти отели по вашим критериям\n"
        "• Посмотреть список вариантов\n"
        "• Узнать секреты эффективного поиска\n\n"
        "Я анализирую информацию от множества отелей!"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(menu_text, reply_markup=hotels_menu_keyboard(), parse_mode='HTML')
    else:
        await update.message.reply_text(menu_text, reply_markup=hotels_menu_keyboard(), parse_mode='HTML')

async def handle_flights_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка советов по авиабилетам"""
    query = update.callback_query
    await query.answer()
    
    tips_text = (
        "💡 <b>Советы по поиску авиабилетов</b> 💡\n\n"
        "1. Ищите билеты в режиме инкогнито\n"
        "2. Покупайте билеты во вторник и среду\n"
        "3. Лучшее время для покупки - 6-8 недель до вылета\n"
        "4. Используйте метапоисковые системы\n"
        "5. Рассмотрите альтернативные аэропорты"
    )
    
    await query.message.reply_text(tips_text, reply_markup=flights_tips_keyboard(), parse_mode='HTML')
    return FLIGHTS_MENU

async def handle_hotels_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка советов по отелям"""
    query = update.callback_query
    await query.answer()
    
    tips_text = (
        "💡 <b>Советы по поиску отелей</b> 💡\n\n"
        "1. Читайте отзывы на нескольких сайтах\n"
        "2. Бронируйте напрямую через сайт отеля\n"
        "3. Проверяйте наличие скрытых сборов\n"
        "4. Рассмотрите альтернативы (апартаменты, гостевые дома)\n"
        "5. Используйте кэшбэк-сервисы"
    )
    
    await query.message.reply_text(tips_text, reply_markup=hotels_tips_keyboard(), parse_mode='HTML')
    return HOTELS_MENU

async def handle_search_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка поиска авиабилетов"""
    await show_last_items(update, 'flights')
    return PROCESS_FLIGHTS

async def handle_search_hotels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка поиска отелей"""
    await show_last_items(update, 'hotels')
    return PROCESS_HOTELS

async def handle_list_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка просмотра всех авиабилетов"""
    await show_all_items(update, 'flights')
    return FLIGHTS_MENU

async def handle_list_hotels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка просмотра всех отелей"""
    await show_all_items(update, 'hotels')
    return HOTELS_MENU

async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки фильтров"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('filter_flights'):
        await query.message.reply_text(
            "Выберите тип фильтра для авиабилетов:",
            reply_markup=filter_options_keyboard('flights')
        )
        return FILTER_FLIGHTS
    elif query.data.startswith('filter_hotels'):
        await query.message.reply_text(
            "Выберите тип фильтра для отелей:",
            reply_markup=filter_options_keyboard('hotels')
        )
        return FILTER_HOTELS

async def handle_filter_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка применения фильтра"""
    query = update.callback_query
    await query.answer()
    
    if '_flights_' in query.data:
        filter_type = query.data.split('_')[-1]
        await show_filtered_items(update, 'flights', filter_type)
        return PROCESS_FLIGHTS
    elif '_hotels_' in query.data:
        filter_type = query.data.split('_')[-1]
        await show_filtered_items(update, 'hotels', filter_type)
        return PROCESS_HOTELS

async def handle_back_to_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в меню авиабилетов"""
    await show_flights_menu(update)
    return FLIGHTS_MENU

async def handle_back_to_hotels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в меню отелей"""
    await show_hotels_menu(update)
    return HOTELS_MENU

async def handle_back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам поиска"""
    query = update.callback_query
    await query.answer()
    
    if 'flights' in query.data:
        await show_last_items(update, 'flights')
        return PROCESS_FLIGHTS
    elif 'hotels' in query.data:
        await show_last_items(update, 'hotels')
        return PROCESS_HOTELS

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(f"Произошла ошибка: {context.error}")

# ========== ЗАПУСК БОТА ==========
def main():
    application = Application.builder().token(TOKEN).build()
    
    content_adder = ContentAdder(ADMIN_GROUP_ID)

    # Обработчики для группы
    group_handlers = [
        CommandHandler("add", content_adder.start_group_adding),
        MessageHandler(filters.TEXT & filters.Chat(ADMIN_GROUP_ID), 
                     content_adder.handle_group_text_message),
        MessageHandler(filters.PHOTO & filters.Chat(ADMIN_GROUP_ID),
                     content_adder.handle_content_photo)
    ]
    
    # Добавляем все обработчики
    for handler in group_handlers:
        application.add_handler(handler)
    
    # Основной обработчик (работает везде)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(handle_main_menu)],
            FLIGHTS_MENU: [
                CallbackQueryHandler(handle_search_flights, pattern='^search_flights$'),
                CallbackQueryHandler(handle_list_flights, pattern='^list_flights$'),
                CallbackQueryHandler(handle_flights_tips, pattern='^flights_tips$'),
                CallbackQueryHandler(handle_main_menu, pattern='^back_to_main$')
            ],
            HOTELS_MENU: [
                CallbackQueryHandler(handle_search_hotels, pattern='^search_hotels$'),
                CallbackQueryHandler(handle_list_hotels, pattern='^list_hotels$'),
                CallbackQueryHandler(handle_hotels_tips, pattern='^hotels_tips$'),
                CallbackQueryHandler(handle_main_menu, pattern='^back_to_main$')
            ],
            PROCESS_FLIGHTS: [
                CallbackQueryHandler(handle_filters, pattern='^filter_flights$'),
                CallbackQueryHandler(handle_back_to_flights, pattern='^back_to_flights$'),
                CallbackQueryHandler(handle_filter_apply, pattern='^filter_flights_')
            ],
            PROCESS_HOTELS: [
                CallbackQueryHandler(handle_filters, pattern='^filter_hotels$'),
                CallbackQueryHandler(handle_back_to_hotels, pattern='^back_to_hotels$'),
                CallbackQueryHandler(handle_filter_apply, pattern='^filter_hotels_')
            ],
            FILTER_FLIGHTS: [
                CallbackQueryHandler(handle_filter_apply, pattern='^filter_flights_'),
                CallbackQueryHandler(handle_back_to_results, pattern='^back_to_results_flights$')
            ],
            FILTER_HOTELS: [
                CallbackQueryHandler(handle_filter_apply, pattern='^filter_hotels_'),
                CallbackQueryHandler(handle_back_to_results, pattern='^back_to_results_hotels$')
            ]
        },
        fallbacks=[]
    )
    
    # Обновляем обработчики:
    application.add_handler(CommandHandler(
        "start_add",
        content_adder.start_content_adding,  # Используем content_adder
        filters=filters.Chat(ADMIN_GROUP_ID)
    ))

    application.add_handler(MessageHandler(
        filters.Chat(ADMIN_GROUP_ID) & filters.TEXT,
        content_adder.handle_group_text_message  # Используем content_adder
    ))

    application.add_handler(MessageHandler(
        filters.Chat(ADMIN_GROUP_ID) & filters.PHOTO,
        content_adder.handle_content_photo  # Новый обработчик фото
    ))

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
