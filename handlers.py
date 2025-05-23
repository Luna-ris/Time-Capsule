import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from config import logger, ENCRYPTION_KEY_BYTES
from crypto import decrypt_data_aes
from localization import t, LOCALE
from database import (
    fetch_data, post_data, add_user, create_capsule, add_recipient,
    get_user_capsules, get_capsule_recipients, delete_capsule,
    generate_unique_capsule_number, update_data, get_chat_id
)
from utils import check_capsule_ownership, save_capsule_content, convert_to_utc, save_send_date
import pytz

CREATING_CAPSULE_TITLE = "creating_capsule_title"
CREATING_CAPSULE_CONTENT = "creating_capsule_content"
CREATING_CAPSULE_RECIPIENTS = "creating_capsule_recipients"
CREATING_CAPSULE_DATE = "creating_capsule_date"
SELECTING_CAPSULE = "selecting_capsule"
SELECTING_CAPSULE_FOR_RECIPIENTS = "selecting_capsule_for_recipients"

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start."""
    user = update.effective_user
    add_user(user.username or str(user.id), user.id, update.effective_chat.id)
    keyboard = [
        [t("create_capsule_btn", locale=LOCALE), t("view_capsules_btn", locale=LOCALE)],
        [t("add_recipient_btn", locale=LOCALE), t("send_capsule_btn", locale=LOCALE)],
        [t("delete_capsule_btn", locale=LOCALE), t("view_recipients_btn", locale=LOCALE)],
        [t("help_btn", locale=LOCALE)],
        [t("select_send_date_btn", locale=LOCALE), t("support_author_btn", locale=LOCALE)],
        [t("change_language_btn", locale=LOCALE)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.effective_message.reply_text(t('start_message', locale=LOCALE), reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help."""
    keyboard = [
        [t("create_capsule_btn", locale=LOCALE), t("view_capsules_btn", locale=LOCALE)],
        [t("add_recipient_btn", locale=LOCALE), t("send_capsule_btn", locale=LOCALE)],
        [t("delete_capsule_btn", locale=LOCALE), t("view_recipients_btn", locale=LOCALE)],
        [t("help_btn", locale=LOCALE)],
        [t("select_send_date_btn", locale=LOCALE), t("support_author_btn", locale=LOCALE)],
        [t("change_language_btn", locale=LOCALE)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.effective_message.reply_text(t('help_message', locale=LOCALE), reply_markup=reply_markup)

async def create_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /create_capsule — начало пошагового мастера."""
    context.user_data['state'] = CREATING_CAPSULE_TITLE
    context.user_data['capsule_content'] = {"text": [], "photos": [], "videos": [], "audios": [],
                                            "documents": [], "stickers": [], "voices": []}
    await update.effective_message.reply_text("📦 Введите название капсулы:")

async def show_capsule_selection(update: Update, context: CallbackContext, action: str):
    """Отображение инлайн-меню для выбора капсулы с пагинацией."""
    capsules = get_user_capsules(update.effective_user.id)
    if not capsules:
        await update.effective_message.reply_text(t('no_capsules', locale=LOCALE))
        return False

    capsules = sorted(capsules, key=lambda x: x['id'])
    logger.info(f"Найдено {len(capsules)} капсул для пользователя {update.effective_user.id}")

    page_key = f"{action}_page"
    page = context.user_data.get(page_key, 1)
    capsules_per_page = 10
    total_pages = (len(capsules) + capsules_per_page - 1) // capsules_per_page

    page = max(1, min(page, total_pages))
    logger.info(f"Отображение страницы {page} из {total_pages} для действия {action}")

    start_idx = (page - 1) * capsules_per_page
    end_idx = start_idx + capsules_per_page
    current_capsules = capsules[start_idx:end_idx]
    logger.info(f"Выбраны капсулы с индекса {start_idx} по {end_idx}: {len(current_capsules)} капсул")

    keyboard = []
    row = []
    for i, capsule in enumerate(current_capsules):
        button_text = f"📦 #{capsule['id']}: {capsule['title']}"[:30]
        button = InlineKeyboardButton(button_text, callback_data=f"{action}_{capsule['id']}")
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"{action}_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Следующая ➡️", callback_data=f"{action}_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    response = f"📋 {t('select_capsule', locale=LOCALE)} (Страница {page} из {total_pages}):\n\n"
    if update.callback_query:
        await update.callback_query.edit_message_text(response, reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text(response, reply_markup=reply_markup)

    context.user_data[page_key] = page
    context.user_data['action'] = action
    return True

async def add_recipient_command(update: Update, context: CallbackContext):
    """Обработчик команды /add_recipient."""
    if await show_capsule_selection(update, context, "add_recipient"):
        context.user_data['state'] = SELECTING_CAPSULE_FOR_RECIPIENTS

async def view_capsules_command(update: Update, context: CallbackContext):
    """Обработчик команды /view_capsules с улучшенным отображением и пагинацией."""
    try:
        capsules = get_user_capsules(update.effective_user.id)
        if not capsules:
            if update.callback_query:
                await update.callback_query.edit_message_text(t('no_capsules', locale=LOCALE))
            else:
                await update.effective_message.reply_text(t('no_capsules', locale=LOCALE))
            return

        capsules = sorted(capsules, key=lambda x: x['id'])

        page = context.user_data.get('view_capsules_page', 1)
        capsules_per_page = 5
        total_pages = (len(capsules) + capsules_per_page - 1) // capsules_per_page

        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * capsules_per_page
        end_idx = start_idx + capsules_per_page
        current_capsules = capsules[start_idx:end_idx]

        response = f"📋 {t('your_capsules', locale=LOCALE)} (Страница {page} из {total_pages}):\n\n"
        keyboard = []
        for capsule in current_capsules:
            button_text = f"📦 #{capsule['id']} {capsule['title']}"[:40]
            button = InlineKeyboardButton(button_text, callback_data=f"view_{capsule['id']}")
            keyboard.append([button])

        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"view_page_{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Следующая ➡️", callback_data=f"view_page_{page+1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(response, reply_markup=reply_markup)
        else:
            await update.effective_message.reply_text(response, reply_markup=reply_markup)

        context.user_data['view_capsules_page'] = page

    except Exception as e:
        logger.error(f"Ошибка при получении капсул: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(t('error_general', locale=LOCALE))
        else:
            await update.effective_message.reply_text(t('error_general', locale=LOCALE))

async def send_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /send_capsule."""
    if await show_capsule_selection(update, context, "send_capsule"):
        context.user_data['state'] = "sending_capsule"

async def delete_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /delete_capsule."""
    if await show_capsule_selection(update, context, "delete_capsule"):
        context.user_data['state'] = "deleting_capsule"

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
    await update.effective_message.reply_text(t('support_author', url=DONATION_URL, locale=LOCALE))

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
    await update.effective_message.reply_text(t('select_language', locale=LOCALE), reply_markup=reply_markup)

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
        [t("create_capsule_btn", locale=LOCALE), t("view_capsules_btn", locale=LOCALE)],
        [t("add_recipient_btn", locale=LOCALE), t("send_capsule_btn", locale=LOCALE)],
        [t("delete_capsule_btn", locale=LOCALE), t("view_recipients_btn", locale=LOCALE)],
        [t("help_btn", locale=LOCALE)],
        [t("select_send_date_btn", locale=LOCALE), t("support_author_btn", locale=LOCALE)],
        [t("change_language_btn", locale=LOCALE)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t('start_message', locale=LOCALE),
        reply_markup=reply_markup
    )

async def handle_inline_selection(update: Update, context: CallbackContext):
    """Обработчик выбора капсулы через инлайн-меню."""
    query = update.callback_query
    logger.info(f"handle_inline_selection вызвана с callback_data: {query.data}")
    try:
        parts = query.data.split('_')
        if len(parts) < 2:
            raise ValueError("Неверный формат callback_data")

        if parts[-2] == "page":
            action_type = "_".join(parts[:-2])
            page_number = int(parts[-1])
            context.user_data[f"{action_type}_page"] = page_number
            logger.info(f"Переход на страницу {page_number} для действия {action_type}")
            await show_capsule_selection(update, context, action_type)
            return
        else:
            action = "_".join(parts[:-1])
            value = int(parts[-1])

        context.user_data['selected_capsule_id'] = value

        if not await check_capsule_ownership(update, value, query):
            logger.info(f"Пользователь {update.effective_user.id} не владеет капсулой {value}")
            await query.edit_message_text("🚫 Вы не являетесь владельцем этой капсулы.")
            return

        if action == "add_recipient":
            await query.edit_message_text(t('enter_recipients', locale=LOCALE))
            context.user_data['state'] = "adding_recipient"
        elif action == "send_capsule":
            await preview_capsule(update, context, value, show_buttons=True)
        elif action == "delete_capsule":
            await query.edit_message_text(
                t('confirm_delete', locale=LOCALE),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Да", callback_data="confirm_delete"),
                     InlineKeyboardButton("Нет", callback_data="cancel_delete")]
                ])
            )
        elif action == "view_recipients":
            await handle_view_recipients_logic(update, context, value)
        elif action == "select_send_date":
            keyboard = [
                [InlineKeyboardButton(t("through_week", locale=LOCALE), callback_data="week")],
                [InlineKeyboardButton(t("through_month", locale=LOCALE), callback_data="month")],
                [InlineKeyboardButton(t("select_date", locale=LOCALE), callback_data="custom")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(t('choose_send_date', locale=LOCALE), reply_markup=reply_markup)
        elif action == "view":
            await preview_capsule(update, context, value, show_buttons=False)
    except Exception as e:
        logger.error(f"Ошибка в handle_inline_selection: {query.data}, ошибка: {str(e)}, тип: {type(e).__name__}")
        await query.edit_message_text(f"⚠️ Ошибка: {str(e)}. Пожалуйста, попробуйте снова.")

async def preview_capsule(update: Update, context: CallbackContext, capsule_id: int, show_buttons: bool = True):
    """Предпросмотр капсулы перед отправкой или просмотром."""
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule:
        await update.callback_query.edit_message_text(t('invalid_capsule_id', locale=LOCALE))
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

    if show_buttons:
        keyboard = [
            [InlineKeyboardButton("Отправить", callback_data="confirm_send"),
             InlineKeyboardButton("Отмена", callback_data="cancel_send")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = None

    await update.callback_query.edit_message_text(preview_text, reply_markup=reply_markup)

async def handle_date_buttons(update: Update, context: CallbackContext):
    """Обработчик кнопок выбора даты отправки."""
    query = update.callback_query
    logger.info(f"handle_date_buttons вызвана с callback_data: {query.data}")
    try:
        if query.data == 'week':
            send_date = datetime.now(pytz.utc) + timedelta(weeks=1)
            await save_send_date(update, context, send_date)
            await query.edit_message_text(f"📅 Дата отправки установлена: через неделю ({send_date.strftime('%d.%m.%Y %H:%M:%S')})")
        elif query.data == 'month':
            send_date = datetime.now(pytz.utc) + timedelta(days=30)
            await save_send_date(update, context, send_date)
            await query.edit_message_text(f"📅 Дата отправки установлена: через месяц ({send_date.strftime('%d.%m.%Y %H:%M:%S')})")
        elif query.data == 'custom':
            await query.edit_message_text(
                "📅 Введите дату и время отправки в формате 'день.месяц.год час:минута:секунда'.\n"
                "Пример: 17.03.2025 21:12:00"
            )
            context.user_data['state'] = "entering_custom_date"
    except Exception as e:
        logger.error(f"Ошибка в handle_date_buttons: {e}")
        await query.edit_message_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте снова.")

async def handle_delete_confirmation(update: Update, context: CallbackContext):
    """Обработчик подтверждения удаления капсулы."""
    query = update.callback_query
    if query.data == "confirm_delete":
        capsule_id = context.user_data.get('selected_capsule_id')
        delete_capsule(capsule_id)
        await query.edit_message_text(t('capsule_deleted', capsule_id=capsule_id, locale=LOCALE))
    else:
        await query.edit_message_text(t('delete_canceled', locale=LOCALE))
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
        t("create_capsule_btn", locale=LOCALE): create_capsule_command,
        t("view_capsules_btn", locale=LOCALE): view_capsules_command,
        t("add_recipient_btn", locale=LOCALE): add_recipient_command,
        t("send_capsule_btn", locale=LOCALE): send_capsule_command,
        t("delete_capsule_btn", locale=LOCALE): delete_capsule_command,
        t("view_recipients_btn", locale=LOCALE): view_recipients_command,
        t("help_btn", locale=LOCALE): help_command,
        t("select_send_date_btn", locale=LOCALE): select_send_date,
        t("support_author_btn", locale=LOCALE): support_author,
        t("change_language_btn", locale=LOCALE): change_language
    }
    if text in actions:
        await actions[text](update, context)
    elif state == CREATING_CAPSULE_TITLE:
        await handle_capsule_title(update, context, text)
    elif state == CREATING_CAPSULE_CONTENT:
        await handle_create_capsule_content(update, context, text)
    elif state == CREATING_CAPSULE_RECIPIENTS:
        await handle_recipient(update, context)
    elif state == "adding_recipient":
        await handle_recipient(update, context)
    elif state == "entering_custom_date":
        await handle_select_send_date(update, context, text)
    else:
        await update.effective_message.reply_text(t('create_capsule_first', locale=LOCALE))

async def handle_capsule_title(update: Update, context: CallbackContext, title: str):
    """Обработка названия капсулы."""
    context.user_data['capsule_title'] = title
    context.user_data['state'] = CREATING_CAPSULE_CONTENT
    await update.effective_message.reply_text("📝 Добавьте контент в капсулу (текст, фото, видео и т.д.):")

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
    await update.effective_message.reply_text(t('text_added', locale=LOCALE), reply_markup=reply_markup)
    context.user_data['state'] = CREATING_CAPSULE_CONTENT

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
        await query.edit_message_text(t('capsule_created', capsule_id=capsule_id, locale=LOCALE) + "\n👥 Укажите получателей (например, @Friend1 @Friend2):")
    elif query.data == "add_more":
        await query.edit_message_text("📝 Добавьте ещё контент в капсулу:")

async def handle_select_send_date(update: Update, context: CallbackContext, text: str):
    """Обработчик ввода пользовательской даты отправки."""
    try:
        send_date_naive = datetime.strptime(text, "%d.%m.%Y %H:%M:%S")
        send_date_utc = convert_to_utc(text)
        now = datetime.now(pytz.utc)
        if send_date_utc <= now:
            await update.effective_message.reply_text(
                "❌ Ошибка: Укажите дату и время в будущем.\nПример: 17.03.2025 21:12:00"
            )
            return
        await save_send_date(update, context, send_date_utc, is_message=True)
        if context.user_data.get('state') == CREATING_CAPSULE_DATE:
            await finalize_capsule_creation(update, context)
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Неверный формат даты. Используйте формат 'день.месяц.год час:минута:секунда'.\nПример: 17.03.2025 21:12:00"
        )
    except Exception as e:
        logger.error(f"Ошибка при установке даты отправки: {e}")
        await update.effective_message.reply_text(t('error_general', locale=LOCALE))

async def finalize_capsule_creation(update: Update, context: CallbackContext):
    """Завершение создания капсулы."""
    capsule_id = context.user_data['current_capsule']
    await update.effective_message.reply_text(t('recipients_added', capsule_id=capsule_id, locale=LOCALE))
    context.user_data['state'] = "idle"
    context.user_data.pop('capsule_title', None)
    context.user_data.pop('capsule_content', None)
    context.user_data.pop('capsule_recipients', None)
    context.user_data.pop('current_capsule', None)

async def handle_recipient(update: Update, context: CallbackContext):
    """Обработчик добавления получателей."""
    try:
        usernames = set(update.message.text.strip().split())
        capsule_id = context.user_data.get('current_capsule') or context.user_data.get('selected_capsule_id')
        for username in usernames:
            add_recipient(capsule_id, username.lstrip('@'))
        await update.effective_message.reply_text(t('recipients_added', capsule_id=capsule_id, locale=LOCALE))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателя: {e}")
        await update.effective_message.reply_text(t('error_general', locale=LOCALE))

async def handle_send_capsule_logic(update: Update, context: CallbackContext, capsule_id: int):
    """Логика отправки капсулы."""
    try:
        capsule = fetch_data("capsules", {"id": capsule_id})
        if not capsule:
            await update.callback_query.edit_message_text(t('invalid_capsule_id', locale=LOCALE))
            return
        recipients = get_capsule_recipients(capsule_id)
        if not recipients:
            await update.callback_query.edit_message_text(t('no_recipients', locale=LOCALE))
            return
        content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
        for recipient in recipients:
            chat_id = get_chat_id(recipient['recipient_username'])
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=t('capsule_received', sender=update.effective_user.username or "Unknown", locale=LOCALE)
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
                await update.callback_query.edit_message_text(t('capsule_sent', recipient=recipient['recipient_username'], locale=LOCALE))
            else:
                await update.callback_query.edit_message_text(t('recipient_not_registered', recipient=recipient['recipient_username'], locale=LOCALE))
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.callback_query.edit_message_text(t('service_unavailable', locale=LOCALE))

async def handle_view_recipients_logic(update: Update, context: CallbackContext, capsule_id: int):
    """Логика просмотра получателей капсулы."""
    try:
        recipients = get_capsule_recipients(capsule_id)
        if recipients:
            recipient_list = "\n".join([f"@{r['recipient_username']}" for r in recipients])
            await update.callback_query.edit_message_text(t('recipients_list', capsule_id=capsule_id, recipients=recipient_list, locale=LOCALE))
        else:
            await update.callback_query.edit_message_text(t('no_recipients_for_capsule', capsule_id=capsule_id, locale=LOCALE))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.callback_query.edit_message_text(t('error_general', locale=LOCALE))

async def handle_media(update: Update, context: CallbackContext, media_type: str, file_attr: str):
    """Обработчик медиафайлов."""
    if context.user_data.get('state') not in [CREATING_CAPSULE_CONTENT]:
        await update.effective_message.reply_text(t('create_capsule_first', locale=LOCALE))
        return
    capsule_content = context.user_data.get('capsule_content', {media_type: []})
    try:
        if media_type == "photos":
            file_id = (await update.message.photo[-1].get_file()).file_id
        elif media_type == "videos":
            file_id = (await update.message.video.get_file()).file_id
        elif media_type == "audios":
            file_id = (await update.message.audio.get_file()).file_id
        elif media_type == "documents":
            file_id = (await update.message.document.get_file()).file_id
        elif media_type == "stickers":
            file_id = (await update.message.sticker.get_file()).file_id
        elif media_type == "voices":
            file_id = (await update.message.voice.get_file()).file_id
        else:
            raise ValueError(f"Неизвестный тип медиа: {media_type}")

        capsule_content.setdefault(media_type, []).append(file_id)
        context.user_data['capsule_content'] = capsule_content
        keyboard = [
            [InlineKeyboardButton("Завершить", callback_data="finish_capsule"),
             InlineKeyboardButton("Добавить ещё", callback_data="add_more")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(t(f'{media_type[:-1]}_added', locale=LOCALE), reply_markup=reply_markup)
        context.user_data['state'] = CREATING_CAPSULE_CONTENT
    except Exception as e:
        logger.error(f"Ошибка при добавлении {media_type[:-1]}: {e}")
        await update.effective_message.reply_text(t('error_general', locale=LOCALE))

async def handle_photo(update: Update, context: CallbackContext):
    """Обработчик добавления фото в капсулу."""
    await handle_media(update, context, "photos", "photo")

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
