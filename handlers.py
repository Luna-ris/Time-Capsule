import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from config import logger, ENCRYPTION_KEY_BYTES
from crypto import decrypt_data_aes
from localization import t, LOCALE
from database import (
    fetch_data, post_data, add_user, create_capsule, add_recipient,
    get_user_capsules, get_capsule_recipients, delete_capsule, edit_capsule,
    generate_unique_capsule_number, update_data, get_chat_id
)
from utils import check_capsule_ownership, save_capsule_content, convert_to_utc, save_send_date
import pytz

# Состояния для пошагового мастера создания капсулы
CREATING_CAPSULE_TITLE = "creating_capsule_title"
CREATING_CAPSULE_CONTENT = "creating_capsule_content"
CREATING_CAPSULE_RECIPIENTS = "creating_capsule_recipients"
CREATING_CAPSULE_DATE = "creating_capsule_date"
SELECTING_CAPSULE = "selecting_capsule"
SELECTING_CAPSULE_FOR_RECIPIENTS = "selecting_capsule_for_recipients"

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start."""
    user = update.message.from_user
    add_user(user.username or str(user.id), user.id, update.message.chat_id)
    keyboard = [
        [t("create_capsule_btn"), t("view_capsules_btn")],
        [t("add_recipient_btn"), t("send_capsule_btn")],
        [t("delete_capsule_btn"), t("edit_capsule_btn")],
        [t("view_recipients_btn"), t("help_btn")],
        [t("select_send_date_btn"), t("support_author_btn")],
        [t("change_language_btn")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(t('start_message'), reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help."""
    keyboard = [
        [t("create_capsule_btn"), t("view_capsules_btn")],
        [t("add_recipient_btn"), t("send_capsule_btn")],
        [t("delete_capsule_btn"), t("edit_capsule_btn")],
        [t("view_recipients_btn"), t("help_btn")],
        [t("select_send_date_btn"), t("support_author_btn")],
        [t("change_language_btn")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(t('help_message'), reply_markup=reply_markup)

async def create_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /create_capsule — начало пошагового мастера."""
    context.user_data['state'] = CREATING_CAPSULE_TITLE
    context.user_data['capsule_content'] = {"text": [], "photos": [], "videos": [], "audios": [],
                                            "documents": [], "stickers": [], "voices": []}
    await update.message.reply_text("📦 Введите название капсулы:")

async def show_capsule_selection(update: Update, context: CallbackContext, action: str):
    """Отображение инлайн-меню для выбора капсулы."""
    capsules = get_user_capsules(update.effective_user.id)
    if not capsules:
        await update.message.reply_text(t('no_capsules'))
        return False

    # Создаем кнопки в 2 столбца
    keyboard = []
    row = []
    for capsule in capsules:
        button_text = f"📦 #{capsule['id']}: {capsule['title']}"[:30]  # Ограничиваем длину текста
        button = InlineKeyboardButton(button_text, callback_data=f"{action}_{capsule['id']}")
        row.append(button)
        if len(row) == 2:  # Если в ряду 2 кнопки, добавляем ряд в клавиатуру
            keyboard.append(row)
            row = []
    if row:  # Добавляем последний ряд, если он не пустой
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t('select_capsule'), reply_markup=reply_markup)
    context.user_data['action'] = action
    return True

async def add_recipient_command(update: Update, context: CallbackContext):
    """Обработчик команды /add_recipient."""
    if await show_capsule_selection(update, context, "add_recipient"):
        context.user_data['state'] = SELECTING_CAPSULE_FOR_RECIPIENTS

async def view_capsules_command(update: Update, context: CallbackContext):
    """Обработчик команды /view_capsules с улучшенным отображением."""
    try:
        capsules = get_user_capsules(update.message.from_user.id)
        if capsules:
            response = []
            for c in capsules:
                status = t('scheduled') if c['scheduled_at'] else t('draft')
                created_at = datetime.fromisoformat(c['created_at']).strftime('%d.%m.%Y %H:%M')
                response.append(
                    f"📦 #{c['id']} {c['title']}\n"
                    f"🕒 {t('created_at')}: {created_at}\n"
                    f"🔒 {t('status')}: {status}"
                )
            
            # Создаем кнопки для выбора капсул
            keyboard = []
            row = []
            for capsule in capsules:
                button_text = f"📦 #{capsule['id']}: {capsule['title']}"[:30]  # Ограничиваем длину текста
                button = InlineKeyboardButton(button_text, callback_data=f"view_{capsule['id']}")
                row.append(button)
                if len(row) == 2:  # Если в ряду 2 кнопки, добавляем ряд в клавиатуру
                    keyboard.append(row)
                    row = []
            if row:  # Добавляем последний ряд, если он не пустой
                keyboard.append(row)

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                t('your_capsules') + "\n\n" + "\n\n".join(response),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(t('no_capsules'))
    except Exception as e:
        logger.error(f"Ошибка при получении капсул: {e}")
        await update.message.reply_text(t('error_general'))

async def send_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /send_capsule."""
    if await show_capsule_selection(update, context, "send_capsule"):
        context.user_data['state'] = "sending_capsule"

async def delete_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /delete_capsule."""
    if await show_capsule_selection(update, context, "delete_capsule"):
        context.user_data['state'] = "deleting_capsule"

async def edit_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /edit_capsule."""
    if await show_capsule_selection(update, context, "edit_capsule"):
        context.user_data['state'] = "editing_capsule"

async def view_recipients_command(update: Update, context: CallbackContext):
    """Обработчик команды /view_recipients."""
    if await show_capsule_selection(update, context, "view_recipients"):
        context.user_data['state'] = "viewing_recipients"

async def select_send_date(update: Update, context: CallbackContext):
    """Обработчик команды /select_send_date."""
    if await show_capsule_selection(update, context, "select_send_date"):
        context.user_data['state'] = SELECTING_CAPSULE

async def support_author(update: Update, context: CallbackContext):
    """Обработчик команды /support_author."""
    DONATION_URL = "https://www.donationalerts.com/r/lunarisqqq"
    await update.message.reply_text(t('support_author', url=DONATION_URL))

async def change_language(update: Update, context: CallbackContext):
    """Обработчик команды /change_language."""
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="ru"),
         InlineKeyboardButton("English", callback_data="en")],
        [InlineKeyboardButton("Español", callback_data="es"),
         InlineKeyboardButton("Français", callback_data="fr")],
        [InlineKeyboardButton("Deutsch", callback_data="de")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t('select_language'), reply_markup=reply_markup)

async def handle_language_selection(update: Update, context: CallbackContext):
    """Обработчик выбора языка."""
    global LOCALE
    query = update.callback_query
    lang = query.data
    LOCALE = lang
    lang_names = {
        'ru': "Русский",
        'en': "English",
        'es': "Español",
        'fr': "Français",
        'de': "Deutsch"
    }
    new_lang = lang_names.get(lang, "Unknown")
    await query.edit_message_text(f"Язык изменен на {new_lang}.")
    keyboard = [
        [t("create_capsule_btn"), t("view_capsules_btn")],
        [t("add_recipient_btn"), t("send_capsule_btn")],
        [t("delete_capsule_btn"), t("edit_capsule_btn")],
        [t("view_recipients_btn"), t("help_btn")],
        [t("select_send_date_btn"), t("support_author_btn")],
        [t("change_language_btn")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t('start_message'),
        reply_markup=reply_markup
    )

async def handle_inline_selection(update: Update, context: CallbackContext):
    """Обработчик выбора капсулы через инлайн-меню."""
    query = update.callback_query
    try:
        # Разделяем callback_data на части
        parts = query.data.rsplit('_', 1)  # Разделяем по последнему '_'
        if len(parts) != 2:
            raise ValueError("Неверный формат callback_data")
        action, capsule_id = parts
        capsule_id = int(capsule_id)  # Пытаемся преобразовать capsule_id в число
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка при разборе callback_data: {query.data}, ошибка: {e}")
        await query.edit_message_text("⚠️ Ошибка: Неверный формат данных. Пожалуйста, попробуйте снова.")
        return

    context.user_data['selected_capsule_id'] = capsule_id

    if not await check_capsule_ownership(update, capsule_id, query):
        return

    if action == "add_recipient":
        await query.edit_message_text(t('enter_recipients'))
        context.user_data['state'] = "adding_recipient"
    elif action == "send_capsule":
        await preview_capsule(update, context, capsule_id)
    elif action == "delete_capsule":
        await query.edit_message_text(
            t('confirm_delete'),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Да", callback_data="confirm_delete"),
                 InlineKeyboardButton("Нет", callback_data="cancel_delete")]
            ])
        )
    elif action == "edit_capsule":
        await query.edit_message_text(t('enter_new_content'))
        context.user_data['state'] = "editing_capsule_content"
    elif action == "view_recipients":
        await handle_view_recipients_logic(update, context, capsule_id)
    elif action == "select_send_date":
        keyboard = [
            [InlineKeyboardButton(t("through_week"), callback_data="week")],
            [InlineKeyboardButton(t("through_month"), callback_data="month")],
            [InlineKeyboardButton(t("select_date"), callback_data="custom")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t('choose_send_date'), reply_markup=reply_markup)
    elif action == "view":
        # Показываем информацию о капсуле
        capsule = fetch_data("capsules", {"id": capsule_id})
        if capsule:
            status = t('scheduled') if capsule[0]['scheduled_at'] else t('draft')
            created_at = datetime.fromisoformat(capsule[0]['created_at']).strftime('%d.%m.%Y %H:%M')
            await query.edit_message_text(
                f"📦 #{capsule[0]['id']} {capsule[0]['title']}\n"
                f"🕒 {t('created_at')}: {created_at}\n"
                f"🔒 {t('status')}: {status}"
            )

async def preview_capsule(update: Update, context: CallbackContext, capsule_id: int):
    """Предпросмотр капсулы перед отправкой."""
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule:
        await update.callback_query.edit_message_text(t('invalid_capsule_id'))
        return

    content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
    preview_text = "📦 Предпросмотр капсулы:\n"
    if content.get('text'):
        preview_text += f"Текст:\n" + "\n".join(content['text']) + "\n"
    if content.get('photos'):
        preview_text += f"Фото: {len(content['photos'])} шт.\n"
    if content.get('videos'):
        preview_text += f"Видео: {len(content['videos'])} шт.\n"
    if content.get('audios'):
        preview_text += f"Аудио: {len(content['audios'])} шт.\n"
    if content.get('documents'):
        preview_text += f"Документы: {len(content['documents'])} шт.\n"
    if content.get('stickers'):
        preview_text += f"Стикеры: {len(content['stickers'])} шт.\n"
    if content.get('voices'):
        preview_text += f"Голосовые: {len(content['voices'])} шт.\n"

    keyboard = [
        [InlineKeyboardButton("Отправить", callback_data="confirm_send"),
         InlineKeyboardButton("Отмена", callback_data="cancel_send")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(preview_text, reply_markup=reply_markup)

async def handle_date_buttons(update: Update, context: CallbackContext):
    """Обработчик кнопок выбора даты отправки."""
    query = update.callback_query
    if query.data == 'week':
        send_date = datetime.now(pytz.utc) + timedelta(weeks=1)
        await save_send_date(update, context, send_date)
    elif query.data == 'month':
        send_date = datetime.now(pytz.utc) + timedelta(days=30)
        await save_send_date(update, context, send_date)
    elif query.data == 'custom':
        await query.edit_message_text(
            "📅 Введите дату и время отправки в формате 'день.месяц.год час:минута:секунда'.\n"
            "Пример: 17.03.2025 21:12:00"
        )
        context.user_data['state'] = "entering_custom_date"

async def handle_delete_confirmation(update: Update, context: CallbackContext):
    """Обработчик подтверждения удаления капсулы."""
    query = update.callback_query
    if query.data == "confirm_delete":
        capsule_id = context.user_data.get('selected_capsule_id')
        delete_capsule(capsule_id)
        await query.edit_message_text(t('capsule_deleted', capsule_id=capsule_id))
    else:
        await query.edit_message_text(t('delete_canceled'))
    context.user_data['state'] = "idle"

async def handle_send_confirmation(update: Update, context: CallbackContext):
    """Обработчик подтверждения отправки капсулы."""
    query = update.callback_query
    if query.data == "confirm_send":
        capsule_id = context.user_data.get('selected_capsule_id')
        await handle_send_capsule_logic(update, context, capsule_id)
    else:
        await query.edit_message_text("❌ Отправка отменена.")
    context.user_data['state'] = "idle"

async def handle_text(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений с пошаговым мастером."""
    text = update.message.text.strip()
    state = context.user_data.get('state', 'idle')
    actions = {
        t("create_capsule_btn"): create_capsule_command,
        t("view_capsules_btn"): view_capsules_command,
        t("add_recipient_btn"): add_recipient_command,
        t("send_capsule_btn"): send_capsule_command,
        t("delete_capsule_btn"): delete_capsule_command,
        t("edit_capsule_btn"): edit_capsule_command,
        t("view_recipients_btn"): view_recipients_command,
        t("help_btn"): help_command,
        t("select_send_date_btn"): select_send_date,
        t("support_author_btn"): support_author,
        t("change_language_btn"): change_language
    }
    if text in actions:
        await actions[text](update, context)
    elif state == CREATING_CAPSULE_TITLE:
        await handle_capsule_title(update, context, text)
    elif state == CREATING_CAPSULE_CONTENT:
        await handle_create_capsule_content(update, context, text)
    elif state == CREATING_CAPSULE_RECIPIENTS:
        await handle_create_capsule_recipients(update, context, text)
    elif state == "adding_recipient":
        await handle_recipient(update, context)
    elif state == "editing_capsule_content":
        await handle_edit_capsule_content(update, context)
    elif state == "entering_custom_date":
        await handle_select_send_date(update, context, text)
    else:
        await update.message.reply_text(t('create_capsule_first'))

async def handle_capsule_title(update: Update, context: CallbackContext, title: str):
    """Обработка названия капсулы."""
    context.user_data['capsule_title'] = title
    context.user_data['state'] = CREATING_CAPSULE_CONTENT
    await update.message.reply_text("📝 Добавьте контент в капсулу (текст, фото, видео и т.д.):")

async def handle_create_capsule_content(update: Update, context: CallbackContext, text: str):
    """Обработка добавления текстового контента в капсулу."""
    capsule_content = context.user_data.get('capsule_content', {"text": []})
    capsule_content['text'].append(text)
    context.user_data['capsule_content'] = capsule_content
    keyboard = [
        [InlineKeyboardButton("Завершить", callback_data="finish_capsule"),
         InlineKeyboardButton("Добавить ещё", callback_data="add_more")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t('text_added'), reply_markup=reply_markup)

async def handle_create_capsule_recipients(update: Update, context: CallbackContext, text: str):
    """Обработка добавления получателей в капсулу."""
    try:
        usernames = set(text.strip().split())
        context.user_data['capsule_recipients'] = usernames
        context.user_data['state'] = CREATING_CAPSULE_DATE
        keyboard = [
            [InlineKeyboardButton(t("through_week"), callback_data="week")],
            [InlineKeyboardButton(t("through_month"), callback_data="month")],
            [InlineKeyboardButton(t("select_date"), callback_data="custom")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(t('choose_send_date'), reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателей: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_content_buttons(update: Update, context: CallbackContext):
    """Обработчик кнопок 'Завершить' и 'Добавить ещё'."""
    query = update.callback_query
    if query.data == "finish_capsule":
        user = update.effective_user
        existing_user = fetch_data("users", {"telegram_id": user.id})
        creator_id = existing_user[0]['id'] if existing_user else post_data("users", {
            "telegram_id": user.id,
            "username": user.username or str(user.id),
            "chat_id": update.effective_chat.id
        })[0]['id']

        content = json.dumps(context.user_data['capsule_content'], ensure_ascii=False)
        user_capsule_number = generate_unique_capsule_number(creator_id)
        capsule_id = create_capsule(creator_id, context.user_data['capsule_title'], content, user_capsule_number)
        context.user_data['current_capsule'] = capsule_id
        context.user_data['state'] = CREATING_CAPSULE_RECIPIENTS
        await query.edit_message_text(t('capsule_created', capsule_id=capsule_id) + "\n👥 Укажите получателей (например, @Friend1 @Friend2):")
    elif query.data == "add_more":
        await query.edit_message_text("📝 Добавьте ещё контент в капсулу:")

async def handle_select_send_date(update: Update, context: CallbackContext, text: str):
    """Обработчик ввода пользовательской даты отправки."""
    try:
        send_date_naive = datetime.strptime(text, "%d.%m.%Y %H:%M:%S")
        send_date_utc = convert_to_utc(text)
        now = datetime.now(pytz.utc)
        if send_date_utc <= now:
            await update.message.reply_text(
                "❌ Ошибка: Укажите дату и время в будущем.\nПример: 17.03.2025 21:12:00"
            )
            return
        await save_send_date(update, context, send_date_utc, is_message=True)
        if context.user_data.get('state') == CREATING_CAPSULE_DATE:
            await finalize_capsule_creation(update, context)
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты. Используйте формат 'день.месяц.год час:минута:секунда'.\nПример: 17.03.2025 21:12:00"
        )
    except Exception as e:
        logger.error(f"Ошибка при установке даты отправки: {e}")
        await update.message.reply_text(t('error_general'))

async def finalize_capsule_creation(update: Update, context: CallbackContext):
    """Завершение создания капсулы."""
    capsule_id = context.user_data['current_capsule']
    for username in context.user_data.get('capsule_recipients', []):
        add_recipient(capsule_id, username.lstrip('@'))
    await update.message.reply_text(t('recipients_added', capsule_id=capsule_id))
    context.user_data['state'] = "idle"
    context.user_data.pop('capsule_title', None)
    context.user_data.pop('capsule_content', None)
    context.user_data.pop('capsule_recipients', None)
    context.user_data.pop('current_capsule', None)

async def handle_recipient(update: Update, context: CallbackContext):
    """Обработчик добавления получателей."""
    try:
        usernames = set(update.message.text.strip().split())
        capsule_id = context.user_data.get('selected_capsule_id')
        for username in usernames:
            add_recipient(capsule_id, username.lstrip('@'))
        await update.message.reply_text(t('recipients_added', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателя: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_send_capsule_logic(update: Update, context: CallbackContext, capsule_id: int):
    """Логика отправки капсулы."""
    try:
        capsule = fetch_data("capsules", {"id": capsule_id})
        if not capsule:
            await update.callback_query.edit_message_text(t('invalid_capsule_id'))
            return
        recipients = get_capsule_recipients(capsule_id)
        if not recipients:
            await update.callback_query.edit_message_text(t('no_recipients'))
            return
        content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
        for recipient in recipients:
            chat_id = get_chat_id(recipient['recipient_username'])
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=t('capsule_received', sender=update.effective_user.username or "Unknown")
                )
                for item in content.get('text', []):
                    await context.bot.send_message(chat_id, item)
                for item in content.get('stickers', []):
                    await context.bot.send_sticker(chat_id, item)
                for item in content.get('photos', []):
                    await context.bot.send_photo(chat_id, item)
                for item in content.get('documents', []):
                    await context.bot.send_document(chat_id, item)
                for item in content.get('voices', []):
                    await context.bot.send_voice(chat_id, item)
                for item in content.get('videos', []):
                    await context.bot.send_video(chat_id, item)
                for item in content.get('audios', []):
                    await context.bot.send_audio(chat_id, item)
                await update.callback_query.edit_message_text(t('capsule_sent', recipient=recipient['recipient_username']))
            else:
                await update.callback_query.edit_message_text(t('recipient_not_registered', recipient=recipient['recipient_username']))
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.callback_query.edit_message_text(t('service_unavailable'))

async def handle_edit_capsule_content(update: Update, context: CallbackContext):
    """Обработчик редактирования содержимого капсулы."""
    try:
        capsule_id = context.user_data.get('selected_capsule_id')
        content = json.dumps({"text": [update.message.text]}, ensure_ascii=False)
        edit_capsule(capsule_id, content=content)
        await update.message.reply_text(t('capsule_edited', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при редактировании содержимого капсулы: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_view_recipients_logic(update: Update, context: CallbackContext, capsule_id: int):
    """Логика просмотра получателей капсулы."""
    try:
        recipients = get_capsule_recipients(capsule_id)
        if recipients:
            recipient_list = "\n".join([f"@{r['recipient_username']}" for r in recipients])
            await update.callback_query.edit_message_text(t('recipients_list', capsule_id=capsule_id, recipients=recipient_list))
        else:
            await update.callback_query.edit_message_text(t('no_recipients_for_capsule', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.callback_query.edit_message_text(t('error_general'))

async def handle_photo(update: Update, context: CallbackContext):
    """Обработчик добавления фото в капсулу."""
    if context.user_data.get('state') not in [CREATING_CAPSULE_CONTENT]:
        await update.message.reply_text(t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"photos": []})
    photo_file_id = (await update.message.photo[-1].get_file()).file_id
    capsule_content.setdefault('photos', []).append(photo_file_id)
    context.user_data['capsule_content'] = capsule_content
    keyboard = [
        [InlineKeyboardButton("Завершить", callback_data="finish_capsule"),
         InlineKeyboardButton("Добавить ещё", callback_data="add_more")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t('photo_added'), reply_markup=reply_markup)

async def handle_media(update: Update, context: CallbackContext, media_type: str, file_attr: str):
    """Обработчик медиафайлов."""
    if context.user_data.get('state') not in [CREATING_CAPSULE_CONTENT]:
        await update.message.reply_text(t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {media_type: []})
    try:
        file_id = (await getattr(update.message, file_attr).get_file()).file_id
        capsule_content.setdefault(media_type, []).append(file_id)
        context.user_data['capsule_content'] = capsule_content
        keyboard = [
            [InlineKeyboardButton("Завершить", callback_data="finish_capsule"),
             InlineKeyboardButton("Добавить ещё", callback_data="add_more")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(t(f'{media_type[:-1]}_added'), reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка при добавлении {media_type[:-1]}: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_video(update: Update, context: CallbackContext):
    """Обработчик добавления видео."""
    await handle_media(update, context, "videos", "video")

async def handle_audio(update: Update, context: CallbackContext):
    """Обработчик добавления аудио."""
    await handle_media(update, context, "audios", "audio")

async def handle_document(update: Update, context: CallbackContext):
    """Обработчик добавления документа."""
    await handle_media(update, context, "documents", "document")

async def handle_sticker(update: Update, context: CallbackContext):
    """Обработчик добавления стикера."""
    await handle_media(update, context, "stickers", "sticker")

async def handle_voice(update: Update, context: CallbackContext):
    """Обработчик добавления голосового сообщения."""
    await handle_media(update, context, "voices", "voice")
