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
            "📋 Руководство по использованию TimeCapsuleBot\n\n"
            "TimeCapsuleBot позволяет создавать капсулы времени, которые можно отправить себе или друзьям в будущем. "
            "Вот как пользоваться ботом шаг за шагом:\n\n"
            "1. Создание капсулы (/create_capsule)\n"
            "- Нажмите 'Создать капсулу' или введите /create_capsule.\n"
            "- Введите название капсулы.\n"
            "- Добавьте контент: текст, фото, видео, аудио, стикеры или документы.\n"
            "- После каждого добавления выбирайте 'Добавить ещё' или 'Завершить'.\n"
            "- Укажите получателей (например, @Friend1 @Friend2).\n"
            "- (Опционально) Установите дату отправки через команду 'Установить дату отправки'.\n\n"
            "2. Управление капсулами\n"
            "- Просмотреть капсулы (/view_capsules): Посмотрите список ваших капсул.\n"
            "- Добавить получателя (/add_recipient): Добавьте новых получателей к существующей капсуле.\n"
            "- Отправить капсулу (/send_capsule): Немедленно отправьте капсулу всем получателям.\n"
            "- Удалить капсулу (/delete_capsule): Удалите ненужную капсулу.\n"
            "- Просмотреть получателей (/view_recipients): Узнайте, кто получит капсулу.\n"
            "- Установить дату отправки (/select_send_date): Задайте, когда капсула будет отправлена (например, через неделю, месяц или выберите свою дату).\n\n"
            "3. Даты отправки\n"
            "- Если вы использовали 'Установить дату отправки' после создания капсулы, она будет отправлена в указанное время.\n"
            "- Без даты капсула останется в черновиках, пока вы не отправите её вручную.\n\n"
            "Дополнительно\n"
            "- Поддержать автора (/support_author): Помогите развитию бота.\n"
            "- Сменить язык (/change_language): Выберите удобный язык интерфейса.\n\n"
            "Если что-то неясно, пишите @TimeCapsuleSupport! Начните с команды /start."
        ),
        "change_language": "🌍 Сменить язык",
        "select_language": "Выберите ваш язык:",
        "capsule_created": "✅ Капсула #{capsule_id} создана!\nДобавьте в неё текст, фото или видео.",
        "enter_recipients": (
            "👥 Введите Telegram-имена получателей через пробел.\n"
            "Пример: @Friend1 @Friend2\n"
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
        "your_capsules": "📋 Ваши капсулы времени:\n",
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
            "📋 TimeCapsuleBot Guide\n\n"
            "TimeCapsuleBot allows you to create time capsules that can be sent to yourself or friends in the future. "
            "Here’s how to use the bot step by step:\n\n"
            "1. Creating a Capsule (/create_capsule)\n"
            "- Click 'Create Capsule' or enter /create_capsule.\n"
            "- Enter a name for the capsule.\n"
            "- Add content: text, photos, videos, audio, stickers, or documents.\n"
            "- After each addition, choose 'Add More' or 'Finish'.\n"
            "- Specify the recipients (e.g., @Friend1 @Friend2).\n"
            "- (Optional) Set a send date using the 'Set Send Date' command.\n\n"
            "2. Managing Capsules\n"
            "- View Capsules (/view_capsules): View a list of your capsules.\n"
            "- Add Recipient (/add_recipient): Add new recipients to an existing capsule.\n"
            "- Send Capsule (/send_capsule): Immediately send the capsule to all recipients.\n"
            "- Delete Capsule (/delete_capsule): Delete an unwanted capsule.\n"
            "- View Recipients (/view_recipients): See who will receive the capsule.\n"
            "- Set Send Date (/select_send_date): Specify when the capsule will be sent (e.g., in a week, a month, or choose your own date).\n\n"
            "3. Send Dates\n"
            "- If you used 'Set Send Date' after creating the capsule, it will be sent at the specified time.\n"
            "- Without a date, the capsule will remain in drafts until you send it manually.\n\n"
            "Additional\n"
            "- Support Author (/support_author): Support the bot’s development.\n"
            "- Change Language (/change_language): Select your preferred interface language.\n\n"
            "If you have any questions, contact @TimeCapsuleSupport! Start with the /start command."
        ),
        "change_language": "🌍 Change Language",
        "select_language": "Select your language:",
        "capsule_created": "✅ Capsule #{capsule_id} created!\nAdd text, photos, or videos to it.",
        "enter_recipients": (
            "👥 Enter Telegram usernames of recipients separated by spaces.\n"
            "Example: @Friend1 @Friend2\n"
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
        "your_capsules": "📋 Your Time Capsules:\n",
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
            "📋 Guía de TimeCapsuleBot\n\n"
            "TimeCapsuleBot te permite crear cápsulas del tiempo que puedes enviarte a ti mismo o a tus amigos en el futuro. "
            "Aquí tienes cómo usar el bot paso a paso:\n\n"
            "1. Crear una Cápsula (/create_capsule)\n"
            "- Haz clic en 'Crear Cápsula' o ingresa /create_capsule.\n"
            "- Ingresa un nombre para la cápsula.\n"
            "- Añade contenido: texto, fotos, videos, audio, stickers o documentos.\n"
            "- Después de cada adición, elige 'Añadir Más' o 'Finalizar'.\n"
            "- Especifica los destinatarios (por ejemplo, @Friend1 @Friend2).\n"
            "- (Opcional) Establece una fecha de envío usando el comando 'Establecer Fecha de Envío'.\n\n"
            "2. Gestionar Cápsulas\n"
            "- Ver Cápsulas (/view_capsules): Ver una lista de tus cápsulas.\n"
            "- Añadir Destinatario (/add_recipient): Añade nuevos destinatarios a una cápsula existente.\n"
            "- Enviar Cápsula (/send_capsule): Envía la cápsula a todos los destinatarios inmediatamente.\n"
            "- Eliminar Cápsula (/delete_capsule): Elimina una cápsula no deseada.\n"
            "- Ver Destinatarios (/view_recipients): Ver quién recibirá la cápsula.\n"
            "- Establecer Fecha de Envío (/select_send_date): Especifica cuándo se enviará la cápsula (por ejemplo, en una semana, un mes o elige tu propia fecha).\n\n"
            "3. Fechas de Envío\n"
            "- Si usaste 'Establecer Fecha de Envío' después de crear la cápsula, se enviará en el momento especificado.\n"
            "- Sin una fecha, la cápsula permanecerá en borradores hasta que la envíes manualmente.\n\n"
            "Adicional\n"
            "- Apoyar al Autor (/support_author): Apoya el desarrollo del bot.\n"
            "- Cambiar Idioma (/change_language): Selecciona tu idioma preferido para la interfaz.\n\n"
            "Si tienes alguna pregunta, contacta a @TimeCapsuleSupport! Comienza con el comando /start."
        ),
        "change_language": "🌍 Cambiar idioma",
        "select_language": "Selecciona tu idioma:",
        "capsule_created": "✅ ¡Cápsula #{capsule_id} creada!\nAgrega texto, fotos o videos a ella.",
        "enter_recipients": (
            "👥 Ingresa los nombres de usuario de Telegram de los destinatarios separados por espacios.\n"
            "Ejemplo: @Friend1 @Friend2\n"
            "Ellos recibirán la cápsula cuando la envíes o llegue la fecha programada."
        ),
        "select_capsule": "📦 Selecciona una cápsula para la acción:",
        "invalid_capsule_id": "❌ ID de cápsula inválido. Verifica tu lista de cápsulas con 'Ver Cápsulas'.",
        "recipients_added": (
            "✅ ¡Destinatarios agregados a la cápsula #{capsule_id}!\n"
            "Ahora puedes establecer una fecha de envío o enviarla inmediatamente."
        ),
        "error_general": "⚠️ Algo salió mal. Inténtalo de nuevo o contacta con soporte.",
        "service_unavailable": (
            "🛠 El servicio no está disponible temporalmente. Por favor, espera e inténtalo de nuevo más tarde."
        ),
        "your_capsules": "📋 Tus cápsulas del tiempo:\n",
        "no_capsules": "📭 Todavía no tienes cápsulas. ¡Crea tu primera con 'Crear Cápsula'!",
        "created_at": "Creado",
        "status": "Estado",
        "scheduled": "⏳ Programado",
        "draft": "✏️ Borrador",
        "enter_capsule_id_to_send": "📨 Ingresa el ID de la cápsula para enviar inmediatamente (por ejemplo, #5):",
        "no_recipients": "❌ Esta cápsula no tiene destinatarios. Agrega algunos con 'Agregar Destinatario'.",
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
        "create_capsule_first": "📦 Primero, crea una cápsula con 'Crear Cápsula' para agregar contenido.",
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
            "📋 Guide de TimeCapsuleBot\n\n"
            "TimeCapsuleBot vous permet de créer des capsules temporelles que vous pouvez envoyer à vous-même ou à vos amis dans le futur. "
            "Voici comment utiliser le bot étape par étape:\n\n"
            "1. Créer une Capsule (/create_capsule)\n"
            "- Cliquez sur 'Créer une Capsule' ou entrez /create_capsule.\n"
            "- Entrez un nom pour la capsule.\n"
            "- Ajoutez du contenu : texte, photos, vidéos, audio, stickers ou documents.\n"
            "- Après chaque ajout, choisissez 'Ajouter Plus' ou 'Terminer'.\n"
            "- Spécifiez les destinataires (par exemple, @Friend1 @Friend2).\n"
            "- (Optionnel) Définissez une date d'envoi en utilisant la commande 'Définir la Date d'Envoi'.\n\n"
            "2. Gérer les Capsules\n"
            "- Voir les Capsules (/view_capsules): Voir une liste de vos capsules.\n"
            "- Ajouter un Destinataire (/add_recipient): Ajoutez de nouveaux destinataires à une capsule existante.\n"
            "- Envoyer la Capsule (/send_capsule): Envoyez la capsule à tous les destinataires immédiatement.\n"
            "- Supprimer la Capsule (/delete_capsule): Supprimez une capsule non désirée.\n"
            "- Voir les Destinataires (/view_recipients): Voir qui recevra la capsule.\n"
            "- Définir la Date d'Envoi (/select_send_date): Spécifiez quand la capsule sera envoyée (par exemple, dans une semaine, un mois ou choisissez votre propre date).\n\n"
            "3. Dates d'Envoi\n"
            "- Si vous avez utilisé 'Définir la Date d'Envoi' après avoir créé la capsule, elle sera envoyée à l'heure spécifiée.\n"
            "- Sans date, la capsule restera en brouillon jusqu'à ce que vous l'envoyiez manuellement.\n\n"
            "Additionnel\n"
            "- Soutenir l'Auteur (/support_author): Soutenez le développement du bot.\n"
            "- Changer de Langue (/change_language): Sélectionnez votre langue préférée pour l'interface.\n\n"
            "Si vous avez des questions, contactez @TimeCapsuleSupport! Commencez avec la commande /start."
        ),
        "change_language": "🌍 Changer de langue",
        "select_language": "Sélectionnez votre langue :",
        "capsule_created": "✅ Capsule #{capsule_id} créée !\nAjoutez-y du texte, des photos ou des vidéos.",
        "enter_recipients": (
            "👥 Entrez les noms d'utilisateur Telegram des destinataires séparés par des espaces.\n"
            "Exemple: @Friend1 @Friend2\n"
            "Ils recevront la capsule lorsque vous l'enverrez ou à la date programmée."
        ),
        "select_capsule": "📦 Sélectionnez une capsule pour l'action :",
        "invalid_capsule_id": "❌ ID de capsule invalide. Vérifiez votre liste de capsules avec 'Voir les Capsules'.",
        "recipients_added": (
            "✅ Destinataires ajoutés à la capsule #{capsule_id} !\n"
            "Vous pouvez maintenant définir une date d'envoi ou l'envoyer immédiatement."
        ),
        "error_general": "⚠️ Quelque chose s'est mal passé. Réessayez ou contactez le support.",
        "service_unavailable": (
            "🛠 Le service est temporairement indisponible. Veuillez patienter et réessayer plus tard."
        ),
        "your_capsules": "📋 Vos capsules temporelles :\n",
        "no_capsules": "📭 Vous n'avez pas encore de capsules. Créez votre première avec 'Créer une Capsule' !",
        "created_at": "Créé",
        "status": "Statut",
        "scheduled": "⏳ Programmé",
        "draft": "✏️ Brouillon",
        "enter_capsule_id_to_send": "📨 Entrez l'ID de la capsule à envoyer immédiatement (par exemple, #5) :",
        "no_recipients": "❌ Cette capsule n'a pas de destinataires. Ajoutez-en avec 'Ajouter un Destinataire'.",
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
        "create_capsule_first": "📦 Créez d'abord une capsule avec 'Créer une Capsule' pour ajouter du contenu.",
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
        "view_recipients_btn": "👥 Voir les Destinatarios",
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
            "📋 TimeCapsuleBot-Anleitung\n\n"
            "TimeCapsuleBot ermöglicht es Ihnen, Zeitkapseln zu erstellen, die Sie sich selbst oder Freunden in der Zukunft senden können. "
            "Hier ist eine Schritt-für-Schritt-Anleitung zur Verwendung des Bots:\n\n"
            "1. Kapsel erstellen (/create_capsule)\n"
            "- Klicken Sie auf 'Kapsel erstellen' oder geben Sie /create_capsule ein.\n"
            "- Geben Sie einen Namen für die Kapsel ein.\n"
            "- Fügen Sie Inhalte hinzu: Text, Fotos, Videos, Audio, Sticker oder Dokumente.\n"
            "- Nach jeder Hinzufügung wählen Sie 'Mehr hinzufügen' oder 'Fertigstellen'.\n"
            "- Geben Sie die Empfänger an (z.B. @Friend1 @Friend2).\n"
            "- (Optional) Legen Sie ein Sendedatum mit dem Befehl 'Sendedatum festlegen' fest.\n\n"
            "2. Kapseln verwalten\n"
            "- Kapseln anzeigen (/view_capsules): Zeigt eine Liste Ihrer Kapseln an.\n"
            "- Empfänger hinzufügen (/add_recipient): Fügen Sie einer bestehenden Kapsel neue Empfänger hinzu.\n"
            "- Kapsel senden (/send_capsule): Senden Sie die Kapsel sofort an alle Empfänger.\n"
            "- Kapsel löschen (/delete_capsule): Löschen Sie eine unerwünschte Kapsel.\n"
            "- Empfänger anzeigen (/view_recipients): Sehen Sie, wer die Kapsel erhalten wird.\n"
            "- Sendedatum festlegen (/select_send_date): Legen Sie fest, wann die Kapsel gesendet wird (z.B. in einer Woche, einem Monat oder wählen Sie Ihr eigenes Datum).\n\n"
            "3. Sendedaten\n"
            "- Wenn Sie 'Sendedatum festlegen' nach dem Erstellen der Kapsel verwendet haben, wird sie zum angegebenen Zeitpunkt gesendet.\n"
            "- Ohne Datum bleibt die Kapsel im Entwurfsmodus, bis Sie sie manuell senden.\n\n"
            "Zusätzlich\n"
            "- Autor unterstützen (/support_author): Unterstützen Sie die Entwicklung des Bots.\n"
            "- Sprache ändern (/change_language): Wählen Sie Ihre bevorzugte Sprache für die Benutzeroberfläche.\n\n"
            "Wenn Sie Fragen haben, kontaktieren Sie @TimeCapsuleSupport! Beginnen Sie mit dem Befehl /start."
        ),
        "change_language": "🌍 Sprache ändern",
        "select_language": "Wählen Sie Ihre Sprache:",
        "capsule_created": "✅ Kapsel #{capsule_id} erstellt!\nFügen Sie Text, Fotos oder Videos hinzu.",
        "enter_recipients": (
            "👥 Geben Sie die Telegram-Benutzernamen der Empfänger getrennt durch Leerzeichen ein.\n"
            "Beispiel: @Friend1 @Friend2\n"
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
        "your_capsules": "📋 Ihre Zeitkapseln:\n",
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
        "confirm_delete": "🗑 Sind Sie sicher, dass Sie diese Kapsel löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.",
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
