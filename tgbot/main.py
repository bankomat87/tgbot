from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from bot.handlers import (
    start,
    help_command,
    status_check,  # Добавлен этот импорт
    render_start,
    style_selected,
    prompt_entered,
    cancel_operation,  # Исправленное имя (было cancel_generation)
    SELECTING_STYLE,
    ENTERING_PROMPT
)
import config

def main():
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # 1. Регистрируем обычные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_check))  # Теперь функция определена

    # 2. Настройка ConversationHandler для генерации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("render", render_start)],
        states={
            SELECTING_STYLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, style_selected)],
            ENTERING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_entered)]
        },
        fallbacks=[CommandHandler("cancel", cancel_operation)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    # 3. Обработчик для любых других сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda update, ctx: update.message.reply_text("Используйте /help для списка команд")
    ))

    print("🟢 Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()