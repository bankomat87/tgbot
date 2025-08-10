import asyncio
from telegram import Update, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from .keyboards import get_style_keyboard, ReplyKeyboardRemove
from .generator import ImageGenerator
from config import API_BASE_URL

# Состояния диалога
SELECTING_STYLE, ENTERING_PROMPT = range(2)

generator = ImageGenerator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    api_status, status_msg = await generator.check_api_status()
    
    message = (
        "👋 Привет! Я бот для генерации изображений через Stable Diffusion.\n\n"
        f"{status_msg}\n\n"
        "Доступные команды:\n"
        "/render - начать генерацию\n"
        "/help - справка по командам\n"
        "/status - проверить API\n"
        "/cancel - отменить операцию"
    )
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "ℹ️ <b>Справка по командам:</b>\n\n"
        "/start - начать работу с ботом\n"
        "/render - запустить генерацию изображения\n"
        "/status - проверить состояние API\n"
        "/help - показать это сообщение\n\n"
        "<b>Процесс генерации:</b>\n"
        "1. Выберите стиль\n"
        "2. Введите описание на английском\n"
        "3. Ожидайте результат (1-3 минуты)\n\n"
        "✏️ <i>Пример промпта:</i> <code>a beautiful sunset over mountains, digital art</code>"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def status_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса API"""
    api_status, status_msg = await generator.check_api_status()
    emoji = "🟢" if api_status else "🔴"
    await update.message.reply_text(f"{emoji} {status_msg}")

async def render_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса генерации"""
    api_status, status_msg = await generator.check_api_status()
    if not api_status:
        await update.message.reply_text(f"🔴 {status_msg}\nПопробуйте позже.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🎨 Выберите стиль изображения:",
        reply_markup=get_style_keyboard()
    )
    return SELECTING_STYLE

async def style_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора стиля"""
    if update.message.text.lower() == 'отмена':
        return await cancel_operation(update, context)
    
    context.user_data['style'] = update.message.text
    await update.message.reply_text(
        f"Вы выбрали: {update.message.text}\n\n"
        "Теперь введите детальное описание на английском:\n"
        "<i>Пример: \"a beautiful sunset over mountains, digital art\"</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    return ENTERING_PROMPT

async def prompt_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода промпта и запуск генерации"""
    prompt = update.message.text
    style = context.user_data['style']
    
    status_msg = await update.message.reply_text(
        f"🔄 <b>Генерация начата:</b>\n"
        f"• Стиль: {style}\n"
        f"• Описание: {prompt}\n\n"
        "⏳ Обычно это занимает 1-3 минуты...",
        parse_mode="HTML"
    )
    
    result = await generator.generate_image(prompt, style)
    
    if not result["success"]:
        await status_msg.edit_text(f"❌ <b>Ошибка:</b>\n{result['error']}", parse_mode="HTML")
        return ConversationHandler.END
    
    for i in range(1, 11):
        await asyncio.sleep(result["estimated_time"] / 10)
        image = await generator.get_image(result["task_id"])
        
        if image:
            await update.message.reply_photo(
                photo=InputFile(image, filename="generated.png"),
                caption=f"🎉 <b>Готово!</b>\n• Стиль: {style}\n• Описание: {prompt}",
                parse_mode="HTML"
            )
            await status_msg.delete()
            return ConversationHandler.END
        
        await status_msg.edit_text(
            f"🔄 <b>Генерация...</b> ({i*10}%)\n"
            f"• Стиль: {style}\n"
            f"• Описание: {prompt}",
            parse_mode="HTML"
        )
    
    await status_msg.edit_text("⚠️ Превышено время ожидания. Попробуйте снова.")
    return ConversationHandler.END

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей операции"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Операция отменена",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def handle_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка неожиданных сообщений"""
    await update.message.reply_text(
        "⚠️ Используйте команды из меню (/help) или завершите текущую операцию (/cancel)",
        reply_markup=ReplyKeyboardRemove()
    )