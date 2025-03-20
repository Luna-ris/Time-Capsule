import logging

logger = logging.getLogger(__name__)

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
        "select_capsule": "📦 Выберите капсулу для действия:",
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
        "select_date": "Ввести свою дату",
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
        "select_capsule": "📦 Select a capsule for the action:",
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
        "select_date": "Enter your own date",
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
            "/select_send_date - Establece una fecha de envío para la cápsula.\n*Ejemplo:* En una semana o un día específico.\n"
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
        "select_capsule": "📦 Selecciona una cápsula para la acción:",
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
        "select_date": "Ingresar tu propia fecha",
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
        "select_capsule": "📦 Sélectionnez une capsule pour l'action :",
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
        "select_date": "Entrer votre propre date",
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
        "edit_capsule_btn": "✏️ Éditer la Capsule",
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
        "select_capsule": "📦 Wählen Sie eine Kapsel für die Aktion aus:",
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
        "select_date": "Eigene Datum eingeben",
        "date_selected": "📅 Sie haben ausgewählt: {date}\nDie Kapsel wird zu diesem Zeitpunkt gesendet.",
        "date_set": "✅ Sendedatum der Kapsel auf {date} festgelegt. Bleiben Sie dran!",
        "support_author": (
            "💖 Unterstützen Sie den Autor des Bots:\n{url}\n"
            "Vielen Dank für Ihre Unterstützung beim Wachstum des Projekts!"
        ),
        "create_capsule_first": "📦 Erstellen Sie zuerst eine Kapsel mit 'Kapsel erstellen', um Inhalte hinzuzufügen.",
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

def t(key: str, locale: str = None, **kwargs) -> str:
    """Получение перевода по ключу с учетом текущей локали."""
    locale_to_use = locale if locale else LOCALE
    logger.debug(f"Fetching translation for key '{key}' in locale '{locale_to_use}'")
    
    translation = TRANSLATIONS.get(locale_to_use, TRANSLATIONS['en']).get(key, key)
    return translation.format(**kwargs) if kwargs else translation
