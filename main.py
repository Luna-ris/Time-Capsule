import logging
import asyncio
import subprocess
import time
import os
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, List

import nest_asyncio
import pytz
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from supabase import create_client, Client

# Локализация
LOCALE = 'ru'
TRANSLATIONS = {
    'ru': {
        "start_message": (
            "Добро пожаловать в TimeCapsuleBot! 📬\n"
            "Я помогу вам создавать капсулы времени с текстом, фото, видео и другим контентом, "
            "чтобы отправить их себе или друзьям в будущем.\n"
            "Используйте кнопки ниже, чтобы начать!"
        ),
        "help_message": (
            "📋 *Список команд TimeCapsuleBot*\n\n"
            "/start - Запустить бота и открыть главное меню.\n"
            "/create_capsule - Создать новую капсулу времени.\n"
            "/add_recipient - Добавить получателей в существующую капсулу.\n"
            "*Пример:* @Friend1 @Friend2\n"
            "/view_capsules - Посмотреть список ваших капсул с их статусом.\n"
            "/send_capsule - Немедленно отправить капсулу получателям.\n"
            "/delete_capsule - Удалить капсулу, если она вам больше не нужна.\n"
            "/edit_capsule - Изменить содержимое капсулы (текст).\n"
            "/view_recipients - Показать, кто получит вашу капсулу.\n"
            "/select_send_date - Установить дату отправки капсулы.\n"
            "*Пример:* Через неделю или конкретный день.\n"
            "/support_author - Поддержать разработчика бота.\n"
            "/change_language - Сменить язык интерфейса.\n\n"
        ),
        "change_language": "🌍 Сменить язык",
        "select_language": "Выберите ваш язык:",
        "capsule_created": "✅ Капсула #{capsule_id} создана!\nДобавьте в неё текст, фото или видео.",
        "enter_recipients": (
            "👥 Введите Telegram-имена получателей через пробел.\n"
            "*Пример:* @Friend1 @Friend2\n"
            "Они получат капсулу, когда вы её отправите или наступит заданная дата."
        ),
        "select_capsule": "📦 Введите номер капсулы для действия:",
        "invalid_capsule_id": (
            "❌ Неверный ID капсулы. Проверьте список ваших капсул с помощью 'Просмотреть капсулы'."
        ),
        "recipients_added": (
            "✅ Получатели добавлены в капсулу #{capsule_id}!\n"
            "Теперь можно установить дату отправки или отправить её сразу."
        ),
        "error_general": "⚠️ Что-то пошло не так. Попробуйте снова или напишите в поддержку.",
        "service_unavailable": (
            "🛠 Сервис временно недоступен. Пожалуйста, подождите и попробуйте позже."
        ),
        "your_capsules": "📋 *Ваши капсулы времени:*\n",
        "no_capsules": "📭 У вас пока нет капсул. Создайте первую с помощью 'Создать капсулу'!",
        "created_at": "Создано",
        "status": "Статус",
        "scheduled": "⏳ Запланировано",
        "draft": "✏️ Черновик",
        "enter_capsule_id_to_send": "📨 Введите ID капсулы для немедленной отправки (например, #5):",
        "no_recipients": "❌ В этой капсуле нет получателей. Добавьте их с помощью 'Добавить получателя'.",
        "capsule_received": "🎉 Вы получили капсулу времени от @{sender}!\nВот её содержимое:",
        "capsule_sent": "📬 Капсула успешно отправлена @{recipient}!\nОни увидят её прямо сейчас.",
        "recipient_not_registered": (
            "⚠️ Получатель @{recipient} не зарегистрирован в боте и не получит капсулу."
        ),
        "confirm_delete": "🗑 Вы уверены, что хотите удалить капсулу? Это действие нельзя отменить.",
        "capsule_deleted": "✅ Капсула #{capsule_id} удалена.",
        "delete_canceled": "❌ Удаление отменено. Капсула осталась на месте.",
        "enter_new_content": "✏️ Введите новый текст для капсулы (старый будет заменён):",
        "capsule_edited": "✅ Капсула #{capsule_id} обновлена с новым содержимым!",
        "recipients_list": "👥 Получатели капсулы #{capsule_id}:\n{recipients}",
        "no_recipients_for_capsule": "📭 В капсуле #{capsule_id} пока нет получателей.",
        "choose_send_date": "📅 Когда отправить капсулу?\nВыберите один из вариантов:",
        "through_week": "Через неделю",
        "through_month": "Через месяц",
        "select_date": "Выбрать дату",
        "date_selected": "📅 Вы выбрали дату: {date}\nКапсула будет отправлена в указанное время.",
        "date_set": "✅ Дата отправки капсулы установлена на {date}. Ожидайте!",
        "support_author": (
            "💖 Поддержите автора бота:\n{url}\n"
            "Спасибо за помощь в развитии проекта!"
        ),
        "create_capsule_first": (
            "📦 Сначала создайте капсулу с помощью 'Создать капсулу', чтобы добавить в неё контент."
        ),
        "text_added": "✅ Текстовое сообщение добавлено в капсулу!",
        "photo_added": "✅ Фото добавлено в капсулу!",
        "video_added": "✅ Видео добавлено в капсулу!",
        "audio_added": "✅ Аудио добавлено в капсулу!",
        "document_added": "✅ Документ добавлен в капсулу!",
        "sticker_added": "✅ Стикер добавлен в капсулу!",
        "voice_added": "✅ Голосовое сообщение добавлено в капсулу!",
        "not_registered": "⚠️ Вы не зарегистрированы в боте. Нажмите /start, чтобы начать.",
        "not_your_capsule": (
            "❌ Эта капсула вам не принадлежит. Вы можете работать только со своими капсулами."
        ),
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "content_limit_exceeded": "⚠️ Превышен лимит: вы добавили слишком много {type}.",
        "create_capsule_btn": "📦 Создать капсулу",
        "view_capsules_btn": "📂 Просмотреть капсулы",
        "add_recipient_btn": "👤 Добавить получателя",
        "send_capsule_btn": "📨 Отправить капсулу",
        "delete_capsule_btn": "🗑 Удалить капсулу",
        "edit_capsule_btn": "✏️ Редактировать капсулу",
        "view_recipients_btn": "👥 Просмотреть получателей",
        "help_btn": "❓ Помощь",
        "select_send_date_btn": "📅 Установить дату отправки",
        "support_author_btn": "💸 Поддержать автора",
        "change_language_btn": "🌍 Сменить язык",
    },
    'en': {
        "start_message": (
            "Welcome to TimeCapsuleBot! 📬\n"
            "I’ll help you create time capsules with text, photos, videos, and more "
            "to send to yourself or friends in the future.\n"
            "Use the buttons below to get started!"
        ),
        "help_message": (
            "📋 *TimeCapsuleBot Command List*\n\n"
            "/start - Launch the bot and open the main menu.\n"
            "/create_capsule - Create a new time capsule.\n*Example:* Add text, photos, or videos.\n"
            "/add_recipient - Add recipients to an existing capsule.\n*Example:* @Friend1 @Friend2\n"
            "/view_capsules - View a list of your capsules with their status.\n"
            "/send_capsule - Send a capsule to recipients immediately.\n"
            "/delete_capsule - Delete a capsule if you no longer need it.\n"
            "/edit_capsule - Edit the capsule’s content (text).\n"
            "/view_recipients - See who will receive your capsule.\n"
            "/select_send_date - Set a send date for the capsule.\n*Example:* In a week or a specific day.\n"
            "/support_author - Support the bot’s developer.\n"
            "/change_language - Change the interface language.\n\n"
        ),
        "change_language": "🌍 Change Language",
        "select_language": "Select your language:",
        "capsule_created": "✅ Capsule #{capsule_id} created!\nAdd text, photos, or videos to it.",
        "enter_recipients": (
            "👥 Enter Telegram usernames of recipients separated by spaces.\n"
            "*Example:* @Friend1 @Friend2\n"
            "They’ll receive the capsule when you send it or the scheduled date arrives."
        ),
        "select_capsule": "📦 Enter the capsule number for the action:",
        "invalid_capsule_id": "❌ Invalid capsule ID. Check your capsule list with 'View Capsules'.",
        "recipients_added": (
            "✅ Recipients added to capsule #{capsule_id}!\n"
            "Now you can set a send date or send it immediately."
        ),
        "error_general": "⚠️ Something went wrong. Try again or contact support.",
        "service_unavailable": "🛠 Service temporarily unavailable. Please wait and try again later.",
        "your_capsules": "📋 *Your Time Capsules:*\n",
        "no_capsules": "📭 You don’t have any capsules yet. Create your first one with 'Create Capsule'!",
        "created_at": "Created",
        "status": "Status",
        "scheduled": "⏳ Scheduled",
        "draft": "✏️ Draft",
        "enter_capsule_id_to_send": "📨 Enter the capsule ID to send immediately (e.g., #5):",
        "no_recipients": "❌ This capsule has no recipients. Add them with 'Add Recipient'.",
        "capsule_received": "🎉 You’ve received a time capsule from @{sender}!\nHere’s its content:",
        "capsule_sent": "📬 Capsule successfully sent to @{recipient}!\nThey’ll see it now.",
        "recipient_not_registered": (
            "⚠️ Recipient @{recipient} isn’t registered with the bot and won’t receive the capsule."
        ),
        "confirm_delete": "🗑 Are you sure you want to delete this capsule? This action cannot be undone.",
        "capsule_deleted": "✅ Capsule #{capsule_id} deleted.",
        "delete_canceled": "❌ Deletion canceled. The capsule remains intact.",
        "enter_new_content": "✏️ Enter new text for the capsule (old content will be replaced):",
        "capsule_edited": "✅ Capsule #{capsule_id} updated with new content!",
        "recipients_list": "👥 Recipients of capsule #{capsule_id}:\n{recipients}",
        "no_recipients_for_capsule": "📭 No recipients found for capsule #{capsule_id}.",
        "choose_send_date": "📅 When should the capsule be sent?\nChoose an option:",
        "through_week": "In a week",
        "through_month": "In a month",
        "select_date": "Select a date",
        "date_selected": "📅 You’ve selected: {date}\nThe capsule will be sent at this time.",
        "date_set": "✅ Capsule send date set to {date}. Stay tuned!",
        "support_author": (
            "💖 Support the bot’s author:\n{url}\n"
            "Thanks for helping the project grow!"
        ),
        "create_capsule_first": "📦 First, create a capsule with 'Create Capsule' to add content.",
        "text_added": "✅ Text message added to the capsule!",
        "photo_added": "✅ Photo added to the capsule!",
        "video_added": "✅ Video added to the capsule!",
        "audio_added": "✅ Audio added to the capsule!",
        "document_added": "✅ Document added to the capsule!",
        "sticker_added": "✅ Sticker added to the capsule!",
        "voice_added": "✅ Voice message added to the capsule!",
        "not_registered": "⚠️ You’re not registered with the bot. Press /start to begin.",
        "not_your_capsule": "❌ This capsule doesn’t belong to you. You can only manage your own capsules.",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "content_limit_exceeded": "⚠️ Limit exceeded: you’ve added too many {type}.",
        "create_capsule_btn": "📦 Create Capsule",
        "view_capsules_btn": "📂 View Capsules",
        "add_recipient_btn": "👤 Add Recipient",
        "send_capsule_btn": "📨 Send Capsule",
        "delete_capsule_btn": "🗑 Delete Capsule",
        "edit_capsule_btn": "✏️ Edit Capsule",
        "view_recipients_btn": "👥 View Recipients",
        "help_btn": "❓ Help",
        "select_send_date_btn": "📅 Set Send Date",
        "support_author_btn": "💸 Support Author",
        "change_language_btn": "🌍 Change Language",
    },
    'es': {
        "start_message": (
            "¡Bienvenido a TimeCapsuleBot! 📬\n"
            "Te ayudaré a crear cápsulas del tiempo con texto, fotos, videos y más "
            "para enviarlas a ti mismo o a tus amigos en el futuro.\n"
            "¡Usa los botones de abajo para comenzar!"
        ),
        "help_message": (
            "📋 *Lista de comandos de TimeCapsuleBot*\n\n"
            "/start - Inicia el bot y abre el menú principal.\n"
            "/create_capsule - Crea una nueva cápsula del tiempo.\n*Ejemplo:* Agrega texto, fotos o videos.\n"
            "/add_recipient - Agrega destinatarios a una cápsula existente.\n*Ejemplo:* @Friend1 @Friend2\n"
            "/view_capsules - Ver una lista de tus cápsulas con su estado.\n"
            "/send_capsule - Envía una cápsula a los destinatarios inmediatamente.\n"
            "/delete_capsule - Elimina una cápsula si ya no la necesitas.\n"
            "/edit_capsule - Edita el contenido de la cápsula (texto).\n"
            "/view_recipients - Ver quién recibirá tu cápsula.\n"
            "/select_send_date - Establece una fecha de envío para la cápsula.\n"
            "*Ejemplo:* En una semana o un día específico.\n"
            "/support_author - Apoya al desarrollador del bot.\n"
            "/change_language - Cambia el idioma de la interfaz.\n\n"
        ),
        "change_language": "🌍 Cambiar idioma",
        "select_language": "Selecciona tu idioma:",
        "capsule_created": "✅ ¡Cápsula #{capsule_id} creada!\nAgrega texto, fotos o videos a ella.",
        "enter_recipients": (
            "👥 Ingresa los nombres de usuario de Telegram de los destinatarios separados por espacios.\n"
            "*Ejemplo:* @Friend1 @Friend2\n"
            "Ellos recibirán la cápsula cuando la envíes o llegue la fecha programada."
        ),
        "select_capsule": "📦 Ingresa el número de la cápsula para la acción:",
        "invalid_capsule_id": "❌ ID de cápsula inválido. Verifica tu lista de cápsulas con 'Ver cápsulas'.",
        "recipients_added": (
            "✅ ¡Destinatarios agregados a la cápsula #{capsule_id}!\n"
            "Ahora puedes establecer una fecha de envío o enviarla inmediatamente."
        ),
        "error_general": "⚠️ Algo salió mal. Inténtalo de nuevo o contacta con soporte.",
        "service_unavailable": (
            "🛠 El servicio no está disponible temporalmente. Por favor, espera e inténtalo de nuevo más tarde."
        ),
        "your_capsules": "📋 *Tus cápsulas del tiempo:*\n",
        "no_capsules": "📭 Todavía no tienes cápsulas. ¡Crea tu primera con 'Crear cápsula'!",
        "created_at": "Creado",
        "status": "Estado",
        "scheduled": "⏳ Programado",
        "draft": "✏️ Borrador",
        "enter_capsule_id_to_send": "📨 Ingresa el ID de la cápsula para enviar inmediatamente (por ejemplo, #5):",
        "no_recipients": "❌ Esta cápsula no tiene destinatarios. Agrega algunos con 'Agregar destinatario'.",
        "capsule_received": "🎉 ¡Has recibido una cápsula del tiempo de @{sender}!\nAquí está su contenido:",
        "capsule_sent": "📬 ¡Cápsula enviada exitosamente a @{recipient}!\nLa verán ahora.",
        "recipient_not_registered": (
            "⚠️ El destinatario @{recipient} no está registrado en el bot y no recibirá la cápsula."
        ),
        "confirm_delete": "🗑 ¿Estás seguro de que quieres eliminar esta cápsula? Esta acción no se puede deshacer.",
        "capsule_deleted": "✅ Cápsula #{capsule_id} eliminada.",
        "delete_canceled": "❌ Eliminación cancelada. La cápsula permanece intacta.",
        "enter_new_content": "✏️ Ingresa el nuevo texto para la cápsula (el contenido antiguo será reemplazado):",
        "capsule_edited": "✅ ¡Cápsula #{capsule_id} actualizada con nuevo contenido!",
        "recipients_list": "👥 Destinatarios de la cápsula #{capsule_id}:\n{recipients}",
        "no_recipients_for_capsule": "📭 No se encontraron destinatarios para la cápsula #{capsule_id}.",
        "choose_send_date": "📅 ¿Cuándo enviar la cápsula?\nElige una opción:",
        "through_week": "En una semana",
        "through_month": "En un mes",
        "select_date": "Seleccionar fecha",
        "date_selected": "📅 Has seleccionado: {date}\nLa cápsula será enviada en ese momento.",
        "date_set": "✅ Fecha de envío de la cápsula establecida para {date}. ¡Mantente atento!",
        "support_author": (
            "💖 Apoya al autor del bot:\n{url}\n"
            "¡Gracias por ayudar a que el proyecto crezca!"
        ),
        "create_capsule_first": "📦 Primero, crea una cápsula con 'Crear cápsula' para agregar contenido.",
        "text_added": "✅ ¡Mensaje de texto agregado a la cápsula!",
        "photo_added": "✅ ¡Foto agregada a la cápsula!",
        "video_added": "✅ ¡Video agregado a la cápsula!",
        "audio_added": "✅ ¡Audio agregado a la cápsula!",
        "document_added": "✅ ¡Documento agregado a la cápsula!",
        "sticker_added": "✅ ¡Sticker agregado a la cápsula!",
        "voice_added": "✅ ¡Mensaje de voz agregado a la cápsula!",
        "not_registered": "⚠️ No estás registrado en el bot. Presiona /start para comenzar.",
        "not_your_capsule": "❌ Esta cápsula no te pertenece. Solo puedes gestionar tus propias cápsulas.",
        "today": "Hoy",
        "tomorrow": "Mañana",
        "content_limit_exceeded": "⚠️ Límite excedido: has agregado demasiados {type}.",
        "create_capsule_btn": "📦 Crear Cápsula",
        "view_capsules_btn": "📂 Ver Cápsulas",
        "add_recipient_btn": "👤 Agregar Destinatario",
        "send_capsule_btn": "📨 Enviar Cápsula",
        "delete_capsule_btn": "🗑 Eliminar Cápsula",
        "edit_capsule_btn": "✏️ Editar Cápsula",
        "view_recipients_btn": "👥 Ver Destinatarios",
        "help_btn": "❓ Ayuda",
        "select_send_date_btn": "📅 Establecer Fecha de Envío",
        "support_author_btn": "💸 Apoyar al Autor",
        "change_language_btn": "🌍 Cambiar Idioma",
    },
    'fr': {
        "start_message": (
            "Bienvenue sur TimeCapsuleBot ! 📬\n"
            "Je vais vous aider à créer des capsules temporelles avec du texte, des photos, des vidéos "
            "et plus encore pour les envoyer à vous-même ou à vos amis dans le futur.\n"
            "Utilisez les boutons ci-dessous pour commencer !"
        ),
        "help_message": (
            "📋 *Liste des commandes de TimeCapsuleBot*\n\n"
            "/start - Lancez le bot et ouvrez le menu principal.\n"
            "/create_capsule - Créez une nouvelle capsule temporelle.\n*Exemple:* Ajoutez du texte, des photos ou des vidéos.\n"
            "/add_recipient - Ajoutez des destinataires à une capsule existante.\n*Exemple:* @Friend1 @Friend2\n"
            "/view_capsules - Affichez une liste de vos capsules avec leur statut.\n"
            "/send_capsule - Envoyez une capsule aux destinataires immédiatement.\n"
            "/delete_capsule - Supprimez une capsule si vous n'en avez plus besoin.\n"
            "/edit_capsule - Modifiez le contenu de la capsule (texte).\n"
            "/view_recipients - Voyez qui recevra votre capsule.\n"
            "/select_send_date - Définissez une date d'envoi pour la capsule.\n*Exemple:* Dans une semaine ou un jour spécifique.\n"
            "/support_author - Soutenez le développeur du bot.\n"
            "/change_language - Changez la langue de l'interface.\n\n"
        ),
        "change_language": "🌍 Changer de langue",
        "select_language": "Sélectionnez votre langue :",
        "capsule_created": "✅ Capsule #{capsule_id} créée !\nAjoutez-y du texte, des photos ou des vidéos.",
        "enter_recipients": (
            "👥 Entrez les noms d'utilisateur Telegram des destinataires séparés par des espaces.\n"
            "*Exemple:* @Friend1 @Friend2\n"
            "Ils recevront la capsule lorsque vous l'enverrez ou à la date programmée."
        ),
        "select_capsule": "📦 Entrez le numéro de la capsule pour l'action :",
        "invalid_capsule_id": "❌ ID de capsule invalide. Vérifiez votre liste de capsules avec 'Voir les capsules'.",
        "recipients_added": (
            "✅ Destinataires ajoutés à la capsule #{capsule_id} !\n"
            "Vous pouvez maintenant définir une date d'envoi ou l'envoyer immédiatement."
        ),
        "error_general": "⚠️ Quelque chose s'est mal passé. Réessayez ou contactez le support.",
        "service_unavailable": (
            "🛠 Le service est temporairement indisponible. Veuillez patienter et réessayer plus tard."
        ),
        "your_capsules": "📋 *Vos capsules temporelles :*\n",
        "no_capsules": "📭 Vous n'avez pas encore de capsules. Créez votre première avec 'Créer une capsule' !",
        "created_at": "Créé",
        "status": "Statut",
        "scheduled": "⏳ Programmé",
        "draft": "✏️ Brouillon",
        "enter_capsule_id_to_send": "📨 Entrez l'ID de la capsule à envoyer immédiatement (par exemple, #5) :",
        "no_recipients": "❌ Cette capsule n'a pas de destinataires. Ajoutez-en avec 'Ajouter un destinataire'.",
        "capsule_received": "🎉 Vous avez reçu une capsule temporelle de @{sender} !\nVoici son contenu :",
        "capsule_sent": "📬 Capsule envoyée avec succès à @{recipient} !\nIls la verront maintenant.",
        "recipient_not_registered": (
            "⚠️ Le destinataire @{recipient} n'est pas enregistré avec le bot et ne recevra pas la capsule."
        ),
        "confirm_delete": "🗑 Êtes-vous sûr de vouloir supprimer cette capsule ? Cette action est irréversible.",
        "capsule_deleted": "✅ Capsule #{capsule_id} supprimée.",
        "delete_canceled": "❌ Suppression annulée. La capsule reste intacte.",
        "enter_new_content": "✏️ Entrez le nouveau texte pour la capsule (l'ancien contenu sera remplacé) :",
        "capsule_edited": "✅ Capsule #{capsule_id} mise à jour avec le nouveau contenu !",
        "recipients_list": "👥 Destinataires de la capsule #{capsule_id} :\n{recipients}",
        "no_recipients_for_capsule": "📭 Aucun destinataire trouvé pour la capsule #{capsule_id}.",
        "choose_send_date": "📅 Quand envoyer la capsule ?\nChoisissez une option :",
        "through_week": "Dans une semaine",
        "through_month": "Dans un mois",
        "select_date": "Sélectionner une date",
        "date_selected": "📅 Vous avez sélectionné : {date}\nLa capsule sera envoyée à ce moment-là.",
        "date_set": "✅ Date d'envoi de la capsule définie sur {date}. Restez à l'écoute !",
        "support_author": (
            "💖 Soutenez l'auteur du bot :\n{url}\n"
            "Merci de contribuer à la croissance du projet !"
        ),
        "create_capsule_first": "📦 Créez d'abord une capsule avec 'Créer une capsule' pour ajouter du contenu.",
        "text_added": "✅ Message texte ajouté à la capsule !",
        "photo_added": "✅ Photo ajoutée à la capsule !",
        "video_added": "✅ Vidéo ajoutée à la capsule !",
        "audio_added": "✅ Audio ajouté à la capsule !",
        "document_added": "✅ Document ajouté à la capsule !",
        "sticker_added": "✅ Sticker ajouté à la capsule !",
        "voice_added": "✅ Message vocal ajouté à la capsule !",
        "not_registered": "⚠️ Vous n'êtes pas enregistré avec le bot. Appuyez sur /start pour commencer.",
        "not_your_capsule": "❌ Cette capsule ne vous appartient pas. Vous ne pouvez gérer que vos propres capsules.",
        "today": "Aujourd'hui",
        "tomorrow": "Demain",
        "content_limit_exceeded": "⚠️ Limite dépassée : vous avez ajouté trop de {type}.",
        "create_capsule_btn": "📦 Créer une Capsule",
        "view_capsules_btn": "📂 Voir les Capsules",
        "add_recipient_btn": "👤 Ajouter un Destinataire",
        "send_capsule_btn": "📨 Envoyer la Capsule",
        "delete_capsule_btn": "🗑 Supprimer la Capsule",
        "edit_capsule_btn": "✏️ Modifier la Capsule",
        "view_recipients_btn": "👥 Voir les Destinataires",
        "help_btn": "❓ Aide",
        "select_send_date_btn": "📅 Définir la Date d'Envoi",
        "support_author_btn": "💸 Soutenir l'Auteur",
        "change_language_btn": "🌍 Changer de Langue",
    },
    'de': {
        "start_message": (
            "Willkommen bei TimeCapsuleBot! 📬\n"
            "Ich helfe Ihnen, Zeitkapseln mit Text, Fotos, Videos und mehr zu erstellen, "
            "die Sie sich selbst oder Freunden in der Zukunft senden können.\n"
            "Verwenden Sie die Schaltflächen unten, um loszulegen!"
        ),
        "help_message": (
            "📋 *TimeCapsuleBot-Befehlsliste*\n\n"
            "/start - Starten Sie den Bot und öffnen Sie das Hauptmenü.\n"
            "/create_capsule - Erstellen Sie eine neue Zeitkapsel.\n*Beispiel:* Fügen Sie Text, Fotos oder Videos hinzu.\n"
            "/add_recipient - Fügen Sie Empfänger zu einer vorhandenen Kapsel hinzu.\n*Beispiel:* @Friend1 @Friend2\n"
            "/view_capsules - Zeigen Sie eine Liste Ihrer Kapseln mit deren Status an.\n"
            "/send_capsule - Senden Sie eine Kapsel sofort an die Empfänger.\n"
            "/delete_capsule - Löschen Sie eine Kapsel, wenn Sie sie nicht mehr benötigen.\n"
            "/edit_capsule - Bearbeiten Sie den Inhalt der Kapsel (Text).\n"
            "/view_recipients - Sehen Sie, wer Ihre Kapsel erhält.\n"
            "/select_send_date - Legen Sie ein Sendedatum für die Kapsel fest.\n*Beispiel:* In einer Woche oder an einem bestimmten Tag.\n"
            "/support_author - Unterstützen Sie den Entwickler des Bots.\n"
            "/change_language - Ändern Sie die Sprache der Benutzeroberfläche.\n\n"
        ),
        "change_language": "🌍 Sprache ändern",
        "select_language": "Wählen Sie Ihre Sprache:",
        "capsule_created": "✅ Kapsel #{capsule_id} erstellt!\nFügen Sie Text, Fotos oder Videos hinzu.",
        "enter_recipients": (
            "👥 Geben Sie die Telegram-Benutzernamen der Empfänger getrennt durch Leerzeichen ein.\n"
            "*Beispiel:* @Friend1 @Friend2\n"
            "Sie erhalten die Kapsel, wenn Sie sie senden oder das geplante Datum erreicht ist."
        ),
        "select_capsule": "📦 Geben Sie die Kapselnummer für die Aktion ein:",
        "invalid_capsule_id": "❌ Ungültige Kapsel-ID. Überprüfen Sie Ihre Kapselliste mit 'Kapseln anzeigen'.",
        "recipients_added": (
            "✅ Empfänger zur Kapsel #{capsule_id} hinzugefügt!\n"
            "Sie können jetzt ein Sendedatum festlegen oder sie sofort senden."
        ),
        "error_general": "⚠️ Etwas ist schief gelaufen. Versuchen Sie es erneut oder kontaktieren Sie den Support.",
        "service_unavailable": (
            "🛠 Der Dienst ist vorübergehend nicht verfügbar. Bitte warten Sie und versuchen Sie es später erneut."
        ),
        "your_capsules": "📋 *Ihre Zeitkapseln:*\n",
        "no_capsules": "📭 Sie haben noch keine Kapseln. Erstellen Sie Ihre erste mit 'Kapsel erstellen'!",
        "created_at": "Erstellt",
        "status": "Status",
        "scheduled": "⏳ Geplant",
        "draft": "✏️ Entwurf",
        "enter_capsule_id_to_send": "📨 Geben Sie die Kapsel-ID zum sofortigen Senden ein (z. B. #5):",
        "no_recipients": "❌ Diese Kapsel hat keine Empfänger. Fügen Sie welche mit 'Empfänger hinzufügen' hinzu.",
        "capsule_received": "🎉 Sie haben eine Zeitkapsel von @{sender} erhalten!\nHier ist ihr Inhalt:",
        "capsule_sent": "📬 Kapsel erfolgreich an @{recipient} gesendet!\nSie sehen sie jetzt.",
        "recipient_not_registered": (
            "⚠️ Der Empfänger @{recipient} ist nicht beim Bot registriert und erhält die Kapsel nicht."
        ),
        "confirm_delete": (
            "🗑 Sind Sie sicher, dass Sie diese Kapsel löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
        ),
        "capsule_deleted": "✅ Kapsel #{capsule_id} gelöscht.",
        "delete_canceled": "❌ Löschen abgebrochen. Die Kapsel bleibt unversehrt.",
        "enter_new_content": "✏️ Geben Sie den neuen Text für die Kapsel ein (der alte Inhalt wird ersetzt):",
        "capsule_edited": "✅ Kapsel #{capsule_id} mit neuem Inhalt aktualisiert!",
        "recipients_list": "👥 Empfänger der Kapsel #{capsule_id}:\n{recipients}",
        "no_recipients_for_capsule": "📭 Keine Empfänger für Kapsel #{capsule_id} gefunden.",
        "choose_send_date": "📅 Wann soll die Kapsel gesendet werden?\nWählen Sie eine Option:",
        "through_week": "In einer Woche",
        "through_month": "In einem Monat",
        "select_date": "Datum auswählen",
        "date_selected": "📅 Sie haben ausgewählt: {date}\nDie Kapsel wird zu diesem Zeitpunkt gesendet.",
        "date_set": "✅ Sendedatum der Kapsel auf {date} festgelegt. Bleiben Sie dran!",
        "support_author": (
            "💖 Unterstützen Sie den Autor des Bots:\n{url}\n"
            "Vielen Dank für Ihre Unterstützung beim Wachstum des Projekts!"
        ),
        "create_capsule_first": (
            "📦 Erstellen Sie zuerst eine Kapsel mit 'Kapsel erstellen', um Inhalte hinzuzufügen."
        ),
        "text_added": "✅ Textnachricht zur Kapsel hinzugefügt!",
        "photo_added": "✅ Foto zur Kapsel hinzugefügt!",
        "video_added": "✅ Video zur Kapsel hinzugefügt!",
        "audio_added": "✅ Audio zur Kapsel hinzugefügt!",
        "document_added": "✅ Dokument zur Kapsel hinzugefügt!",
        "sticker_added": "✅ Sticker zur Kapsel hinzugefügt!",
        "voice_added": "✅ Sprachnachricht zur Kapsel hinzugefügt!",
        "not_registered": "⚠️ Sie sind nicht beim Bot registriert. Drücken Sie /start, um zu beginnen.",
        "not_your_capsule": "❌ Diese Kapsel gehört Ihnen nicht. Sie können nur Ihre eigenen Kapseln verwalten.",
        "today": "Heute",
        "tomorrow": "Morgen",
        "content_limit_exceeded": "⚠️ Limit überschritten: Sie haben zu viele {type} hinzugefügt.",
        "create_capsule_btn": "📦 Kapsel Erstellen",
        "view_capsules_btn": "📂 Kapseln Anzeigen",
        "add_recipient_btn": "👤 Empfänger Hinzufügen",
        "send_capsule_btn": "📨 Kapsel Senden",
        "delete_capsule_btn": "🗑 Kapsel Löschen",
        "edit_capsule_btn": "✏️ Kapsel Bearbeiten",
        "view_recipients_btn": "👥 Empfänger Anzeigen",
        "help_btn": "❓ Hilfe",
        "select_send_date_btn": "📅 Sendedatum Festlegen",
        "support_author_btn": "💸 Autor Unterstützen",
        "change_language_btn": "🌍 Sprache Ändern",
    }
}

def t(key: str, **kwargs) -> str:
    """Получение перевода по ключу с учетом текущей локали."""
    translation = TRANSLATIONS.get(LOCALE, TRANSLATIONS['en']).get(key, key)
    return translation.format(**kwargs) if kwargs else translation

# Функции запуска сервисов
def start_process(command: str, name: str) -> bool:
    """Запуск процесса с логированием."""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"{name} запущен с PID: {process.pid}")
        time.sleep(2)
        if process.poll() is None:
            logger.info(f"{name} успешно запущен.")
            return True
        else:
            error = process.stderr.read().decode()
            logger.error(f"Ошибка запуска {name}: {error}")
            return False
    except Exception as e:
        logger.error(f"Не удалось запустить {name}: {e}")
        return False

def start_services():
    """Запуск необходимых сервисов."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.error("Переменная REDIS_URL не задана.")
        sys.exit(1)
    celery_command = "celery -A celery_config.app worker --loglevel=info --pool=solo"
    if not start_process(celery_command, "Celery"):
        logger.error("Не удалось запустить Celery.")
        sys.exit(1)

# Шифрование и дешифрование
def encrypt_data_aes(data: str, key: bytes) -> str:
    """Шифрование данных с помощью AES."""
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return (iv + encrypted).hex()

def decrypt_data_aes(encrypted_hex: str, key: bytes) -> str:
    """Дешифрование данных с помощью AES."""
    data = bytes.fromhex(encrypted_hex)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()
    return unpadded.decode('utf-8')

# Работа с Supabase
def fetch_data(table: str, query: dict = {}) -> list:
    """Получение данных из Supabase."""
    try:
        response = supabase.table(table).select("*")
        for key, value in query.items():
            response = response.eq(key, value)
        return response.execute().data
    except Exception as e:
        logger.error(f"Ошибка Supabase: {e}")
        return []

def post_data(table: str, data: dict) -> list:
    """Добавление данных в Supabase."""
    try:
        return supabase.table(table).insert(data).execute().data
    except Exception as e:
        logger.error(f"Ошибка записи в Supabase: {e}")
        return []

def update_data(table: str, query: dict, data: dict) -> list:
    """Обновление данных в Supabase."""
    try:
        query_builder = supabase.table(table).update(data)
        for key, value in query.items():
            query_builder = query_builder.eq(key, value)
        return query_builder.execute().data
    except Exception as e:
        logger.error(f"Ошибка обновления в Supabase: {e}")
        return []

def delete_data(table: str, query: dict) -> list:
    """Удаление данных из Supabase."""
    try:
        return (
            supabase.table(table)
            .delete()
            .eq(next(iter(query)), query[next(iter(query))])
            .execute()
            .data
        )
    except Exception as e:
        logger.error(f"Ошибка удаления в Supabase: {e}")
        return []

def get_chat_id(username: str) -> Optional[int]:
    """Получение chat_id по имени пользователя."""
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

def add_user(username: str, telegram_id: int, chat_id: int):
    """Добавление пользователя в базу данных."""
    if not fetch_data("users", {"telegram_id": telegram_id}):
        post_data("users", {
            "telegram_id": telegram_id,
            "username": username,
            "chat_id": chat_id
        })

def generate_unique_capsule_number(creator_id: int) -> int:
    """Генерация уникального номера капсулы для пользователя."""
    return len(fetch_data("capsules", {"creator_id": creator_id})) + 1

def create_capsule(
    creator_id: int,
    title: str,
    content: str,
    user_capsule_number: int,
    scheduled_at: Optional[datetime] = None
) -> int:
    """Создание новой капсулы."""
    encrypted_content = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    data = {
        "creator_id": creator_id,
        "title": title,
        "content": encrypted_content,
        "user_capsule_number": user_capsule_number
    }
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    response = post_data("capsules", data)
    return response[0]['id'] if response else -1

def add_recipient(capsule_id: int, recipient_username: str):
    """Добавление получателя к капсуле."""
    post_data("recipients", {
        "capsule_id": capsule_id,
        "recipient_username": recipient_username
    })

def delete_capsule(capsule_id: int):
    """Удаление капсулы и связанных данных."""
    delete_data("recipients", {"capsule_id": capsule_id})
    delete_data("capsules", {"id": capsule_id})

def edit_capsule(
    capsule_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    scheduled_at: Optional[datetime] = None
):
    """Редактирование капсулы."""
    data = {}
    if title:
        data["title"] = title
    if content:
        data["content"] = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    if data:
        update_data("capsules", {"id": capsule_id}, data)

def get_user_capsules(telegram_id: int) -> list:
    """Получение списка капсул пользователя."""
    user = fetch_data("users", {"telegram_id": telegram_id})
    return fetch_data("capsules", {"creator_id": user[0]['id']}) if user else []

def get_capsule_recipients(capsule_id: int) -> list:
    """Получение списка получателей капсулы."""
    return fetch_data("recipients", {"capsule_id": capsule_id})

# Обработчики команд
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
    """Обработчик команды /create_capsule."""
    try:
        user = update.message.from_user
        existing_user = fetch_data("users", {"telegram_id": user.id})
        if not existing_user:
            response = post_data("users", {
                "telegram_id": user.id,
                "username": user.username or str(user.id),
                "chat_id": update.message.chat_id
            })
            creator_id = response[0]['id']
        else:
            creator_id = existing_user[0]['id']
        initial_content = json.dumps({
            "text": [],
            "photos": [],
            "videos": [],
            "audios": [],
            "documents": [],
            "stickers": [],
            "voices": []
        }, ensure_ascii=False)
        user_capsule_number = generate_unique_capsule_number(creator_id)
        capsule_id = create_capsule(creator_id, "Без названия", initial_content, user_capsule_number)
        if capsule_id == -1:
            await update.message.reply_text(t('service_unavailable'))
            return
        context.user_data['current_capsule'] = capsule_id
        context.user_data['capsule_content'] = json.loads(initial_content)
        context.user_data['state'] = CREATING_CAPSULE
        await update.message.reply_text(t('capsule_created', capsule_id=capsule_id))
    except Exception as e:
        logger.error(f"Ошибка при создании капсулы: {e}")
        await update.message.reply_text(t('error_general'))

async def show_capsule_selection(update: Update, context: CallbackContext, action: str) -> bool:
    """Запрашивает номер капсулы для выполнения действия."""
    await update.message.reply_text(t('select_capsule'))
    context.user_data['action'] = action
    return True

async def add_recipient_command(update: Update, context: CallbackContext):
    """Обработчик команды /add_recipient."""
    if await show_capsule_selection(update, context, "add_recipient"):
        context.user_data['state'] = SELECTING_CAPSULE_FOR_RECIPIENTS

async def view_capsules_command(update: Update, context: CallbackContext):
    """Обработчик команды /view_capsules."""
    try:
        capsules = get_user_capsules(update.message.from_user.id)
        if capsules:
            response = [
                f"📦 #{c['id']} {c['title']}\n"
                f"🕒 {t('created_at')}: {datetime.fromisoformat(c['created_at']).strftime('%d.%m.%Y %H:%M')}\n"
                f"🔒 {t('status')}: {t('scheduled') if c['scheduled_at'] else t('draft')}"
                for c in capsules
            ]
            await update.message.reply_text(
                t('your_capsules') + "\n" + "\n".join(response),
                parse_mode="Markdown"
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

# Обработчики callback-запросов
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

async def handle_capsule_selection(update: Update, context: CallbackContext):
    """Обработчик выбора капсулы."""
    text = update.message.text.strip()
    try:
        capsule_id = int(text.replace('#', ''))
        context.user_data['selected_capsule_id'] = capsule_id
    except ValueError:
        await update.message.reply_text(t('invalid_capsule_id'))
        return
    action = context.user_data.get('action')
    if not await check_capsule_ownership(update, capsule_id):
        return
    if action == "add_recipient":
        await update.message.reply_text(t('enter_recipients'))
        context.user_data['state'] = "adding_recipient"
    elif action == "send_capsule":
        await handle_send_capsule_logic(update, context, capsule_id)
    elif action == "delete_capsule":
        await update.message.reply_text(
            t('confirm_delete'),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Да", callback_data="confirm_delete"),
                 InlineKeyboardButton("Нет", callback_data="cancel_delete")]
            ])
        )
    elif action == "edit_capsule":
        await update.message.reply_text(t('enter_new_content'))
        context.user_data['state'] = "editing_capsule_content"
    elif action == "view_recipients":
        await handle_view_recipients_logic(update, context, capsule_id)
    elif action == "select_send_date":
        keyboard = [
            [InlineKeyboardButton(t('through_week'), callback_data='week')],
            [InlineKeyboardButton(t('through_month'), callback_data='month')],
            [InlineKeyboardButton(t('select_date'), callback_data='calendar')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(t('choose_send_date'), reply_markup=reply_markup)
        context.user_data['state'] = "selecting_send_date"

async def handle_date_buttons(update: Update, context: CallbackContext):
    """Обработчик выбора даты отправки."""
    query = update.callback_query
    if query.data == 'week':
        send_date = datetime.now(pytz.utc) + timedelta(weeks=1)
        context.user_data['send_date'] = send_date
        await query.edit_message_text(t('date_selected', date=send_date.strftime('%d.%m.%Y %H:%M')))
        await save_send_date(update, context)
    elif query.data == 'month':
        send_date = datetime.now(pytz.utc) + timedelta(days=30)
        context.user_data['send_date'] = send_date
        await query.edit_message_text(t('date_selected', date=send_date.strftime('%d.%m.%Y %H:%M')))
        await save_send_date(update, context)
    elif query.data == 'calendar':
        await query.edit_message_text(
            "📅 Пожалуйста, введите дату и время отправки в формате ЧЧ:ММ ДД.ММ.ГГГГ.\n"
            "Пример: 21:12 17.03.2025\n"
        )
        context.user_data['state'] = "entering_custom_date"

async def handle_calendar_selection(update: Update, context: CallbackContext):
    """Обработчик выбора даты из календаря (устаревшая функция)."""
    query = update.callback_query
    selected_day = int(query.data.split('_')[1])
    send_date = datetime.now(pytz.utc).replace(day=selected_day, hour=0, minute=0, second=0, microsecond=0)
    context.user_data['send_date'] = send_date
    await query.edit_message_text(t('date_selected', date=send_date.strftime('%d.%m.%Y %H:%M')))
    await save_send_date(update, context)

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

async def handle_text(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений."""
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
    elif state == CREATING_CAPSULE:
        await handle_create_capsule_steps(update, context, text)
    elif state == "adding_recipient":
        await handle_recipient(update, context)
    elif state == "editing_capsule_content":
        await handle_edit_capsule_content(update, context)
    elif state == "entering_custom_date":
        await handle_custom_date_input(update, context, text)
    elif state in [
        SELECTING_CAPSULE_FOR_RECIPIENTS,
        "sending_capsule",
        "deleting_capsule",
        "editing_capsule",
        "viewing_recipients",
        SELECTING_CAPSULE
    ]:
        await handle_capsule_selection(update, context)
    else:
        await update.message.reply_text(t('create_capsule_first'))

async def handle_custom_date_input(update: Update, context: CallbackContext, text: str):
    """Обработчик ввода пользовательской даты."""
    try:
        local_tz = pytz.timezone('Europe/Moscow')  # Замените на ваш часовой пояс
        naive_date = datetime.strptime(text, '%H:%M %d.%m.%Y')
        local_date = local_tz.localize(naive_date)
        send_date = local_date.astimezone(pytz.utc)

        now = datetime.now(pytz.utc)
        if send_date <= now:
            await update.message.reply_text(
                "❌ Ошибка: Укажите дату и время в будущем.\n"
                "Пример: 21:12 17.03.2025"
            )
            return

        context.user_data['send_date'] = send_date
        await update.message.reply_text(t('date_selected', date=local_date.strftime('%d.%m.%Y %H:%M')))
        await save_send_date(update, context)
        context.user_data['state'] = "idle"
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты. Используйте формат ЧЧ:ММ ДД.ММ.ГГГГ.\n"
            "Пример: 21:12 17.03.2025"
        )

async def handle_create_capsule_steps(update: Update, context: CallbackContext, text: str):
    """Обработчик шагов создания капсулы."""
    capsule_content = context.user_data.get('capsule_content', {"text": []})
    capsule_content['text'].append(text)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(t('text_added'))

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
            await update.message.reply_text(t('invalid_capsule_id'))
            return
        recipients = get_capsule_recipients(capsule_id)
        if not recipients:
            await update.message.reply_text(t('no_recipients'))
            return
        content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
        for recipient in recipients:
            chat_id = get_chat_id(recipient['recipient_username'])
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=t('capsule_received', sender=update.effective_user.username)
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
                await update.message.reply_text(t('capsule_sent', recipient=recipient['recipient_username']))
            else:
                await update.message.reply_text(t('recipient_not_registered', recipient=recipient['recipient_username']))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.message.reply_text(t('service_unavailable'))

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
            await update.message.reply_text(t('recipients_list', capsule_id=capsule_id, recipients=recipient_list))
        else:
            await update.message.reply_text(t('no_recipients_for_capsule', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_photo(update: Update, context: CallbackContext):
    """Обработчик добавления фото в капсулу."""
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"photos": []})
    photo_file_id = (await update.message.photo[-1].get_file()).file_id
    capsule_content.setdefault('photos', []).append(photo_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(t('photo_added'))

async def handle_media(update: Update, context: CallbackContext, media_type: str, file_attr: str):
    """Обработчик медиафайлов."""
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {media_type: []})
    try:
        file_id = (await getattr(update.message, file_attr).get_file()).file_id
        capsule_content.setdefault(media_type, []).append(file_id)
        context.user_data['capsule_content'] = capsule_content
        save_capsule_content(context, context.user_data['current_capsule'])
        await update.message.reply_text(t(f'{media_type[:-1]}_added'))
        logger.info(f"Добавлен {media_type[:-1]} в капсулу #{context.user_data['current_capsule']}")
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

# Вспомогательные функции
async def check_capsule_ownership(update: Update, capsule_id: int, query=None) -> bool:
    """Проверка владения капсулой."""
    user = fetch_data("users", {"telegram_id": update.effective_user.id})
    if not user:
        if query:
            await query.edit_message_text(t('not_registered'))
        else:
            await update.message.reply_text(t('not_registered'))
        return False
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule or capsule[0]['creator_id'] != user[0]['id']:
        if query:
            await query.edit_message_text(t('not_your_capsule'))
        else:
            await update.message.reply_text(t('not_your_capsule'))
        return False
    return True

def save_capsule_content(context: CallbackContext, capsule_id: int):
    """Сохранение содержимого капсулы."""
    content = context.user_data.get('capsule_content', {})
    json_str = json.dumps(content, ensure_ascii=False)
    encrypted = encrypt_data_aes(json_str, ENCRYPTION_KEY_BYTES)
    update_data("capsules", {"id": capsule_id}, {"content": encrypted})

async def save_send_date(update: Update, context: CallbackContext):
    """Сохранение даты отправки капсулы."""
    try:
        send_date = context.user_data.get('send_date')
        capsule_id = context.user_data.get('selected_capsule_id')
        if not send_date or not capsule_id:
            await update.callback_query.edit_message_text(t('error_general'))
            return

        edit_capsule(capsule_id, scheduled_at=send_date)
        logger.info(f"Планирую задачу для капсулы {capsule_id} на {send_date}")
        send_capsule_task.apply_async((capsule_id,), eta=send_date)
        logger.info(f"Задача для капсулы {capsule_id} успешно запланирована")

        await update.callback_query.edit_message_text(t('date_set', date=send_date.strftime('%d.%m.%Y %H:%M')))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при установке даты для капсулы {capsule_id}: {e}")
        await update.callback_query.edit_message_text(t('error_general'))

async def post_init(application):
    """Инициализация задач после запуска бота."""
    logger.info("Начало инициализации задач")
    try:
        capsules = fetch_data("capsules")
        logger.info(f"Найдено {len(capsules)} капсул в базе данных")

        now = datetime.now(pytz.utc)
        logger.info(f"Текущее время UTC: {now}")

        for capsule in capsules:
            if capsule.get('scheduled_at'):
                scheduled_at = datetime.fromisoformat(capsule['scheduled_at']).replace(tzinfo=pytz.utc)
                logger.info(f"Обработка капсулы {capsule['id']}, запланированной на {scheduled_at}")

                if scheduled_at > now:
                    logger.info(f"Добавление задачи для капсулы {capsule['id']} в Celery")
                    send_capsule_task.apply_async((capsule['id'],), eta=scheduled_at)
                    logger.info(f"Задача для капсулы {capsule['id']} запланирована на {scheduled_at}")
        logger.info("Инициализация задач завершена")
    except Exception as e:
        logger.error(f"Не удалось инициализировать задачи: {e}")

async def check_bot_permissions(context: CallbackContext):
    """Проверка прав бота."""
    me = await context.bot.get_me()
    logger.info(f"Бот запущен как @{me.username}")

# Главная функция
async def main():
    """Запуск бота."""
    start_services()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    await check_bot_permissions(application)

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create_capsule", create_capsule_command))
    application.add_handler(CommandHandler("add_recipient", add_recipient_command))
    application.add_handler(CommandHandler("view_capsules", view_capsules_command))
    application.add_handler(CommandHandler("send_capsule", send_capsule_command))
    application.add_handler(CommandHandler("delete_capsule", delete_capsule_command))
    application.add_handler(CommandHandler("edit_capsule", edit_capsule_command))
    application.add_handler(CommandHandler("view_recipients", view_recipients_command))
    application.add_handler(CommandHandler("support_author", support_author))
    application.add_handler(CommandHandler("select_send_date", select_send_date))
    application.add_handler(CommandHandler("change_language", change_language))

    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r'^(ru|en|es|fr|de)$'))
    application.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r'^(week|month|calendar)$'))
    application.add_handler(CallbackQueryHandler(handle_calendar_selection, pattern=r'^day_\d+$'))
    application.add_handler(CallbackQueryHandler(
        handle_delete_confirmation,
        pattern=r'^(confirm_delete|cancel_delete)$'
    ))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    await application.initialize()
    await post_init(application)
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # Загрузка переменных окружения
    load_dotenv()
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default_key_32_bytes_long!!!!!!!")
    ENCRYPTION_KEY_BYTES = ENCRYPTION_KEY.encode('utf-8')[:32].ljust(32, b'\0')

    # Инициализация Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Константы состояний
    CREATING_CAPSULE = "creating_capsule"
    SELECTING_CAPSULE = "selecting_capsule"
    SELECTING_CAPSULE_FOR_RECIPIENTS = "selecting_capsule_for_recipients"

    # Запуск бота
    nest_asyncio.apply()
    asyncio.run(main())
